from collections.abc import Iterable
import logging
from typing import Any, LiteralString, cast
import pymssql

from .types import Article, StorageModifier, DBResult

logger = logging.getLogger(__name__)


class Database:
    def __init__(self) -> None:
        self.connection: pymssql.Connection | None = None
        self.cursor: pymssql.Cursor | None = None

    def connect_to_database(self, server: str, username: str, password: str, database: str) -> None:
        logger.info(f"Connecting to database {database} on {server}")
        """Establishes a connection to the database."""
        self.connection = pymssql.connect(server=server, user=username,
                                          password=password, database=database, tds_version=r"7.0")
        if not self.connection:
            raise ConnectionError(
                f"Failed to connect to database {database} on {server}")
        self.cursor = self.connection.cursor()
        if not self.cursor:
            raise ConnectionError(
                "Failed to create a cursor for the database connection.")

    def close(self) -> None:
        """Closes the database connection and cursor."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: LiteralString, params: Iterable[Any] = ()) -> list[tuple[Any, ...]] | None:
        """Executes a SQL query and returns the result."""
        if self.cursor is None:
            raise ConnectionError(
                "Database cursor is not initialized. Call connect_to_database first.")
        try:
            self.cursor.execute(query, params)
            try:
                return self.cursor.fetchall()
            # Handles cases where statement has no resultset (e.g. INSERT, UPDATE)
            except pymssql.OperationalError:
                return None
            except Exception:
                logger.error(
                    f"Error fetching results for query: {query} with params: {params}.", exc_info=True)
                raise
        except Exception:
            logger.error(
                f"Error executing query: {query} with params: {params}.", exc_info=True)
            raise

    def commit(self) -> None:
        assert self.connection is not None, "Connection is not initialized."
        self.connection.commit()

    def rollback(self) -> None:
        assert self.connection is not None, "Connection is not initialized."
        self.connection.rollback()

    """********************
    ** ARTICLES
    ********************"""

    def get_article(self, article_id: int | None = None) -> DBResult:
        query: LiteralString = f"""
            select artikel_id, artikel_bezeichnung
            from artikel_basis
            where 1=1
            {' and artikel_id = %s' if article_id is not None else ''}
        """
        params: tuple[int, ...] = () if article_id is None else (article_id,)
        rows: DBResult = self.execute_query(query, params)
        return rows

    """********************
    ** STORAGE
    ********************"""

    def update_storage(self, sm: StorageModifier, absolute: bool = False) -> None:
        storage_id: int = sm.storage_id
        amount: int = sm.amount
        article: Article = sm.article
        try:
            # get the lager artikel
            query: LiteralString = f"""select top 1 * from internal_lager_artikel_by_priority(%s)"""
            result: list[tuple[Any, ...]] | None = self.execute_query(
                query, (article.id,))
            if result is None or len(result) == 0:
                raise LookupError(
                    f"No storage article id found for article {article.id}.")
            storage_article_id: int = result[0][0]

            # check if the lagerdetail (=lagerstand) already exists
            # if not, create it
            query: LiteralString = """select count(*) from lager_details 
                where lager_detail_lager = %s and 
                lager_detail_artikel = %s"""
            result: list[tuple[Any, ...]] | None = self.execute_query(
                query, (storage_id, storage_article_id))
            if result is None or len(result) == 0:
                raise LookupError(f"Error for query {query}.")
            count: int = result[0][0]
            if count == 0:
                query: LiteralString = f"""exec insert_lagerdetail %s, %s, %s, %s, %s"""
                self.execute_query(
                    query, (storage_id, storage_article_id, 0, 0, 0))

            # if we set the absolute value, first set the stock value to 0
            if absolute:
                query: LiteralString = f"""update lager_details set lager_detail_istStand = 0 where lager_detail_lager = %s and lager_detail_artikel = %s"""
                self.execute_query(query, (storage_id, storage_article_id))

            query: LiteralString = """
                select lager_einheit_multiplizierer from lager_einheiten, lager_artikel
                where 1=1
                and lager_einheit_id = lager_artikel_einheit
                and lager_artikel_lagerartikel = %s
            """
            result: list[tuple[Any, ...]] | None = self.execute_query(
                query,  (storage_article_id, ))
            if result is None or len(result) == 0:
                raise LookupError(
                    f"No unit modifier found for storage article {storage_article_id}.")
            # Ensure it's a float for calculation
            unit_modifier: float = float(result[0][0])
            logger.debug(
                f"Unit modifier for storage_article_id {storage_article_id}: {unit_modifier}")

            query: LiteralString = f"""exec lager_update_stand %s, %s, %s"""
            self.execute_query(
                query,  (article.id, storage_id, amount * unit_modifier))
        except Exception:  # Keep 'e' for the raise, but logger will capture details
            self.rollback()
            logger.error(
                f"Error updating storage for article {article.id}, storage {storage_id}, amount {amount}.", exc_info=True)
            raise
        self.commit()

    def add_article_to_storage(self, sm: StorageModifier, absolute: bool = False) -> None:
        if sm.amount < 0:
            raise ValueError
        self.update_storage(sm, absolute)

    def withdraw_article_from_storage(self, sm: StorageModifier, absolute: bool = False) -> None:
        if sm.amount < 0:
            raise ValueError
        self.update_storage(sm._replace(amount=-sm.amount), absolute)

    def get_all_storage_article_groups(self) -> list[tuple[Any, ...]] | None:
        query: LiteralString = f"""
            select distinct artikel_gruppe_id, artikel_gruppe_name 
            from lager_artikel, artikel_basis, artikel_gruppen
            where 1=1
            and lager_artikel_artikel = artikel_id
            and artikel_gruppe = artikel_gruppe_id
        """
        rows: list[tuple[Any, ...]] | None = self.execute_query(query)
        return rows

    def get_all_storage_articles(self) -> list[tuple[Any, ...]] | None:
        query: LiteralString = f"""select * from lager_artikel"""
        rows: list[tuple[Any, ...]] | None = self.execute_query(query)
        return rows

    def get_storage_articles_by_group(self, article_group_id: int) -> DBResult:
        query: LiteralString = f"""
            select artikel_id, artikel_bezeichnung
            from artikel_basis, lager_artikel
            where 1=1
            and lager_artikel_artikel = artikel_id
            and artikel_gruppe = %s
        """
        rows: DBResult = self.execute_query(query, (article_group_id,))
        return rows

    def get_storage_articles_in_storage(self, storage_id: int) -> list[tuple[Any, ...]] | None:
        """Retrieves all articles found in a specific storage.

        This method queries the database to find all articles that are present
        in the specified storage. It returns a list of tuples, where each tuple
        contains the article ID, article name, and the current stock level
        (lager_detail_istStand) for that article in the storage.

        Args:
            storage_id (int): The ID of the storage to query.

        Returns:
            list[tuple[Any, ...]] | None: A list of tuples, where each tuple
            contains (artikel_id, artikel_bezeichnung, lager_detail_istStand).
        """

        query: LiteralString = f"""
            select artikel_id, artikel_bezeichnung, lager_detail_istStand/lager_einheit_multiplizierer
            from artikel_basis, lager_artikel, lager_details, lager_einheiten
            where 1=1
            and lager_einheit_id = lager_artikel_einheit
            and artikel_id = lager_artikel_artikel
            and lager_detail_lager = %s
            and lager_detail_artikel = lager_artikel_lagerartikel
            and lager_detail_istStand > 0
        """
        rows: list[tuple[Any, ...]] | None = self.execute_query(
            query, (storage_id,))
        return rows

    def get_article_groups_in_storage(self, storage_id: int) -> list[tuple[Any, ...]] | None:
        """Retrieves all article groups for articles found in a specific storage.

        This method queries the database to find all distinct article groups
        associated with articles that are present in the specified storage.

        Args:
            storage_id (int): The ID of the storage to query.

        Returns:
            list[tuple[Any, ...]] | None: A list of tuples, where each tuple contains the article group ID and name. Returns None if no data is found or an error occurs.
        """

        query: LiteralString = f"""
            select distinct artikel_gruppe_id, artikel_gruppe_name 
            from lager_artikel, artikel_basis, artikel_gruppen, lager_details
            where 1=1
            and lager_artikel_artikel = artikel_id 
            and artikel_gruppe = artikel_gruppe_id 
            and lager_detail_artikel = lager_artikel_lagerartikel 
            and lager_detail_lager = %s
            and lager_detail_istStand > 0
        """
        rows: list[tuple[Any, ...]] | None = self.execute_query(
            query, (storage_id,))
        return rows

    def get_articles_in_storage(self, storage_id: int, article_group_id: int | None = None, show_not_in_stock: bool = False) -> list[tuple[Any, ...]] | None:
        query: LiteralString = f"""
            select artikel_id, artikel_bezeichnung, lager_detail_istStand/lager_einheit_multiplizierer
            from artikel_basis, lager_artikel, lager_details, lager_einheiten
            where 1=1
            and lager_einheit_id = lager_artikel_einheit
            and artikel_id = lager_artikel_artikel
            and lager_detail_artikel = lager_artikel_lagerartikel
            and lager_detail_lager = %s
        """
        params: tuple[int, ...] = (storage_id,)
        if article_group_id is not None:
            query += f" and artikel_gruppe = %s"
            params = (storage_id, article_group_id)

        if not show_not_in_stock:
            query += f" and lager_detail_istStand > 0.001"

        rows: list[tuple[Any, ...]] | None = self.execute_query(query, params)
        return rows

    def get_storage_name(self, storage_id: int) -> list[tuple[Any, ...]] | None:
        query: LiteralString = f"""select lager_bezeichnung from lager_basis where lager_id = %s"""
        rows: list[tuple[Any, ...]] | None = self.execute_query(
            query, (storage_id,))
        return rows

    def empty_storage(self, storage_id: int) -> None:
        query: LiteralString = f"""
            update lager_details
            set lager_detail_istStand = 0
            where lager_detail_lager = %s
        """
        self.execute_query(query, (storage_id,))
        self.commit()

    """********************
    ** SALES
    ********************"""

    def get_client_sales(self, client: str) -> DBResult:
        query: LiteralString = f"""
            SELECT rechnung_kellnerKurzName, ROUND(SUM(rechnung_detail_preis * rechnung_detail_menge), 2) AS total_sales
            FROM rechnungen_details, rechnungen_basis
            WHERE 1=1
            AND rechnung_kellnerKurzName = %s
            AND rechnung_detail_rechnung = rechnung_id
            AND checkpoint_tag IS NULL
            GROUP BY rechnung_kellnerKurzName
        """
        rows: DBResult = self.execute_query(query, (client,))
        return rows

    def get_tallied_articles(self, client: str) -> DBResult:
        query: LiteralString = f"""
            select sum(tisch_bondetail_absmenge), artikel_bezeichnung 
            from tische_bereiche, tische_aktiv, tische_bons, tische_bondetails, artikel_basis, kellner_basis 
            where 1=1 
            and tisch_bondetail_artikel = artikel_id 
            and tisch_bereich = tischbereich_id 
            and tisch_bon_tisch = tisch_id 
            and tisch_bondetail_bon = tisch_bon_id 
            and tisch_bon_kellner = kellner_id 
            and checkpoint_tag is null
            and kellner_kurzName = %s 
            group by artikel_bezeichnung 
            having sum(tisch_bondetail_absmenge) > 0 
            order by artikel_bezeichnung
        """
        rows: DBResult = self.execute_query(query, (client,))
        return rows

    def get_latest_tallied_articles(self, client: str) -> DBResult:
        query: LiteralString = f"""
            select top 10 kellner_kurzName, tisch_bondetail_absmenge, artikel_bezeichnung \
            from kellner_basis, tische_bons, tische_bondetails, artikel_basis \
            where 1=1 \
            and kellner_id = tisch_bon_kellner \
            and tisch_bondetail_bon = tisch_bon_id \
            and artikel_id = tisch_bondetail_artikel \
            and kellner_kurzName like %s \
            order by tisch_bon_dt_erstellung desc
        """
        rows: DBResult = self.execute_query(query, (f'%{client}%',))
        return rows

    def get_wardrobe_sales(self) -> DBResult:
        query: LiteralString = f"""
            select kellner_kurzName, tischbereich_kurzName + '-' + cast(tisch_pri_nummer as VARCHAR), 
            round(sum(tisch_bondetail_absmenge*tisch_bondetail_preis), 2), tischbereich_istAufwand
            from tische_aktiv, tische_bereiche, tische_bons, tische_bondetails, kellner_basis
            where 1=1
            and tisch_bereich = tischbereich_id
            and tisch_bon_tisch = tisch_id
            and tisch_bondetail_bon = tisch_bon_id
            and tisch_bon_kellner = kellner_id
            and checkpoint_tag is null
            and tischbereich_name like '%GARDEROBE%'
            group by kellner_kurzName, tischbereich_kurzName + '-' + cast(tisch_pri_nummer as VARCHAR), tischbereich_istAufwand
        """
        rows: DBResult = self.execute_query(query)
        return rows

    """********************
    ** INVOICES
    ********************"""

    def get_invoice_data(self, invoice_id: int) -> DBResult:
        query: LiteralString = """
            select rechnung_nr, rechnung_dt_erstellung, rechnung_detail_absmenge, 
            rechnung_detail_preis*rechnung_detail_absmenge, rechnung_detail_text,
            (select sum(rechnung_detail_absmenge*rechnung_detail_preis) from rechnungen_details where rechnung_detail_rechnung = rechnung_id) as total,
            case mwst_satz when 10.00 then 'A' when 20.00 then 'B' when 5.00 then 'C' end as mwstsatz,
            (rechnung_detail_preis*rechnung_detail_absmenge)/(100+mwst_satz)*mwst_satz as mwst,
            mwst_bezeichnung, rechnung_tischCode, rechnung_kellnerKurzName,
            rechnung_kassenidentifikation, rechnung_barumsatz_nr, dbo.GetMachineCodeQr(rechnung_id),
            adresse_vorname, adresse_nachname, adresse_strasse, adresse_plz, adresse_ort, adresse_firma,
            adresse_id, rechnung_id
            from rechnungen_basis
            full outer join rechnungen_adressen
            on rechnungen_basis.rechnung_adresse = rechnungen_adressen.adresse_id,
            rechnungen_details, meta_mwstgruppen
            where 1=1
            and rechnung_id = rechnung_detail_rechnung
            and rechnung_detail_mwst = mwst_id
            and rechnung_id = %s
        """
        rows: DBResult = self.execute_query(query, (invoice_id,))
        return rows

    def get_invoice_list(self, waiter: str | None = None, invoice_type: int | None = None, limit: int = 10) -> DBResult:
        query: str = f"""
            select top {limit} rechnung_id, rechnung_nr, rechnung_dt_erstellung, rechnung_tischCode, rechnung_kellnerKurzName
            from rechnungen_basis
            where 1=1
            {' and rechnung_kellnerKurzName = %s' if waiter is not None else ''}
            {' and rechnung_typ = %s' if invoice_type is not None else ''}
            order by rechnung_dt_erstellung desc
        """  # type: ignore
        params: list[str | int] = []
        if waiter is not None:
            params.append(waiter)
        if invoice_type is not None:
            params.append(invoice_type)
        logger.debug(
            f"Executing get_invoice_list query: {query.strip()} with params: {params}")
        rows: DBResult = self.execute_query(cast(LiteralString, query), params)
        return rows

    def get_invoice_type(self, id: int | None = None) -> DBResult:
        query: LiteralString = f"""
            SELECT rechnung_typ_id, rechnung_typ_kurz, rechnung_typ_bezeichnung,
            rechnung_typ_maxNummer, rechnung_typ_istBarverkaufTyp, rechnung_typ_istAufwandTyp,
            rechnung_typ_anzahl, rechnung_typ_istSofortRechnungstyp
            FROM rechnungen_typen
            {' WHERE rechnung_typ_id = %s' if id is not None else ''}
        """
        params: tuple[int] | tuple[()] = (id,) if id is not None else ()
        rows: DBResult = self.execute_query(query, params)
        return rows

    """********************
    ** RECIPES
    ********************"""

    def get_receipes(self) -> DBResult:
        query: LiteralString = f"""
            SELECT
                art1.artikel_bezeichnung,
                zutate_menge,
                art2.artikel_bezeichnung,
                lager_einheit_name
            FROM
                artikel_basis AS art1
            INNER JOIN
                artikel_zutaten ON zutate_master_artikel = art1.artikel_id
            INNER JOIN
                artikel_basis AS art2 ON zutate_artikel = art2.artikel_id
            LEFT OUTER JOIN
                lager_artikel ON lager_artikel_artikel = art2.artikel_id
            LEFT OUTER JOIN
                lager_einheiten ON lager_artikel_einheit = lager_einheit_id
            WHERE
                zutate_istRezept = 1
            ORDER BY
                art1.artikel_bezeichnung;
        """
        rows: DBResult = self.execute_query(query)
        return rows
