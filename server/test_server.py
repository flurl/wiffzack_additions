# type: ignore
import types
from unittest.mock import MagicMock, patch, ANY
import pathlib
from pathlib import Path
import io
import json as pyjson

from flask import Flask, Response
import pytest

import server
from lib import messages, checklist

# Test mk_response returns JSON when Accept header is application/json


def test_mk_response_json():
    app = Flask(__name__)
    with app.test_request_context(headers={"Accept": "application/json"}):
        resp = server.mk_response([1, 2, 3])
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"] == [1, 2, 3]


def test_wants_json_response_json():
    app = Flask(__name__)
    with app.test_request_context(headers={"Accept": "application/json"}):
        assert server.wants_json_response() is True


def test_wants_json_response_html():
    app = Flask(__name__)
    with app.test_request_context(headers={"Accept": "text/html"}):
        assert server.wants_json_response() is False


def test_serve_vue_app_index(monkeypatch):
    app = server.app
    monkeypatch.setattr(server, "STATIC_FOLDER", pathlib.Path(app.root_path))
    # Use Flask's Response object for a valid response
    monkeypatch.setattr(server, "send_from_directory", lambda folder, filename: Response(
        "<html>dummy index</html>", status=200, mimetype="text/html"))
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    with app.test_client() as client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.is_json is False
        assert b"dummy index" in resp.data


def test_api_jotd(monkeypatch):
    app = server.app
    # Patch Path.is_file to always return True
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    # Patch open to return a fake file object
    fake_jokes = [
        {"id": 1, "body": "Why did the chicken cross the road? To get to the other side!"}]
    fake_file = io.StringIO(pyjson.dumps(fake_jokes))
    monkeypatch.setattr("builtins.open", lambda *a, **kw: fake_file)
    # Patch json.load to load from our fake file
    monkeypatch.setattr(pyjson, "load", lambda f: fake_jokes)
    with app.test_client() as client:
        resp = client.get("/api/jotd")
        assert resp.status_code == 200
        assert resp.is_json
        assert b"chicken cross the road" in resp.data


def test_api_alarm_trigger_success(monkeypatch):
    app = server.app
    # Patch config to provide a known alarm URL template
    server.config["alarm"] = {"url": "http://dummy/alarm/{location}"}

    # Patch urllib.request.urlopen to simulate a successful response
    class DummyResponse:
        def __init__(self):
            self.status = 200

        def read(self):
            return b"OK"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("urllib.request.urlopen",
                        lambda url, timeout=10: DummyResponse())
    with app.test_client() as client:
        resp = client.get("/api/alarm/trigger/testlocation")
        assert resp.status_code == 200
        assert resp.is_json
        assert b"Alarm triggered successfully" in resp.data


def test_api_restart_success(monkeypatch):
    app = server.app
    # Patch Path.touch to do nothing
    monkeypatch.setattr(Path, "touch", lambda self: None)
    with app.test_client() as client:
        resp = client.get("/api/restart")
        assert resp.status_code == 200
        assert resp.is_json
        assert b"Server restart signaled" in resp.data


def test_api_recipe_list(monkeypatch):
    app = server.app
    # Create a mock database object with a get_receipes method

    class MockDB:
        def get_receipes(self):
            return [
                ("Pizza", 2, "Cheese", "kg"),
                ("Pizza", 1, "Tomato", "kg"),
            ]
    # Patch get_db to return our mock database
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        resp = client.get("/api/recipe/list")
        assert resp.status_code == 200
        assert resp.is_json
        assert b"Pizza" in resp.data
        assert b"Cheese" in resp.data
        assert b"Tomato" in resp.data


def test_api_get_messages(monkeypatch):
    app = server.app
    # Patch messages.get_messages_list to return a dummy list of messages
    monkeypatch.setattr(
        server.messages, "get_messages_list", lambda: [
            messages.Message(path="foo", name="bar",
                             type="txt", content="hello"),
            messages.Message(path="bob", name="alice", type="txt",
                             content="hello from bob to alice")
        ])
    with app.test_client() as client:
        resp = client.get("/api/message/list")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) >= 2
        paths = [msg["path"] for msg in data["messages"]]
        assert "foo" in paths
        assert "bob" in paths


