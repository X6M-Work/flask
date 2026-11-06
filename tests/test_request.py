from __future__ import annotations

from flask import Flask
from flask import Request
from flask import request
from flask.testing import FlaskClient


def test_max_content_length(app: Flask, client: FlaskClient) -> None:
    app.config["MAX_CONTENT_LENGTH"] = 50

    @app.post("/")
    def index():
        request.form["myfile"]
        AssertionError()

    @app.errorhandler(413)
    def catcher(error):
        return "42"

    rv = client.post("/", data={"myfile": "foo" * 50})
    assert rv.data == b"42"


def test_limit_config(app: Flask):
    app.config["MAX_CONTENT_LENGTH"] = 100
    app.config["MAX_FORM_MEMORY_SIZE"] = 50
    app.config["MAX_FORM_PARTS"] = 3
    r = Request({})

    # no app context, use Werkzeug defaults
    assert r.max_content_length is None
    assert r.max_form_memory_size == 500_000
    assert r.max_form_parts == 1_000

    # in app context, use config
    with app.app_context():
        assert r.max_content_length == 100
        assert r.max_form_memory_size == 50
        assert r.max_form_parts == 3

    # regardless of app context, use override
    r.max_content_length = 90
    r.max_form_memory_size = 30
    r.max_form_parts = 4

    assert r.max_content_length == 90
    assert r.max_form_memory_size == 30
    assert r.max_form_parts == 4

    with app.app_context():
        assert r.max_content_length == 90
        assert r.max_form_memory_size == 30
        assert r.max_form_parts == 4

    # can explicitly disable limits by setting to None
    r.max_content_length = None
    r.max_form_memory_size = None
    r.max_form_parts = None

    assert r.max_content_length is None
    assert r.max_form_memory_size is None
    assert r.max_form_parts is None

    with app.app_context():
        assert r.max_content_length is None
        assert r.max_form_memory_size is None
        assert r.max_form_parts is None


def test_trusted_hosts_config(app: Flask) -> None:
    app.config["TRUSTED_HOSTS"] = ["example.test", ".other.test"]

    @app.get("/")
    def index() -> str:
        return ""

    client = app.test_client()
    r = client.get(base_url="http://example.test")
    assert r.status_code == 200
    r = client.get(base_url="http://a.other.test")
    assert r.status_code == 200
    r = client.get(base_url="http://bad.test")
    assert r.status_code == 400


def test_max_content_length_override_none(app: Flask, client: FlaskClient) -> None:
    app.config["MAX_CONTENT_LENGTH"] = 50

    @app.before_request
    def disable_limit() -> None:
        request.max_content_length = None

    @app.post("/")
    def index():
        return request.form["myfile"]

    rv = client.post("/", data={"myfile": "foo" * 50})
    assert rv.status_code == 200
    assert rv.data == b"foo" * 50
