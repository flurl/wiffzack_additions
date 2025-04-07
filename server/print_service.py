#!/usr/bin/env python3

import datetime
import sys
import queue
import threading
import logging
from pathlib import Path
from string import Template
from decimal import Decimal
from typing import Any, NoReturn, TypeAlias, Optional
from dataclasses import dataclass, field

from lib.EscPos.EscPosHTMLParser import EscPosHTMLParser
import wiffzack as wz
from wiffzack.types import DBResult


logger: logging.Logger = logging.getLogger(__name__)


@dataclass(order=True)
class PrintJob:
    invoice_id: int = field(compare=False)
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

    def enqueue_print_job(self, invoice_id: int) -> None:
        """
        Enqueues a print job for a given invoice ID.

        The print jobs are prioritized based on the invoice ID, with higher
        invoice IDs having higher priority. This is achieved by negating the
        invoice ID when adding it to the priority queue, as PriorityQueue prioritizes
        smaller numbers

        Args:
            invoice_id (int): The ID of the invoice to be printed.
        """
        self.print_queue.put(
            (-invoice_id, PrintJob(invoice_id)))

    def print_worker(self) -> NoReturn:
        while True:
            item: print_queue_item = self.print_queue.get()
            invoice_id: int = item[1].invoice_id
            retries: int = item[1].tries

            if retries >= 3:
                # give up after 3 tries
                self.print_queue.task_done()
                logger.error(
                    f"Permanently failed to print invoice: {invoice_id}. Skipping…")
                continue

            logger.debug(f"Printing invoice: {invoice_id}")
            try:
                self.print_invoice(invoice_id)
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
        for line in sys.stdin:
            try:
                invoice_id: int = int(line.strip())
                self.enqueue_print_job(invoice_id)
            except ValueError:
                logging.error(f"Invalid input: {line.strip()}")

    def parse_invoice(self,
                      invoice_data: list[InvoiceDataRow],
                      template: Path,
                      output: str = 'html') -> str:

        with open(template, 'r') as f:
            tmpl: Template = Template(f.read())

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

        invoice: str = tmpl.safe_substitute({'articles': articles,
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
                                             })
        if output == 'html':
            return invoice.replace("\n", "")
        else:
            parser = EscPosHTMLParser()
            parser.feed(invoice)
            return parser.code

    def print_invoice(self, invoice_id: int):
        result: DBResult = wz.db.get_invoice_data(invoice_id)
        if not result:
            raise LookupError

        SPOOLDIR: Path = Path("./spool")
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
        template: Path = Path("./print_templates/invoice/invoice.html")
        with open(save_dir / f"invoice_{invoice_id}", "w") as f:
            f.write(self.parse_invoice(invoice_data, template, "escpos"))

        """fh = open( SPOOLDIR+os.sep+bar+os.sep+'invoice_'+str(uuid.uuid1()), 'wb')
        fh.write(self._parseInvoice('escpos', template=template))
        fh.close()
        if self._rechnung_m_name:
            self._rechnung_m_name = False
            time.sleep(1)
            fh = open( SPOOLDIR+os.sep+bar+os.sep+ \
                      'invoice_'+str(uuid.uuid1()), 'wb')
            fh.write(self._parseInvoice('escpos', template=template))
            fh.close()"""


if __name__ == "__main__":
    import tomllib
    with open("config.toml", "rb") as f:
        config: dict[str, Any] = tomllib.load(f)
    wz.db.connect_to_database(config["database"]["server"],
                              config["database"]["username"],
                              config["database"]["password"],
                              config["database"]["database"])
    import logging.config
    logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
    logger.info("Starting print service")
    print_service = PrintService()
    print_service.listen_for_input()
