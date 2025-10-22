#!/usr/bin/env python3

from dataclasses import asdict
import logging
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, LiteralString
import urllib.request
import json  # Add this import
import random  # Add this import
import urllib.error
import csv

from flask import Flask, jsonify, make_response, render_template, request, send_from_directory, g
from flask.wrappers import Response
from flask_cors import CORS
from werkzeug.wrappers import Response
from wiffzack import Database
from wiffzack.db_connection import DatabaseConnection
from wiffzack.types import Article, StorageModifier, DBResult
import lib.messages as messages
from lib.config import ConfigLoader
import lib.checklist as checklist

config_loader = ConfigLoader()
config: dict[str, Any] = config_loader.config

# Ensure the log directory exists before configuring logging
# This path should match the directory used in logging.conf for fileHandler
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

JOTD_FILE_PATH: Path = Path("./stupidstuff.json")
logger: logging.Logger = logging.getLogger(__name__)
storage_transfer_logger: logging.Logger = logging.getLogger("storage_transfer")

# --- Static File Configuration ---
# Calculate the path to the 'dist' directory relative to this script (server.py)
# Go up one level from 'server/' to the project root, then into 'client/dist/'
STATIC_FOLDER: Path = Path(
    __file__).resolve().parent.parent / 'client' / 'dist'

app = Flask(__name__)
# Limit CORS to API routes if needed
CORS(app, resources={r'/api/*': {'origins': '*'}})

# --- Database Connection Management ---


def get_db() -> Database:
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        g.db = Database()
        try:
            g.db.connect_to_database(
                config["database"]["server"],
                config["database"]["username"],
                config["database"]["password"],
                config["database"]["database"]
            )
        except KeyError as e:
            logger.error(
                f"CRITICAL: Missing database configuration key: {e}. Check your config.toml.")
            raise  # Re-raise to halt app or be caught by Flask error handlers
        except Exception as e:
            logger.error(f"CRITICAL: Failed to connect to database: {e}.")
            raise
    return g.db


@app.teardown_appcontext
def teardown_db(exception: BaseException | None = None) -> None:
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.route('/api/<string:client>/sales', methods=['GET'])
def get_sales(client: str) -> Response:
    """
    Retrieve total sales for a specific client from the database.

    This endpoint handles GET requests to retrieve the total sales
    for a given waiter's short name. The sales are aggregated from
    the 'rechnungen_details' and 'rechnungen_basis' tables in the
    database.

    Parameters:
    - client (str): The short name of the waiter to filter
      sales data.

    Returns:
    - Response: A JSON response containing the aggregated total sales
      data grouped by the waiter's short name.
    """
    db: Database = get_db()
    result: DBResult = db.get_client_sales(client)
    return mk_response(result, "sales")


@app.route('/api/<string:client>/tallied_articles', methods=['GET'])
def get_tallied_articles(client: str) -> Response:
    return mk_response(get_db().get_tallied_articles(client), "Tallied articles")


@app.route('/api/<string:client>/latest_tallied_articles', methods=['GET'])
def get_latest_tallied_articles(client: str) -> Response:
    return mk_response(get_db().get_latest_tallied_articles(client), "Latest")


@app.route('/api/wardrobe_sales', methods=['GET'])
def get_wardrobe_sales() -> Response:
    result: DBResult = get_db().get_wardrobe_sales()
    return mk_response(result, "Wardrobe Sales")


@app.route('/api/artikel', methods=['GET'])
def get_articles() -> Response:
    query: LiteralString = f"""
    select artikel_id, artikel_bezeichnung, artikel_ep from artikel_basis
    """
    rows: DBResult = get_db().execute_query(query)
    return mk_response(rows)


@app.route("/api/articles", methods=["GET"])
@app.route("/api/articles/<int:article_id>", methods=["GET"])
def get_article(article_id: int | None = None) -> Response:
    result: DBResult = get_db().get_article(article_id)
    return mk_response(result)


# --- API Routes ---


@app.route('/api/storage_article_groups', methods=['GET'])
@app.route('/api/storage_article_groups/<int:storage_id>', methods=['GET'])
def get_storage_article_groups(storage_id: int | None = None) -> Response:
    db: Database = get_db()
    if storage_id is None:
        result: DBResult = db.get_all_storage_article_groups()
    else:
        result: DBResult = db.get_article_groups_in_storage(storage_id)
    return mk_response(result)