def test_api_send_message(monkeypatch):
    app = server.app
    monkeypatch.setattr(server.messages, "get_message",
                        lambda path: messages.Message(path="foo", name="bar", type="txt", content="hello"))
    with app.test_client() as client:
        resp = client.get("/api/message/foo")
        assert resp.status_code == 200
        assert resp.is_json
        assert b"foo" in resp.data
        assert b"bar" in resp.data
        assert b"txt" in resp.data
        assert b"hello" in resp.data


def test_api_send_html_message(monkeypatch):
    app = server.app
    # Patch messages.get_message to return a dummy HTML message
    monkeypatch.setattr(server.messages, "get_message",
                        lambda path: messages.Message(path="foo", name="bar", type="html", content="<h1>hello</h1>"))
    # Patch send_from_directory to return a dummy HTML response
    monkeypatch.setattr(server, "send_from_directory", lambda folder, filename: Response(
        "<h1>hello</h1>", status=200, mimetype="text/html"))
    with app.test_client() as client:
        resp = client.get("/message/html/foo/")
        assert resp.status_code == 200
        assert resp.is_json is False
        assert b"<h1>hello</h1>" in resp.data


def test_api_get_invoice_type(monkeypatch):
    app = server.app
    # Create a mock database object with a get_invoice_type method

    class MockDB:
        def get_invoice_type(self, id=None):
            return [
                (1, "A", "Barverkauf", 100, True, False, 10, True),
                (2, "B", "Rechnung", 200, False, True, 20, False),
            ]
    # Patch get_db to return our mock database
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        resp = client.get("/api/invoice_type")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2
        ids = [row[0] for row in data["data"]]
        assert 1 in ids
        assert 2 in ids


def test_api_get_invoice_html(monkeypatch):
    app = server.app
    # Patch subprocess.Popen to simulate print_service.py output

    class DummyProcess:
        def __init__(self):
            self.returncode = 0

        def communicate(self, input=None, timeout=None):
            return ("<html><body>Invoice 123</body></html>", "")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    monkeypatch.setattr("subprocess.Popen", lambda *a, **kw: DummyProcess())
    with app.test_client() as client:
        resp = client.get("/api/invoice/html/123",
                          headers={"Accept": "text/html"})
        assert resp.status_code == 200
        print(resp.data)
        assert resp.is_json is False
        assert resp.mimetype == "text/html"
        assert b"<html><body>Invoice 123</body></html>" in resp.data


def test_api_print_invoice(monkeypatch):
    app = server.app
    # Patch subprocess.Popen to simulate print_service.py process

    class DummyProcess:
        def __init__(self):
            self.stdin = io.StringIO()
            self.returncode = 0

        def communicate(self, input=None, timeout=None):
            return ("", "")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    monkeypatch.setattr("subprocess.Popen", lambda *a, **kw: DummyProcess())
    with app.test_client() as client:
        resp = client.get("/api/invoice/print/123")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert "Print job dispatched" in data["message"]


def test_api_get_invoice_list(monkeypatch):
    app = server.app
    # Mock DB with get_invoice_list method

    class MockDB:
        def get_invoice_list(self, waiter=None, invoice_type=None):
            if waiter == "bob":
                return [
                    (2, "B200", "2024-01-02T13:00:00", "T2", "bob")
                ]
            return [
                (1, "A100", "2024-01-01T12:00:00", "T1", "alice"),
                (2, "B200", "2024-01-02T13:00:00", "T2", "bob"),
            ]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        # Test all invoices
        resp = client.get("/api/invoice/list")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert any(row[4] == "alice" for row in data["data"])
        assert any(row[4] == "bob" for row in data["data"])
        # Test filtered by waiter
        resp2 = client.get("/api/invoice/list/bob")
        assert resp2.status_code == 200
        assert resp2.is_json
        data2 = resp2.get_json()
        assert data2["success"] is True
        assert len(data2["data"]) == 1
        assert data2["data"] == [
            [2, "B200", "2024-01-02T13:00:00", "T2", "bob"]]
        # TODO: Test filtered by invoice type. Therefore the it's necessary that the query returns the invoice_type too


