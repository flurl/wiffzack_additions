#!/usr/bin/env python3

import logging
from typing import Any, LiteralString
import tomllib
import csv

from flask import Flask, jsonify, make_response, render_template, request
from flask_cors import CORS
from werkzeug.wrappers import Response

import wiffzack as wz
from wiffzack.types import Article, StorageModifier, DBResult

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s - %(filename)s:%(lineno)d %(funcName)s: %(message)s")


with open("config.toml", "rb") as f:
    config: dict[str, Any] = tomllib.load(f)


wz.db.connect_to_database(config["database"]["server"],
                          config["database"]["username"],
                          config["database"]["password"],
                          config["database"]["database"])


app = Flask(__name__)
# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})


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

    result: DBResult = wz.db.get_client_sales(client)
    return mk_response(result, "sales")


@app.route('/api/<string:client>/tallied_articles', methods=['GET'])
def get_tallied_articles(client: str) -> Response:
    return mk_response(wz.db.get_tallied_articles(client), "Tallied articles")


@app.route('/api/<string:client>/latest_tallied_articles', methods=['GET'])
def get_latest_tallied_articles(client: str) -> Response:
    return mk_response(wz.db.get_latest_tallied_articles(client), "Latest")


@app.route('/api/wardrobe_sales', methods=['GET'])
def get_wardrobe_sales() -> Response:
    result: DBResult = wz.db.get_wardrobe_sales()
    return mk_response(result, "Wardrobe Sales")


@app.route('/api/artikel', methods=['GET'])
def get_articles() -> Response:
    query: LiteralString = f"""
    select artikel_id, artikel_bezeichnung, artikel_ep from artikel_basis
    """
    rows: DBResult = wz.db.execute_query(query)
    return mk_response(rows)


@app.route('/api/storage_article_groups', methods=['GET'])
@app.route('/api/storage_article_groups/<int:storage_id>', methods=['GET'])
def get_storage_article_groups(storage_id: int | None = None) -> Response:
    if storage_id is None:
        result: DBResult = wz.db.get_all_storage_article_groups()
    else:
        result: DBResult = wz.db.get_article_groups_in_storage(storage_id)
    return mk_response(result)


@app.route('/api/storage_article_by_group/<int:group>', methods=['GET'])
def get_article_by_group(group: int) -> Response:
    result: DBResult = wz.db.get_storage_articles_by_group(group)
    return mk_response(result)


@app.route("/api/update_storage/to/<int:to_storage_id>", methods=["POST"])
@app.route("/api/update_storage/from/<int:from_storage_id>", methods=["POST"])
@app.route('/api/update_storage/from/<int:from_storage_id>/to/<int:to_storage_id>', methods=['POST'])
def update_storage(to_storage_id: int | None = None, from_storage_id: int | None = None) -> Response:
    articles: Any | None = request.json
    absolute: bool = True if request.args.get(
        "method") == "absolute" else False
    logging.debug(f"Moving from {from_storage_id} to {to_storage_id}")
    logging.debug(articles)
    if articles is None:
        return jsonify({'success': False})

    if from_storage_id is not None:
        try:
            for article in articles.values():
                logging.debug("from", article)
                sm: StorageModifier = StorageModifier(article=Article(article["id"], article["name"]),
                                                      storage_id=from_storage_id,
                                                      amount=article["amount"])
                wz.db.withdraw_article_from_storage(sm, absolute=absolute)
        except Exception as e:
            print(repr(e))
            return jsonify({'success': False})

    if to_storage_id is not None:
        try:
            for article in articles.values():
                logging.debug("to", article)
                sm: StorageModifier = StorageModifier(article=Article(article["id"], article["name"]),
                                                      storage_id=to_storage_id,
                                                      amount=article["amount"])
                wz.db.add_article_to_storage(sm, absolute=absolute)
        except Exception as e:
            print(e)
            return jsonify({'success': False})

    return jsonify({'success': True})


@app.route("/api/get_articles_in_storage/<int:storage_id>", methods=["GET"])
@app.route("/api/get_articles_in_storage/<int:storage_id>/article_group/<int:article_group_id>", methods=["GET"])
def get_articles_in_storage(storage_id: int, article_group_id: int | None = None) -> Response:
    logging.debug(storage_id)
    result: DBResult = wz.db.get_articles_in_storage(
        storage_id, article_group_id)
    logging.debug(result)
    return mk_response(result)


@app.route("/api/get_storage_name/<int:storage_id>", methods=["GET"])
def get_storage_name(storage_id: int) -> Response:
    result: DBResult = wz.db.get_storage_name(storage_id)
    logging.debug(result)
    return mk_response(result)


@app.route("/api/get_config/<string:terminal_id>", methods=["GET"])
def get_config(terminal_id: str) -> Response:
    logging.debug(config)
    try:
        return jsonify({'success': True, 'config': config["terminal_config"][terminal_id]})
    except KeyError:
        return jsonify({'success': False})


@app.route("/api/set_init_inventory/storage/<int:storage_id>", methods=["GET"])
def set_init_inventory(storage_id: int) -> Response:
    result: DBResult = wz.db.get_storage_name(storage_id)
    assert result is not None
    storage_name: str = result[0][0]
        
    filename: str = f"{config['server']['init_stock_directory']}{storage_name}.csv"

    try:
        with open(filename, mode ='r') as file:
            csvFile = csv.DictReader(file, delimiter=';')
            for line in csvFile:
                    id:int = int(line["article_id"])
                    amount:int = int(line["amount"])
                    sm:StorageModifier = StorageModifier( article=Article(id, ""),
                                            storage_id=storage_id,
                                            amount=amount)
                    try:
                        wz.db.update_storage(sm, absolute=True)
                    except Exception as e:
                        print(e)
                        return jsonify({'success': False})
    except FileNotFoundError as e:
        print(e)
        return jsonify({'success': False})
                
    return jsonify({'success': True})


def wants_json_response() -> bool:
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']


def mk_response(data: DBResult, heading: str|None = None) -> Response:
    print(heading)
    # Check the Accept header
    if wants_json_response():
        # Return the data as JSON
        return jsonify(data)
    else:
        # Return the data as an HTML table
        return make_response(render_template('data_table.html', data=data, heading=heading))


if __name__ == '__main__':
    app.run(debug=True)