@app.route('/api/storage_article_by_group/<int:group>', methods=['GET'])
def get_article_by_group(group: int) -> Response:
    result: DBResult = get_db().get_storage_articles_by_group(group)
    return mk_response(result)


@app.route("/api/update_storage/to/<int:to_storage_id>", methods=["POST"])
@app.route("/api/update_storage/from/<int:from_storage_id>", methods=["POST"])
@app.route('/api/update_storage/from/<int:from_storage_id>/to/<int:to_storage_id>', methods=['POST'])
def update_storage(to_storage_id: int | None = None, from_storage_id: int | None = None) -> Response:
    """
    Update the storage by moving articles between storages or within a single storage.

    This endpoint handles POST requests to update the storage by either adding or
    withdrawing articles from a storage, or moving articles between two storages.
    The operation can be performed in absolute or relative mode.

    Parameters:
    - to_storage_id (int, optional): The ID of the storage to add articles to.
    - from_storage_id (int, optional): The ID of the storage to withdraw articles from.

    Request Body (JSON):
    - A dictionary where keys are arbitrary and values are dictionaries with the following structure:
      {
        "id": (int) Article ID,
        "name": (str) Article name,
        "amount": (int) Amount to add or withdraw
      }

    Query Parameters:
    - method (str, optional): If set to "absolute", the operation will be performed in absolute mode.
      Otherwise, it defaults to relative mode.

    Returns:
    - Response: A JSON response indicating the success or failure of the operation.
      {'success': True} or {'success': False}
    """
    db: Database = get_db()
    articles: Any | None = request.json
    absolute: bool = True if request.args.get(
        "method") == "absolute" else False
    logger.debug(f"Moving from {from_storage_id} to {to_storage_id}")
    logger.debug(articles)
    if articles is None or len(articles) == 0:
        return jsonify({'success': False})

    if from_storage_id is not None:
        try:
            result: DBResult = db.get_storage_name(from_storage_id)
            assert result is not None
            from_storage_name: str = result[0][0]
        except AssertionError:
            return jsonify({'success': False, 'message': f'Invalid from storage ID {from_storage_id}'})

        try:
            for article in articles.values():
                logger.debug(
                    f"Processing withdrawal for article: {article} from storage: {from_storage_id}")
                sm: StorageModifier = StorageModifier(article=Article(article["id"], article["name"]),
                                                      storage_id=from_storage_id,
                                                      amount=article["amount"])
                db.withdraw_article_from_storage(sm, absolute=absolute)
                storage_transfer_logger.info(
                    f"Withdrew|{sm.amount}|{sm.article.id}-{sm.article.name}|{from_storage_id}-{from_storage_name}"
                )
        except Exception:
            logger.error(
                f"Error withdrawing article from storage {from_storage_id}", exc_info=True)
            return jsonify({'success': False})

    if to_storage_id is not None:
        try:
            result: DBResult = db.get_storage_name(to_storage_id)
            assert result is not None
            to_storage_name: str = result[0][0]
        except AssertionError:
            return jsonify({'success': False, 'message': f'Invalid to storage ID {to_storage_id}'})

        try:
            for article in articles.values():
                logger.debug(
                    f"Processing addition for article: {article} to storage: {to_storage_id}")
                sm: StorageModifier = StorageModifier(article=Article(article["id"], article["name"]),
                                                      storage_id=to_storage_id,
                                                      amount=article["amount"])
                db.add_article_to_storage(sm, absolute=absolute)
                storage_transfer_logger.info(
                    f"Added|{sm.amount}|{sm.article.id}-{sm.article.name}|{to_storage_id}-{to_storage_name}"
                )
        except Exception:
            logger.error(
                f"Error adding article to storage {to_storage_id}", exc_info=True)
            return jsonify({'success': False})

    return jsonify({'success': True})


@app.route("/api/empty_storage/<int:storage_id>", methods=["GET"])
def empty_storage(storage_id: int) -> Response:
    get_db().empty_storage(storage_id)
    return jsonify({'success': True})