def test_api_set_init_inventory(monkeypatch):
    app = server.app
    # Mock DB

    class MockDB:
        def get_storage_name(self, storage_id):
            return [("TestStorage",)]

        def get_article(self, id):
            return [(id, f"Article{id}")]

        def update_storage(self, sm, absolute=False):
            # Just record the call for assertion if needed
            self.last_update = (sm, absolute)
    mock_db = MockDB()
    monkeypatch.setattr(server, "get_db", lambda: mock_db)
    # Patch config
    server.config["server"] = {"init_stock_directory": ""}
    # Patch open to simulate CSV file
    fake_csv = io.StringIO("article_id;amount\n1;10\n2;20\n")
    monkeypatch.setattr("builtins.open", lambda *a, **kw: fake_csv)
    # Patch csv.DictReader to read from our fake file
    orig_dict_reader = __import__("csv").DictReader

    def fake_dict_reader(file, delimiter=None):
        return orig_dict_reader(file, delimiter=delimiter)
    monkeypatch.setattr(server.csv, "DictReader", fake_dict_reader)
    with app.test_client() as client:
        resp = client.get("/api/set_init_inventory/storage/42")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True


def test_api_get_config(monkeypatch):
    app = server.app
    # Patch config to provide terminal_config
    server.config["terminal_config"] = {
        "foo": {"setting": 1},
        "bar": {"setting": 2}
    }
    with app.test_client() as client:
        # Test without terminal_id
        resp = client.get("/api/get_config")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert data["config"] == server.config["terminal_config"]
        # Test with terminal_id
        resp2 = client.get("/api/get_config/foo")
        assert resp2.status_code == 200
        assert resp2.is_json
        data2 = resp2.get_json()
        assert data2["success"] is True
        assert data2["config"] == {"setting": 1}
        # Test with missing terminal_id
        resp3 = client.get("/api/get_config/doesnotexist")
        assert resp3.status_code == 200
        assert resp3.is_json
        data3 = resp3.get_json()
        assert data3["success"] is False


def test_api_get_storage_name(monkeypatch):
    app = server.app
    # Mock DB with get_storage_name method

    class MockDB:
        def get_storage_name(self, storage_id):
            return [("TestStorage",)]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        resp = client.get("/api/get_storage_name/42")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        # Should match the mock return value
        assert data["data"] == [["TestStorage"]]


def test_api_get_articles_in_storage(monkeypatch):
    app = server.app
    # Mock DB with get_articles_in_storage method

    class MockDB:
        def get_articles_in_storage(self, storage_id, article_group_id=None, show_not_in_stock=False):
            # Return different data based on params for coverage
            if article_group_id is not None:
                return [(1, "Beer", 10.0), (2, "Wine", 5.0)]
            if show_not_in_stock:
                return [(3, "Juice", 0.0)]
            return [(1, "Beer", 10.0), (2, "Wine", 5.0), (3, "Juice", 0.0)]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        # Basic call
        resp = client.get("/api/get_articles_in_storage/42")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert any(row[1] == "Beer" for row in data["data"])
        # With article_group_id
        resp2 = client.get("/api/get_articles_in_storage/42/article_group/7")
        assert resp2.status_code == 200
        assert resp2.is_json
        data2 = resp2.get_json()
        assert data2["success"] is True
        assert any(row[1] == "Wine" for row in data2["data"])
        assert any(row[1] == "Beer" for row in data2["data"])
        assert not any(row[1] == "Juice" for row in data2["data"])
        # With show_not_in_stock
        resp3 = client.get(
            "/api/get_articles_in_storage/42?show_not_in_stock=1")
        assert resp3.status_code == 200
        assert resp3.is_json
        data3 = resp3.get_json()
        assert data3["success"] is True
        assert any(row[1] == "Juice" for row in data3["data"])


