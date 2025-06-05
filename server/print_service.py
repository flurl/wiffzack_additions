#!/usr/bin/env python3

import datetime
import sys
import logging
from pathlib import Path
from decimal import Decimal
from typing import Any, LiteralString, Optional
from dataclasses import dataclass
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


def parse_invoice_content(
    invoice_data_rows: list[InvoiceDataRow],
    template_content: str,  # Actual content of the template file
    output_format: str = 'html'
) -> bytes:
    """
    Parses invoice data using the provided template content and returns output bytes.
    """
    logger.debug(
        f"Parsing invoice {invoice_data_rows[0].invoice_nr} for output: {output_format}")

    try:
        tmpl: step.Template = step.Template(template_content)  # type: ignore
        articles: str = ''
        taxes: dict[str, list[Decimal | str]] = {}
        for row in invoice_data_rows:
            amount: int = row.article_amount
            article: str = row.article
            sum: Decimal = row.article_sum
            tax_type: str = row.tax
            articles_row: str = "{0:<3d}x {1:<41s} {2:>7.2f} {3:s}<br />".format(
                amount, article, sum, tax_type)
            articles += articles_row
            try:
                # Ensure taxes[row.tax][0] and taxes[row.tax][2] are Decimal before addition
                taxes[row.tax][0] = Decimal(taxes[row.tax][0]) + row.tax_sum
                taxes[row.tax][2] = Decimal(
                    taxes[row.tax][2]) + row.article_sum
            except KeyError:
                taxes[row.tax] = [row.tax_sum, row.tax_desc, row.article_sum]
        invoice_number: str = str(invoice_data_rows[0].invoice_nr)

        taxes_text: str = ''
        for key, value in taxes.items():
            taxes_text += '{0}: {1} MwSt. von {3:.2f} = {2:.2f}<br />'.format(
                key, value[1], value[0], value[2])

        first_row: InvoiceDataRow = invoice_data_rows[0]
        namespace: dict[str, str] = {
            'articles': articles,
            'invoiceNumber': invoice_number,
            'date': '{0:%Y-%m-%d %H:%M}'.format(first_row.date),
            'total': '{0:.2f}'.format(first_row.invoice_total),
            'taxes': taxes_text,
            'tischCode': first_row.table,
            'kellnerKurzName': first_row.waiter,
            'kasseid': first_row.register_id,
            'barumsatzNummer': first_row.cash_nr,
            'qrCode': first_row.qr_code,
            'vorname': first_row.first_name if first_row.first_name is not None else "",
            'nachname': first_row.last_name if first_row.last_name is not None else "",
            'strasse': first_row.street if first_row.street is not None else "",
            'plz': first_row.zip_code if first_row.zip_code is not None else "",
            'ort': first_row.city if first_row.city is not None else "",
            'firma': first_row.company if first_row.company is not None else ""
        }
        invoice: str = str(tmpl.expand(namespace))  # type: ignore

        if output_format == 'html':
            return invoice.replace("\n", "").encode('iso-8859-1')
        else:
            parser = EscPosHTMLParser(PRINTERPROFILE)
            parser.feed(invoice)
            return parser.output
    except Exception as e:
        logger.error(
            f"Error during template parsing for invoice {invoice_data_rows[0].invoice_nr}: {e}", exc_info=True)
        raise


def process_single_print_job(invoice_id: int, template_name: str, output_format: str = "escpos") -> None:
    """
    Processes a single print job: fetches data, loads template, generates output, and handles it.
    """
    logger.debug(
        f"Processing job for invoice: {invoice_id}, template: {template_name}, output: {output_format}")
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

    save_dir: Path = SPOOLDIR / \
        (invoice_data[0].waiter if invoice_data[0].waiter else "_unknown_waiter_")
    save_dir.mkdir(parents=True, exist_ok=True)

    template_file_path: Path = PRINTTEMPLATESPATH / f"{template_name}.html"
    try:
        with open(template_file_path, "r") as template_f:
            template_content: str = template_f.read()
    except Exception as e:
        logger.error(
            f"Failed to read template file {template_file_path} for invoice {invoice_id}: {e}", exc_info=True)
        raise  # Re-raise to be caught by print_worker and retried

    output_file_path: Path | None = None
    if output_format == "escpos":
        output_file_path = save_dir / f"{template_name}_{invoice_id}"

    try:
        # First, try to parse the invoice and generate the content
        # This way, if parse_invoice fails, we haven't opened the output file yet (for escpos)
        invoice_bytes: bytes = parse_invoice_content(
            invoice_data, template_content, output_format=output_format)

        if output_format == "escpos":
            if output_file_path:  # Should always be true here
                with open(output_file_path, "wb") as out_f:
                    out_f.write(invoice_bytes)
                logger.debug(
                    f"Successfully wrote escpos output to {output_file_path}")
        elif output_format == "html":
            print(invoice_bytes.decode('iso-8859-1'))
            sys.stdout.flush()
        else:
            raise ValueError(f"Unknown output type: {output_format}")
    except Exception as e:
        logger.error(
            f"Exception processing invoice_id {invoice_id} (output: {output_format}): {type(e).__name__}: {e}", exc_info=True)
        if output_format == "escpos" and output_file_path and output_file_path.exists() and output_file_path.stat().st_size == 0:
            logger.warning(
                f"Output file {output_file_path} for invoice {invoice_id} exists and is 0 bytes after error.")
        elif output_format == "escpos" and output_file_path and not output_file_path.exists():
            logger.info(
                f"Output file {output_file_path} for invoice {invoice_id} was not created (error likely occurred before file open).")
        raise  # Re-raise to be caught by print_worker for retry logic


if __name__ == "__main__":
    config_loader = ConfigLoader()
    config: dict[str, Any] = config_loader.config

    import logging.config
    logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
    logger.info("Starting print service script")

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

    try:
        # Read one line from stdin, as server.py spawns one process per request
        # and closes stdin after writing one line (or uses communicate).
        line: str | Any = sys.stdin.readline()
        if not line:
            logger.warning("No input received on stdin. Exiting.")
            sys.exit(0)  # Exit gracefully if no input

        params: list[str] = line.strip().split(":")
        try:
            invoice_id_arg: int = int(params[0])
            template_arg: str = params[1] if len(params) > 1 else "invoice"
            output_arg: str = params[2] if len(params) > 2 else "escpos"
        except (ValueError, IndexError) as e:
            logger.error(
                f"Invalid input format: '{line.strip()}'. Error: {e}", exc_info=True)
            sys.exit(1)

        process_single_print_job(invoice_id_arg, template_arg, output_arg)

    except KeyboardInterrupt:
        logger.info("Print service script interrupted.")
    except Exception as e:
        logger.error(
            f"Unhandled exception in print service script: {e}", exc_info=True)
        sys.exit(1)  # Indicate failure
    finally:
        if 'db_connection' in globals() and db_connection:
            db_connection.close()
        logger.info("Print service script finished.")