@app.route("/api/get_articles_in_storage/<int:storage_id>", methods=["GET"])
@app.route("/api/get_articles_in_storage/<int:storage_id>/article_group/<int:article_group_id>", methods=["GET"])
def get_articles_in_storage(storage_id: int, article_group_id: int | None = None) -> Response:
    show_not_in_stock: bool = True if request.args.get(
        "show_not_in_stock") == "1" else False
    logger.debug(
        f"Fetching articles for storage_id: {storage_id}, article_group_id: {article_group_id}, show_not_in_stock: {show_not_in_stock}")
    result: DBResult = get_db().get_articles_in_storage(
        storage_id, article_group_id, show_not_in_stock)
    logger.debug(result)
    return mk_response(result)


@app.route("/api/get_storage_name/<int:storage_id>", methods=["GET"])
def get_storage_name(storage_id: int) -> Response:
    result: DBResult = get_db().get_storage_name(storage_id)
    logger.debug(result)
    return mk_response(result)


@app.route("/api/get_config", methods=["GET"])
@app.route("/api/get_config/<string:terminal_id>", methods=["GET"])
def get_config(terminal_id: str | None = None) -> Response:
    logger.debug(config)
    try:
        if terminal_id is None:
            return jsonify({'success': True, 'config': config["terminal_config"]})
        else:
            return jsonify({'success': True, 'config': config["terminal_config"][terminal_id]})
    except KeyError:
        return jsonify({'success': False})


@app.route("/api/set_init_inventory/storage/<int:storage_id>", methods=["GET"])
def set_init_inventory(storage_id: int) -> Response:
    """
    sets the initial inventory for a storage.

    Parameters:
    - storage_id (int): The ID of the storage to set the initial inventory for.

    Returns:
    - Response: A JSON response indicating the success or failure of the operation.
      {'success': True} or {'success': False}
    """
    db: Database = get_db()
    result: DBResult = db.get_storage_name(storage_id)
    assert result is not None
    storage_name: str = result[0][0]

    filename: str = f"{config['server']['init_stock_directory']}{storage_name}.csv"

    try:
        with open(filename, mode='r') as file:
            csvFile = csv.DictReader(file, delimiter=';')
            for line in csvFile:
                id: int = int(line["article_id"])
                amount: int = int(line["amount"])
                result: DBResult = db.get_article(id)
                assert result is not None
                article_name: str = result[0][1]
                sm: StorageModifier = StorageModifier(article=Article(id, article_name),
                                                      storage_id=storage_id,
                                                      amount=amount)
                try:
                    db.update_storage(sm, absolute=True)
                    storage_transfer_logger.info(
                        f"Init|{sm.amount}|{sm.article.id}-{sm.article.name}|{storage_id}-{storage_name}")
                except Exception:
                    logger.error(
                        f"Error setting initial inventory for article ID {id} in storage {storage_id} from file {filename}", exc_info=True)
                    return jsonify({'success': False})
    except FileNotFoundError:
        logger.error(
            f"Initial inventory file not found: {filename}", exc_info=True)
        return jsonify({'success': False})

    return jsonify({'success': True})


@app.route("/api/invoice/list", methods=["GET"])
@app.route("/api/invoice/list/<string:waiter>", methods=["GET"])
def get_invoice_list(waiter: str | None = None) -> Response:
    invoice_type: int | None = request.args.get("invoice_type", type=int)
    result: DBResult = get_db().get_invoice_list(
        waiter=waiter, invoice_type=invoice_type)
    return mk_response(result)