def test_api_empty_storage(monkeypatch):
    app = server.app
    called = {}

    class MockDB:
        def empty_storage(self, storage_id):
            called["storage_id"] = storage_id
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        resp = client.get("/api/empty_storage/99")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert called["storage_id"] == 99


def test_api_update_storage(monkeypatch):
    app = server.app
    called = {"add": [], "withdraw": []}

    class MockDB:
        def get_storage_name(self, storage_id):
            return [(f"Storage{storage_id}",)]

        def add_article_to_storage(self, sm, absolute=False):
            called["add"].append((sm, absolute))

        def withdraw_article_from_storage(self, sm, absolute=False):
            called["withdraw"].append((sm, absolute))
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    # Minimal valid article dict
    articles = {
        "a": {"id": 1, "name": "Beer", "amount": 5},
        "b": {"id": 2, "name": "Wine", "amount": 3}
    }
    with app.test_client() as client:
        # Test 'to' route
        resp = client.post("/api/update_storage/to/10", json=articles)
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert len(called["add"]) == 2
        # Test 'from' route
        called["add"].clear()
        called["withdraw"].clear()
        resp2 = client.post("/api/update_storage/from/20", json=articles)
        assert resp2.status_code == 200
        assert resp2.is_json
        data2 = resp2.get_json()
        assert data2["success"] is True
        assert len(called["withdraw"]) == 2
        # Test 'from/to' route with absolute
        called["add"].clear()
        called["withdraw"].clear()
        resp3 = client.post(
            "/api/update_storage/from/20/to/10?method=absolute", json=articles)
        assert resp3.status_code == 200
        assert resp3.is_json
        data3 = resp3.get_json()
        assert data3["success"] is True
        assert len(called["add"]) == 2
        assert len(called["withdraw"]) == 2
        # Test missing articles (should fail)
        resp4 = client.post("/api/update_storage/to/10", json={})
        assert resp4.status_code == 200
        assert resp4.is_json
        data4 = resp4.get_json()
        assert data4["success"] is False
        resp5 = client.post("/api/update_storage/to/10", json=None)
        # Unsupported Media Type because server refuses to accept
        # the request because the payload format is in an unsupported format.
        assert resp5.status_code == 415


def test_api_get_article_by_group(monkeypatch):
    app = server.app

    class MockDB:
        def get_storage_articles_by_group(self, group):
            return [(1, "Beer"), (2, "Wine")]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        resp = client.get("/api/storage_article_by_group/5")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert any(row[1] == "Beer" for row in data["data"])
        assert any(row[1] == "Wine" for row in data["data"])


def test_api_get_storage_article_groups(monkeypatch):
    app = server.app

    class MockDB:
        def get_all_storage_article_groups(self):
            return [(1, "Drinks"), (2, "Snacks")]

        def get_article_groups_in_storage(self, storage_id):
            return [(3, "Specials")]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        # No storage_id
        resp = client.get("/api/storage_article_groups")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert any(row[1] == "Drinks" for row in data["data"])
        assert any(row[1] == "Snacks" for row in data["data"])
        # With storage_id
        resp2 = client.get("/api/storage_article_groups/42")
        assert resp2.status_code == 200
        assert resp2.is_json
        data2 = resp2.get_json()
        assert data2["success"] is True
        assert any(row[1] == "Specials" for row in data2["data"])


def test_api_get_article(monkeypatch):
    app = server.app

    class MockDB:
        def get_article(self, article_id=None):
            if article_id is None:
                return [(1, "Beer"), (2, "Wine")]
            return [(article_id, f"Article{article_id}")]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        # All articles
        resp = client.get("/api/articles")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert any(row[1] == "Beer" for row in data["data"])
        # Single article
        resp2 = client.get("/api/articles/7")
        assert resp2.status_code == 200
        assert resp2.is_json
        data2 = resp2.get_json()
        assert data2["success"] is True
        assert data2["data"] == [[7, "Article7"]]


