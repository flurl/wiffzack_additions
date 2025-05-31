#!/usr/bin/env python3

import datetime
import sys
import queue
import threading
import logging
from pathlib import Path
from decimal import Decimal
from typing import Any, LiteralString, NoReturn, TypeAlias, Optional
from dataclasses import dataclass, field

import step

from lib.EscPos.EscPosHTMLParser import EscPosHTMLParser
from lib.config import ConfigLoader
import wiffzack as wz
from wiffzack.types import DBResult


logger: logging.Logger = logging.getLogger(__name__)

PRINTERPROFILE: LiteralString = "TM-T88II"
SPOOLDIR: Path = Path("./spool")
PRINTTEMPLATESPATH: Path = Path("./print_templates/")

db_connection: wz.Database  # Global for this module


@dataclass(order=True)
class PrintJob:
    invoice_id: int = field(compare=False)
    template: str = field(compare=False)
    output: str = field(compare=False)
    tries: int = field(default=0, compare=False)


@dataclass
class InvoiceDataRow:
    invoice_nr: int
    date: datetime.datetime
    article_amount: int
    article_sum: Decimal
    article: str
    invoice_total: Decimal
    tax: str
    tax_sum: Decimal
    tax_desc: str
    table: str
    waiter: str
    register_id: str
    cash_nr: str
    qr_code: str
    first_name: Optional[str]
    last_name: Optional[str]
    street: Optional[str]
    zip_code: Optional[str]
    city: Optional[str]
    company: Optional[str]


print_queue_item: TypeAlias = tuple[int, PrintJob]