@app.route("/api/invoice/print/<int:invoice_id>", methods=["GET"])
def print_invoice(invoice_id: int) -> Response:
    """
    Triggers the printing of an invoice by sending the invoice ID to the print service.

    This endpoint handles GET requests to initiate the printing of a specific invoice.
    It communicates with the print service by writing the invoice ID to the standard
    input of the print service process.

    Parameters:
    - invoice_id (int): The ID of the invoice to be printed.

    Returns:
    - Response: A JSON response indicating the success or failure of the operation.
      {'success': True} or {'success': False}
    """
    logger.info(
        f"Attempting to print invoice {invoice_id} by spawning a new print_service process.")
    try:
        command: list[str] = [sys.executable, "print_service.py"]
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            text=True  # For string input to stdin
        )

        print_data: str = f"{invoice_id}:invoice:escpos\n"

        if process.stdin:
            process.stdin.write(print_data)
            process.stdin.flush()
            process.stdin.close()  # Signal EOF to print_service.py
        else:
            logger.error(
                f"Failed to get stdin for print_service process for invoice {invoice_id}.")
            return jsonify({'success': False, 'message': 'Failed to open stdin for print service'})

        logger.info(
            f"Print job for invoice {invoice_id} dispatched to a new print_service process.")
        return jsonify({'success': True, 'message': 'Print job dispatched.'})

    except FileNotFoundError:
        logger.error(
            f"print_service.py not found. Cannot print invoice {invoice_id}.", exc_info=True)
        return jsonify({'success': False, 'message': 'Print service executable not found.'})
    except Exception as e:
        logger.error(
            f"Failed to start print service for invoice {invoice_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Failed to start print service: {str(e)}'})


@app.route("/api/invoice/html/<int:invoice_id>", methods=["GET"])
def get_invoice_html(invoice_id: int) -> Response:
    logger.info(f"Fetching HTML for invoice {invoice_id} via new process")
    try:
        command: list[str] = [sys.executable, "print_service.py"]
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Capture stderr for debugging
            text=True,  # For string I/O
            encoding='iso-8859-1'  # Match print_service.py's output encoding
        )

        print_data: str = f"{invoice_id}:invoice:html\n"
        stdout_data: str
        stderr_data: str
        stdout_data, stderr_data = process.communicate(
            input=print_data, timeout=30)

        if process.returncode != 0:
            logger.error(
                f"Print service (HTML) for invoice {invoice_id} exited with code {process.returncode}. Stderr: {stderr_data}")
            return jsonify({'success': False, 'message': f'Print service error: {stderr_data}'})

        if not stdout_data:
            logger.error(
                f"Print service (HTML) for invoice {invoice_id} produced no output. Stderr: {stderr_data}")
            return jsonify({'success': False, 'message': 'Print service produced no output'})

        return mk_response(stdout_data.strip())
    except subprocess.TimeoutExpired:
        logger.error(
            f"Print service (HTML) for invoice {invoice_id} timed out.")
        return jsonify({'success': False, 'message': 'Print service timed out'})
    except Exception as e:
        logger.error(f"Failed to get html representation of invoice: {e}")
        return jsonify({'success': False})


@app.route("/api/invoice_type", methods=["GET"])
@app.route("/api/invoice_type/<int:invoice_type_id>", methods=["GET"])
def get_invoice_type(invoice_type_id: int | None = None) -> Response:
    result: DBResult = get_db().get_invoice_type(invoice_type_id)
    return mk_response(result)


@app.route("/api/message/list", methods=["GET"])
def get_messages() -> Response:
    msgs: list[messages.Message] = messages.get_messages_list()
    # Convert Message objects to dicts, ensuring path is a string
    msgs_dicts: list[dict[str, Any]] = []
    for msg in msgs:
        msg_dict: dict[str, Any] = asdict(msg)
        # # Explicitly convert the Path object to a string
        # if isinstance(msg_dict.get("path"), pathlib.Path):
        #     msg_dict["path"] = str(msg_dict["path"])
        msgs_dicts.append(msg_dict)
    return jsonify({"success": True, "messages": msgs_dicts})


@app.route("/api/message/<string:message_path>", methods=["GET"])
def send_message(message_path: str) -> Response:
    try:
        msg: messages.Message = messages.get_message(message_path)
        return jsonify({"success": True,
                        "data": {"message": msg}})
    except FileNotFoundError:
        return jsonify({'success': False})


@app.route("/message/html/<string:message_path>/", methods=["GET"])
@app.route("/message/html/<string:message_path>/<path:path>", methods=["GET"])
def send_html_message(message_path: str, path: str | None = None) -> Response:
    try:
        msg: messages.Message = messages.get_message(message_path)
        if msg.type != "html":
            raise ValueError
    except FileNotFoundError:
        return jsonify({'success': False})

    if path is None:
        path = f"{msg.name}.{msg.type}"
    return send_from_directory(messages.MESSAGEDIR / message_path, path)


@app.route("/api/recipe/list", methods=["GET"])
def get_receipes() -> Response:
    result: DBResult = get_db().get_receipes()
    return mk_response(result)