def test_api_get_articles(monkeypatch):
    app = server.app

    class MockDB:
        def execute_query(self, query, params=()):
            return [(1, "Beer", 2.5), (2, "Wine", 3.0)]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        resp = client.get("/api/artikel")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert any(row[1] == "Beer" for row in data["data"])
        assert any(row[2] == 3.0 for row in data["data"])


def test_api_get_wardrobe_sales(monkeypatch):
    app = server.app

    class MockDB:
        def get_wardrobe_sales(self):
            return [("waiter1", "A-1", 10.0, False)]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        resp = client.get("/api/wardrobe_sales")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"] == [["waiter1", "A-1", 10.0, False]]


def test_api_get_latest_tallied_articles(monkeypatch):
    app = server.app

    class MockDB:
        def get_latest_tallied_articles(self, client):
            return [("waiter1", 2, "Beer"), ("waiter2", 1, "Wine")]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        resp = client.get("/api/waiter/latest_tallied_articles")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert any(row[2] == "Beer" for row in data["data"])


def test_api_get_tallied_articles(monkeypatch):
    app = server.app

    class MockDB:
        def get_tallied_articles(self, client):
            return [(3, "Beer"), (1, "Wine")]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        resp = client.get("/api/waiter/tallied_articles")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert any(row[1] == "Beer" for row in data["data"])


def test_api_get_sales(monkeypatch):
    app = server.app

    class MockDB:
        def get_client_sales(self, client):
            return [(client, 123.45)]
    monkeypatch.setattr(server, "get_db", lambda: MockDB())
    with app.test_client() as client:
        resp = client.get("/api/waiter/sales")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"] == [["waiter", 123.45]]


def test_get_db_creates_and_reuses_db(monkeypatch):
    app = server.app
    # Patch Database and connect_to_database
    mock_db_instance = MagicMock()
    mock_connect = MagicMock()
    monkeypatch.setattr(server, "Database", lambda: mock_db_instance)
    mock_db_instance.connect_to_database = mock_connect
    # Patch config to have all keys
    monkeypatch.setattr(server, "config", {
        "database": {
            "server": "s", "username": "u", "password": "p", "database": "d"
        }
    })
    with app.app_context():
        # Should create and connect
        db1 = server.get_db()
        assert db1 is mock_db_instance
        mock_connect.assert_called_once()
        # Should reuse the same db
        db2 = server.get_db()
        assert db2 is db1
        # connect_to_database should not be called again
        assert mock_connect.call_count == 1


def test_get_db_missing_config(monkeypatch):
    app = server.app
    # Patch Database
    monkeypatch.setattr(server, "Database", lambda: MagicMock())
    # Patch config to be missing a key
    monkeypatch.setattr(server, "config", {"database": {"server": "s"}})
    with app.app_context():
        with pytest.raises(KeyError):
            server.get_db()


def test_get_db_connect_exception(monkeypatch):
    app = server.app
    # Patch Database
    mock_db_instance = MagicMock()

    def fail_connect(*a, **kw):
        raise RuntimeError("fail connect")
    mock_db_instance.connect_to_database = fail_connect
    monkeypatch.setattr(server, "Database", lambda: mock_db_instance)
    monkeypatch.setattr(server, "config", {
        "database": {
            "server": "s", "username": "u", "password": "p", "database": "d"
        }
    })
    with app.app_context():
        with pytest.raises(RuntimeError):
            server.get_db()


def test_teardown_db_closes(monkeypatch):
    app = server.app
    mock_db = MagicMock()
    with app.app_context():
        from flask import g
        g.db = mock_db
        server.teardown_db(None)
        mock_db.close.assert_called_once()
        # g.db should be removed
        assert "db" not in g


def test_teardown_db_no_db():
    app = server.app
    with app.app_context():
        from flask import g
        # No db in g
        server.teardown_db(None)  # Should not raise