class PrintService:
    def __init__(self) -> None:
        self.print_queue: queue.PriorityQueue[print_queue_item] = queue.PriorityQueue(
        )
        self.worker_thread = threading.Thread(
            target=self.print_worker, daemon=True)
        self.worker_thread.start()

    def enqueue_print_job(self, invoice_id: int, template: str, output: str) -> None:
        """
        Enqueues a print job for a given invoice ID.

        The print jobs are prioritized based on the invoice ID, with higher
        invoice IDs having higher priority. This is achieved by negating the
        invoice ID when adding it to the priority queue, as PriorityQueue prioritizes
        smaller numbers

        Args:
            invoice_id (int): The ID of the invoice to be printed.
            template (str): The template name to be used
            output (str): The output format to be used
        """
        self.print_queue.put(
            (-invoice_id, PrintJob(invoice_id, template, output)))

    def print_worker(self) -> NoReturn:
        while True:
            item: print_queue_item = self.print_queue.get()
            invoice_id: int = item[1].invoice_id
            template: str = item[1].template
            output: str = item[1].output
            retries: int = item[1].tries

            if retries >= 3:
                # give up after 3 tries
                self.print_queue.task_done()
                logger.error(
                    f"Permanently failed to print invoice: {invoice_id}. Skipping…")
                continue

            logger.debug(f"Printing invoice: {invoice_id}")
            try:
                self.print_invoice(invoice_id, template, output)
                logger.debug(f"Finished printing invoice: {invoice_id}")
            except Exception as e:
                """
                if the print job failed requeue it. Since new jobs have an higher ID they
                will be prioritized because of the negation in enqueue_print_job()
                and the failed ones will try reppinting after the new ones
                """
                item[1].tries += 1
                self.print_queue.put(item)
                logger.debug(f"Failed to print invoice: {invoice_id}")
                logger.debug(f"Failed with error: {e}")
                logger.debug(repr(e))
            finally:
                self.print_queue.task_done()

    def listen_for_input(self) -> None:
        """
        Listens for input from stdin and enqueues print jobs.

        This method continuously reads lines from standard input, parses them
        as print job requests, and enqueues them into the print queue. Each line
        is expected to contain the invoice ID, optionally followed by the template
        name and output format, separated by spaces.
        """

        for line in sys.stdin:
            params: list[str] = line.strip().split(":")
            try:
                invoice_id: int = int(params[0])
            except ValueError as e:
                logging.error(f"Invalid input: {line.strip()}")
                raise e
            try:
                template: str = params[1]
            except IndexError:
                template = "invoice"
            try:
                output: str = params[2]
            except IndexError:
                output = "escpos"
            self.enqueue_print_job(invoice_id, template, output)

    def parse_invoice(self,
                      invoice_data: list[InvoiceDataRow],
                      template: str,
                      output: str = 'html') -> bytes:

        logger.debug(f"printing invoice {invoice_data[0].invoice_nr}")
        # logger.debug(f"template: {template}")
        logger.debug(f"output: {output}")

        tmpl: step.Template = step.Template(template)  # type: ignore
        articles: str = ''
        taxes: dict[str, list[Decimal | str]] = {}
        for row in invoice_data:
            amount: int = row.article_amount
            article: str = row.article
            sum: Decimal = row.article_sum
            tax_type: str = row.tax
            articles_row: str = "{0:<3d}x {1:<41s} {2:>7.2f} {3:s}<br />".format(
                amount, article, sum, tax_type)
            articles += articles_row
            try:
                taxes[row.tax][0] = Decimal(
                    taxes[row.tax][0]) + row.tax_sum  # sum of taxes
                taxes[row.tax][2] = Decimal(
                    taxes[row.tax][2]) + row.article_sum  # sum of taxes
            except KeyError:
                # taxes[row.tax] = [row.tax_sum, row.tax_desc, row.article_sum]
                taxes[row.tax] = [row.tax_sum, row.tax_desc, row.article_sum]
        invoice_number: str = str(invoice_data[0].invoice_nr)

        taxes_text: str = ''
        for key, value in taxes.items():
            taxes_text += '{0}: {1} MwSt. von {3:.2f} = {2:.2f}<br />'.format(
                key, value[1], value[0], value[2])

        namespace: dict[str, str] = {
            'articles': articles,
            'invoiceNumber': invoice_number,
            'date': '{0:%Y-%m-%d %H:%M}'.format(invoice_data[0].date),
            'total': '{0:.2f}'.format(invoice_data[0].invoice_total),
            'taxes': taxes_text,
            'tischCode': invoice_data[0].table,
            'kellnerKurzName': invoice_data[0].waiter,
            'kasseid': invoice_data[0].register_id,
            'barumsatzNummer': invoice_data[0].cash_nr,
            'qrCode': invoice_data[0].qr_code,
            'vorname': invoice_data[0].first_name if invoice_data[0].first_name is not None else "",
            'nachname': invoice_data[0].last_name if invoice_data[0].last_name is not None else "",
            'strasse': invoice_data[0].street if invoice_data[0].street is not None else "",
            'plz': invoice_data[0].zip_code if invoice_data[0].zip_code is not None else "",
            'ort': invoice_data[0].city if invoice_data[0].city is not None else "",
            'firma': invoice_data[0].company if invoice_data[0].company is not None else ""
        }
        invoice: str = str(tmpl.expand(namespace))  # type: ignore

        if output == 'html':
            return invoice.replace("\n", "").encode('iso-8859-1')
        else:
            parser = EscPosHTMLParser(PRINTERPROFILE)
            parser.feed(invoice)
            return parser.output

    def print_invoice(self, invoice_id: int, template_name: str, output: str = "escpos") -> None:
        global db_connection
        result: DBResult = db_connection.get_invoice_data(invoice_id)
        if not result:
            raise LookupError

        row: tuple[Any, ...]
        invoice_data: list[InvoiceDataRow] = []
        for row in result:
            invoice_data_row: InvoiceDataRow = InvoiceDataRow(
                invoice_nr=row[0],
                date=row[1],
                article_amount=row[2],
                article_sum=row[3],
                article=row[4],
                invoice_total=row[5],
                tax=row[6],
                tax_sum=row[7],
                tax_desc=row[8],
                table=row[9],
                waiter=row[10],
                register_id=row[11],
                cash_nr=row[12],
                qr_code=row[13],
                first_name=row[14],
                last_name=row[15],
                street=row[16],
                zip_code=row[17],
                city=row[18],
                company=row[19])
            invoice_data.append(invoice_data_row)

        save_dir: Path = SPOOLDIR / invoice_data[0].waiter
        save_dir.mkdir(parents=True, exist_ok=True)
        # template: Path = Path()
        with open(PRINTTEMPLATESPATH / f"{template_name}.html", "r") as f:
            template: str = f.read()
            if output == "escpos":
                with open(save_dir / f"{template_name}_{invoice_id}", "wb") as f:
                    invoice: bytes = self.parse_invoice(
                        invoice_data, template, output=output)
                    f.write(invoice)
            elif output == "html":
                invoice: bytes = self.parse_invoice(
                    invoice_data, template, output=output)
                # sys.stdout.write(invoice.decode('iso-8859-1'))
                print(invoice.decode('iso-8859-1'))
                sys.stdout.flush()

            else:
                raise ValueError(f"Unknown output type: {output}")


if __name__ == "__main__":
    config_loader = ConfigLoader()
    config: dict[str, Any] = config_loader.config
    db_connection = wz.Database()
    try:
        db_connection.connect_to_database(config["database"]["server"],
                                          config["database"]["username"],
                                          config["database"]["password"],
                                          config["database"]["database"])
    except KeyError as e:
        logger.error(
            f"CRITICAL: Missing database configuration key: {e}. Check your config.toml. Exiting.")
        exit(1)
    except Exception as e:
        logger.error(f"CRITICAL: Failed to connect to database: {e}. Exiting.")
        logger.debug(f"Used config: {config}")
        exit(1)

    import logging.config
    logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
    logger.info("Starting print service")
    print_service = PrintService()
    try:
        print_service.listen_for_input()
    except KeyboardInterrupt:
        logger.info("Print service shutting down...")
    finally:
        if db_connection:
            db_connection.close()
        logger.info("Print service stopped.")