@app.route("/api/restart", methods=["GET"])
def restart_server() -> Response:
    """
    Signals the server to restart by creating a flag file.
    An external watchdog process is expected to monitor this file
    and perform the actual server restart.
    """
    try:
        flag_file_path_str: str = "./.restart"

        flag_file = Path(flag_file_path_str)
        flag_file.touch()  # Create the file or update its timestamp if it exists
        logger.info(f"Restart requested. Flag file created at: {flag_file}")
        return jsonify({'success': True, 'message': 'Server restart signaled.'})
    except Exception as e:
        logger.error(f"Error creating restart flag file: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error creating restart flag: {str(e)}'})


@app.route("/api/alarm/trigger/<string:location>", methods=["GET"])
def trigger_alarm(location: str) -> Response:
    """
    Triggers an external alarm by making a GET request to a predefined URL.

    Parameters:
    - location (str): The location identifier to be included in the alarm URL.

    Returns:
    - Response: A JSON response indicating the success or failure of the alarm trigger.
    """
    try:
        alarm_url_template: str | None = config.get("alarm", {}).get("url")
        if not alarm_url_template:
            logger.error(
                "Alarm trigger requested, but 'alarm.url' is not configured in server settings.")
            return jsonify({'success': False, 'message': 'Alarm URL not configured on server.'})
        alarm_url: str = alarm_url_template.format(location=location)
    # Handles if .format(location=location) fails due to unexpected template
    except KeyError as e:
        logger.error(
            f"Alarm URL template in config is invalid or missing 'location' placeholder: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Invalid alarm URL template in server configuration.'})

    logger.info(
        f"Attempting to trigger alarm for location '{location}' at URL: {alarm_url}")

    try:
        with urllib.request.urlopen(alarm_url, timeout=10) as response:
            if response.status == 200:
                logger.info(
                    f"Alarm successfully triggered for location '{location}'. Response: {response.read().decode('utf-8')}")
                return jsonify({'success': True, 'message': f'Alarm triggered successfully for {location}.'})
            else:
                logger.error(
                    f"Failed to trigger alarm for location '{location}'. Status: {response.status}, Response: {response.read().decode('utf-8')}")
                return jsonify({'success': False, 'message': f'Alarm server returned status {response.status}.'})
    except urllib.error.URLError as e:
        logger.error(
            f"Error triggering alarm for location '{location}' at {alarm_url}: {e.reason}", exc_info=True)
        return jsonify({'success': False, 'message': f'Failed to connect to alarm server: {e.reason}'})
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while triggering alarm for '{location}': {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'An unexpected error occurred: {str(e)}'})


@app.route("/api/jotd", methods=["GET"])
def get_jotd() -> Response:
    """
    Retrieves a random "Joke of the Day" from the stupidstuff.json file.

    Returns:
    - Response: A plaintext response containing the body of a randomly selected joke,
                or an error message if the file cannot be processed.
    """
    try:
        if not JOTD_FILE_PATH.is_file():
            logger.error(f"JOTD file not found at {JOTD_FILE_PATH}")
            return mk_response("Joke file not found.", heading="Error")

        with open(JOTD_FILE_PATH, 'r', encoding='utf-8') as f:
            jokes: list[dict[str, Any]] = json.load(f)

        if not jokes:
            logger.error(f"JOTD file {JOTD_FILE_PATH} is empty or not a list.")
            return mk_response("No jokes available or file format error.", heading="Error")

        body: str = ""
        while body == "":
            selected_joke: dict[str, Any] = random.choice(jokes)
            try:
                body = selected_joke["body"]
                if body == "":
                    logger.warning(
                        f"Joke {selected_joke['id']} body is empty.")
            except KeyError:
                return mk_response("Joke body not found.")
        return mk_response(body)

    except json.JSONDecodeError:
        logger.error(
            f"Error decoding JSON from {JOTD_FILE_PATH}", exc_info=True)
        return mk_response("Error reading joke file format.", heading="Error")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred in get_jotd: {e}", exc_info=True)
        return mk_response(f"An unexpected error occurred: {str(e)}", heading="Error")

# region Checklist related routes ---


@app.route("/api/checklist/list", methods=["GET"])
def get_checklists() -> Response:
    dbConn: DatabaseConnection = get_db().connection
    checklists: list[checklist.Checklist] = checklist.get_all_checklists(
        dbConn)
    return mk_response([asdict(c) for c in checklists])


@app.route("/api/checklist/latest/by_category/<string:category>", methods=["GET"])
def get_latest_checklist_by_category(category: str) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    checklists: list[checklist.Checklist] = checklist.get_latest_closed_checklists_by_category(
        dbConn, category, config["checklist"]["expiry_mins"])
    if len(checklists) == 0:
        return jsonify({'success': False})
    return mk_response([asdict(c) for c in checklists])


@app.route("/api/checklist/latest/<int:master_id>", methods=["GET"])
@app.route("/api/checklist/latest/<int:master_id>/<int:closed>", methods=["GET"])
def get_latest_checklist(master_id: int, closed: int = 0) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    cl: checklist.Checklist | None = checklist.get_latest_checklist(
        dbConn, master_id, config["checklist"]["expiry_mins"], closed)
    if cl is None:
        return jsonify({'success': False})
    return mk_response(asdict(cl))


@app.route("/api/checklist/history/<int:master_id>", methods=["GET"])
def get_checklist_history(master_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    checklists: list[checklist.Checklist] = checklist.get_checklist_history(
        dbConn, master_id)
    return mk_response([asdict(c) for c in checklists])


@app.route("/api/checklist/close/<int:checklist_id>", methods=["GET"])
def close_checklist(checklist_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    checklist.close_checklist(dbConn, checklist_id)
    return jsonify({'success': True})


@app.route("/api/checklist/master/new", methods=["POST"])
def create_checklist_master() -> Response:
    dbConn: DatabaseConnection = get_db().connection
    json: Any | None = request.json
    if json is None:
        return jsonify({'success': False})
    name: str = json["name"]
    category: str = json["category"]
    master: checklist.ChecklistMaster = checklist.create_checklist_master(
        dbConn, name, category)

    return mk_response({'id': master.id, 'name': master.name})


@app.route("/api/checklist/master/list", methods=["GET"])
def get_checklist_masters() -> Response:
    dbConn: DatabaseConnection = get_db().connection
    masters: list[checklist.ChecklistMaster] = checklist.get_all_checklist_masters(
        dbConn)
    return mk_response([asdict(m) for m in masters])


@app.route("/api/checklist/master/list/category/<string:category>", methods=["GET"])
def get_checklist_masters_by_category(category: str) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    masters: list[checklist.ChecklistMaster] = checklist.get_checklist_masters_by_category(
        dbConn, category)
    return mk_response([asdict(m) for m in masters])


@app.route("/api/checklist/master/<int:master_id>", methods=["GET"])
def get_checklist_master(master_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    master: checklist.ChecklistMaster | None = checklist.get_checklist_master(
        dbConn, master_id)
    if master is None:
        return jsonify({'success': False})
    return mk_response(asdict(master))


@app.route("/api/checklist/master/update/<int:master_id>", methods=["POST"])
def update_checklist_master(master_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    json_data: Any | None = request.json
    if json_data is None:
        return jsonify({'success': False, 'message': 'No JSON data provided'})
    name: str = json_data["name"]
    category: str = json_data["category"]
    master: checklist.ChecklistMaster = checklist.ChecklistMaster(
        id=master_id, name=name, category=category)
    checklist.update_checklist_master(dbConn, master)
    return jsonify({'success': True})


@app.route("/api/checklist/master/delete/<int:master_id>", methods=["GET"])
def delete_checklist_master(master_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    checklist.delete_checklist_master(dbConn, master_id)
    return jsonify({'success': True})


@app.route("/api/checklist/master/<int:master_id>/questions", methods=["GET"])
def get_questions_for_master(master_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    questions: list[checklist.ChecklistQuestion] = checklist.get_questions_for_master(
        dbConn, master_id)
    return mk_response([asdict(q) for q in questions])


@app.route("/api/checklist/question/new", methods=["POST"])
def create_checklist_question() -> Response:
    dbConn: DatabaseConnection = get_db().connection
    json: Any | None = request.json
    if json is None:
        return jsonify({'success': False})
    master_id: int = json["master_id"]
    order: int = json["order"]
    text: str = json["text"]
    question: checklist.ChecklistQuestion = checklist.create_checklist_question(
        dbConn, text, order, master_id)
    return mk_response(asdict(question))


@app.route("/api/checklist/question/<int:question_id>", methods=["GET"])
def get_checklist_question(question_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    question: checklist.ChecklistQuestion | None = checklist.get_checklist_question(
        dbConn, question_id)
    if question is None:
        return jsonify({'success': False})
    return mk_response(asdict(question))


@app.route("/api/checklist/question/update/<int:question_id>", methods=["POST"])
def update_checklist_question(question_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    json: Any | None = request.json
    if json is None:
        return jsonify({'success': False})
    master_id: int = json["master_id"]
    order: int = json["order"]
    text: str = json["text"]
    question: checklist.ChecklistQuestion = checklist.ChecklistQuestion(
        id=question_id, text=text, order=order, master_id=master_id)
    checklist.update_checklist_question(
        dbConn, question)
    return jsonify({'success': True})


@app.route("/api/checklist/question/delete/<int:question_id>", methods=["GET"])
def delete_checklist_question(question_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    checklist.delete_checklist_question(dbConn, question_id)
    return jsonify({'success': True})


@app.route("/api/checklist/new_from_master/<int:master_id>", methods=["GET"])
def create_checklist_from_master(master_id: int):
    dbConn: DatabaseConnection = get_db().connection
    checklist.create_checklist_from_master(dbConn, master_id)
    return jsonify({'success': True})


@app.route("/api/checklist/answers/<int:checklist_id>", methods=["GET"])
def get_checklist_answers(checklist_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    answers: list[checklist.ChecklistAnswer] = checklist.get_answers_for_checklist(
        dbConn, checklist_id)
    return mk_response([asdict(a) for a in answers])


@app.route("/api/checklist/answer/update/<int:answer_id>", methods=["POST"])
def create_checklist_answer(answer_id: int) -> Response:
    dbConn: DatabaseConnection = get_db().connection
    json: Any | None = request.json
    if json is None:
        return jsonify({'success': False})
    choice: bool = json["choice"]
    question_text: str = json["question_text"]
    checklist_id: int = json["checklist_id"]
    answer: checklist.ChecklistAnswer = checklist.ChecklistAnswer(
        id=answer_id, choice=choice, question_text=question_text, checklist_id=checklist_id)
    checklist.update_checklist_answer(dbConn, answer)
    return jsonify({'success': True})


# endregion Checklist related routes ---

# --- End API Routes ---

# --- Catch-all route for Vue App ---
# This route MUST be defined AFTER all other routes


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_vue_app(path: str) -> Response:
    """Serves the Vue application's index.html or its static assets."""
    logger.debug(f"Catch-all route received path: '{path}'")

    # Construct the full path potential asset path within STATIC_FOLDER
    asset_path: Path = STATIC_FOLDER / path

    # Check if the path points to an existing file within STATIC_FOLDER
    # Important: Use Path object methods for checking existence and type
    if asset_path.is_file():
        logger.debug(
            f"Path points to an existing file. Serving asset: '{path}'")
        # Use send_from_directory with the base STATIC_FOLDER and the relative path
        return send_from_directory(STATIC_FOLDER, path)
    else:
        # If the path doesn't correspond to a file (or it's the root '/'),
        # serve the main index.html file.
        index_html_path: Path = STATIC_FOLDER / 'index.html'
        logger.debug(
            f"Path is not a file or is root. Attempting to serve index.html from: '{index_html_path}'")
        if not index_html_path.is_file():
            logger.error(
                f"CRITICAL: index.html not found at '{index_html_path}'!")
            return Response("Server configuration error: index.html not found.", 500)
        # Use send_from_directory to serve index.html
        return send_from_directory(STATIC_FOLDER, 'index.html')
# --- End Catch-all Route ---


def wants_json_response() -> bool:
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']


def mk_response(data: DBResult | Iterable[Any], heading: str | None = None) -> Response:
    # Check the Accept header
    if wants_json_response():
        # Return the data as JSON
        return jsonify({"success": True, "data": data})
    else:
        if isinstance(data, str):
            # Return the data as HTML
            return make_response(data)
        # will also match DBResult
        elif isinstance(data, Iterable):
            # Return the data as an HTML table
            return make_response(render_template('data_table.html', data=data, heading=heading))
        else:
            raise TypeError(f"Unknown data type: {type(data)}")


if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
    logger.info("Starting server")
    logger.info(f"Serving static files from: {STATIC_FOLDER}")

    # Use host/port from config if available, otherwise default
    server_host: str = config.get("server", {}).get("host", "0.0.0.0")
    server_port: int = config.get("server", {}).get("port", 5000)
    debug_mode: bool = config.get("server", {}).get("debug", False)

    logger.info(
        f"Running Flask app on {server_host}:{server_port} with debug={debug_mode}")
    app.run(host=server_host, port=server_port, debug=debug_mode)