# region Checklist Tests

@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_get_checklist_masters(monkeypatch):
    app = server.app
    mock_masters = [
        checklist.ChecklistMaster(id=1, name="Morning", category="Daily"),
        checklist.ChecklistMaster(id=2, name="Evening", category="Daily")
    ]
    monkeypatch.setattr(
        server.checklist, "get_all_checklist_masters", lambda db: mock_masters)
    with app.test_client() as client:
        resp = client.get("/api/checklist/master/list")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]['name'] == "Morning"


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_create_checklist_master(monkeypatch):
    app = server.app
    mock_master = checklist.ChecklistMaster(id=3, name="New", category="Test")
    monkeypatch.setattr(
        server.checklist, "create_checklist_master", lambda db, name, cat: mock_master)
    with app.test_client() as client:
        resp = client.post("/api/checklist/master/new",
                           json={"name": "New", "category": "Test"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == 3
        assert data["data"]["name"] == "New"


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_update_checklist_master(monkeypatch):
    app = server.app
    # The function doesn't return anything, so we just need to check it's called
    mock_update = MagicMock()
    monkeypatch.setattr(
        server.checklist, "update_checklist_master", mock_update)
    with app.test_client() as client:
        resp = client.post("/api/checklist/master/update/1",
                           json={"name": "Updated", "category": "Daily"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        mock_update.assert_called_once()
        # Check that the arguments passed to the mock are correct
        call_args = mock_update.call_args[0]
        assert isinstance(call_args[1], checklist.ChecklistMaster)
        assert call_args[1].id == 1
        assert call_args[1].name == "Updated"


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_delete_checklist_master(monkeypatch):
    app = server.app
    mock_delete = MagicMock()
    monkeypatch.setattr(
        server.checklist, "delete_checklist_master", mock_delete)
    with app.test_client() as client:
        resp = client.get("/api/checklist/master/delete/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        mock_delete.assert_called_once_with(ANY, 1)


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_get_questions_for_master(monkeypatch):
    app = server.app
    mock_questions = [
        checklist.ChecklistQuestion(id=1, text="Q1", order=1, master_id=1),
        checklist.ChecklistQuestion(id=2, text="Q2", order=2, master_id=1)
    ]
    monkeypatch.setattr(server.checklist, "get_questions_for_master",
                        lambda db, master_id: mock_questions)
    with app.test_client() as client:
        resp = client.get("/api/checklist/master/1/questions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]['text'] == "Q1"


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_update_checklist_question(monkeypatch):
    app = server.app
    mock_update = MagicMock()
    monkeypatch.setattr(
        server.checklist, "update_checklist_question", mock_update)
    with app.test_client() as client:
        question_data = {"text": "Updated Q", "order": 1, "master_id": 1}
        resp = client.post(
            "/api/checklist/question/update/1", json=question_data)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        mock_update.assert_called_once()
        call_args = mock_update.call_args[0]
        assert isinstance(call_args[1], checklist.ChecklistQuestion)
        assert call_args[1].id == 1
        assert call_args[1].text == "Updated Q"


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_create_checklist_from_master(monkeypatch):
    app = server.app
    mock_create = MagicMock()
    monkeypatch.setattr(
        server.checklist, "create_checklist_from_master", mock_create)
    with app.test_client() as client:
        resp = client.get("/api/checklist/new_from_master/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        mock_create.assert_called_once_with(ANY, 1)


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_get_latest_checklist(monkeypatch):
    app = server.app
    mock_checklist = checklist.Checklist(
        id=1, datum=None, completed=False, master_name="Morning")
    monkeypatch.setattr(server.checklist, "get_latest_checklist",
                        lambda db, master_id, expiry, closed: mock_checklist)
    with app.test_client() as client:
        resp = client.get("/api/checklist/latest/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == 1
        assert data["data"]["master_name"] == "Morning"


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_get_latest_checklist_none(monkeypatch):
    app = server.app
    monkeypatch.setattr(
        server.checklist, "get_latest_checklist", lambda db, master_id, expiry, closed: None)
    with app.test_client() as client:
        resp = client.get("/api/checklist/latest/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is False


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_get_checklist_answers(monkeypatch):
    app = server.app
    mock_answers = [
        checklist.ChecklistAnswer(
            id=1, checklist_id=1, question_text="Q1", choice=True),
        checklist.ChecklistAnswer(
            id=2, checklist_id=1, question_text="Q2", choice=None)
    ]
    monkeypatch.setattr(
        server.checklist, "get_answers_for_checklist", lambda db, chk_id: mock_answers)
    with app.test_client() as client:
        resp = client.get("/api/checklist/answers/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["choice"] is True
        assert data["data"][1]["choice"] is None


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_update_checklist_answer(monkeypatch):
    app = server.app
    mock_update = MagicMock()
    monkeypatch.setattr(
        server.checklist, "update_checklist_answer", mock_update)
    with app.test_client() as client:
        answer_data = {"choice": False,
                       "question_text": "Q1", "checklist_id": 1}
        resp = client.post("/api/checklist/answer/update/1", json=answer_data)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        mock_update.assert_called_once()
        call_args = mock_update.call_args[0]
        assert isinstance(call_args[1], checklist.ChecklistAnswer)
        assert call_args[1].id == 1
        assert call_args[1].choice is False


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_close_checklist(monkeypatch):
    app = server.app
    mock_close = MagicMock()
    monkeypatch.setattr(server.checklist, "close_checklist", mock_close)
    with app.test_client() as client:
        resp = client.get("/api/checklist/close/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        mock_close.assert_called_once_with(ANY, 1)


@pytest.fixture()
def mock_db_for_checklist_tests(monkeypatch):
    """
    Automatically mock get_db for all checklist tests to avoid real DB connection.
    The mock DB object has a `connection` attribute which is also a mock,
    so `get_db().connection` works as expected in the route handlers.
    """
    mock_db_instance = MagicMock()
    mock_db_instance.connection = MagicMock()
    monkeypatch.setattr(server, "get_db", lambda: mock_db_instance)


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_get_checklist_history(monkeypatch):
    app = server.app
    mock_history = [
        checklist.Checklist(id=1, datum="2023-01-01T10:00:00",
                            completed=True, master_name="Daily Morning"),
        checklist.Checklist(id=2, datum="2023-01-02T10:00:00",
                            completed=False, master_name="Daily Morning")
    ]
    monkeypatch.setattr(
        server.checklist, "get_checklist_history", lambda db, master_id: mock_history)
    with app.test_client() as client:
        resp = client.get("/api/checklist/history/123")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == 1
        assert data["data"][0]["master_name"] == "Daily Morning"
        assert data["data"][1]["id"] == 2
        assert data["data"][1]["completed"] is False

# endregion Checklist Tests


@pytest.mark.usefixtures("mock_db_for_checklist_tests")
def test_api_get_latest_by_category_succeeds_if_one_is_closed(monkeypatch):
    """
    Tests that the endpoint returns success: true if at least one checklist
    for a category has been closed, and success: false if none are closed.
    """
    app = server.app

    # 1. Simulate that NO checklists have been recently closed.
    monkeypatch.setattr(
        server.checklist, "get_latest_closed_checklists_by_category", lambda db, cat, exp: [])

    with app.test_client() as client:
        # The API should report failure because no checklists are closed.
        resp = client.get("/api/checklist/latest/by_category/bar")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is False

        # 2. Now, simulate that AT LEAST ONE checklist is closed.
        mock_closed_checklists = [
            checklist.Checklist(id=101, datum=None,
                                completed=True, master_name="Morning")
        ]
        monkeypatch.setattr(
            server.checklist, "get_latest_closed_checklists_by_category", lambda db, cat, exp: mock_closed_checklists)

        resp2 = client.get("/api/checklist/latest/by_category/bar")
        data2 = resp2.get_json()
        assert data2["success"] is True
        assert len(data2["data"]) == 1
