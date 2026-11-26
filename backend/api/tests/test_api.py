from unittest.mock import Mock

import duckdb
import pytest
from anyio import get_cancelled_exc_class
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

from backend.api.app import main
from backend.api.app.core import database as db_module
from backend.api.app.core.config import Settings
from backend.api.app.core.database import get_db, open_database

PROTECTED_PATHS = [
    "/dossiers",
    "/dossiers/D1",
    "/textes",
    "/textes/T1",
    "/articles?dossier_uid=D1",
    "/articles/A1",
    "/amendements?dossier_uid=D1&texte_uid=T1",
    "/amendements/A1",
    "/organes",
    "/organes/types",
    "/organes/O1",
    "/groupes_politiques",
    "/groupes_politiques/G1",
    "/personnes?organe_uid=O1",
    "/personnes/P1",
    "/search?q=loi",
]


@pytest.mark.parametrize("path", PROTECTED_PATHS)
@pytest.mark.parametrize(
    "authorization", [None, "", "Bearer ", "Bearer incorrect", "Basic incorrect"]
)
async def test_business_routes_require_password(client, application, path, authorization):
    database = Mock(side_effect=AssertionError("Aucun accès DB autorisé"))
    application.state.database = database
    client.headers.pop("Authorization")
    if authorization is not None:
        client.headers["Authorization"] = authorization
    response = await client.get("/api/v0" + path)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["type"] == "about:blank"
    assert "?" not in response.json()["instance"]
    assert (await client.get("/health")).status_code == 200
    database.cursor.assert_not_called()


async def test_missing_password_fails_closed():
    app = main.create_app(Settings(_env_file=None, API_PASSWORD=None, DATA_PATH=None))
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for path in PROTECTED_PATHS:
                assert (await client.get("/api/v0" + path)).status_code == 503
            with pytest.raises(HTTPException) as error:
                next(get_db(Request({"type": "http", "app": app})))
            assert error.value.status_code == 503


@pytest.mark.parametrize(
    "query",
    [
        "q=",
        "q=%20",
        "q=x&types=unknown",
        "q=x",
        "q=loi&page=0",
        "q=loi&hits_per_page=101",
        "q=loi&legislature=x",
        "q=loi&semantic_ratio=2",
    ],
)
async def test_search_validation(client, query):
    response = await client.get("/api/v0/search?" + query)
    assert response.status_code == response.json()["status"] == 422
    assert response.headers["content-type"] == "application/problem+json"


async def test_openapi_contract(client):
    spec = (await client.get("/openapi.json")).json()
    for path, methods in spec["paths"].items():
        if path.startswith("/api/v0"):
            operation = methods["get"]
            assert operation["security"] == [{"HTTPBearer": []}]
            assert "application/problem+json" in operation["responses"]["422"]["content"]
            assert "application/json" not in operation["responses"]["422"]["content"]


@pytest.fixture
def data_file(tmp_path):
    path = tmp_path / "clair.duckdb"
    with duckdb.connect(path) as connection:
        connection.execute("CREATE TABLE dossiers AS SELECT 'D1' AS uid")
    return str(path)


def test_open_database_is_read_only(data_file):
    connection = open_database(Settings(_env_file=None, DATA_PATH=data_file))
    try:
        cursor = connection.cursor()
        cursor.execute("USE clair")
        assert cursor.execute("SELECT uid FROM dossiers").fetchall() == [("D1",)]
        with pytest.raises(duckdb.Error, match="read-only"):
            cursor.execute("CREATE TABLE ecriture (a INTEGER)")
        with pytest.raises(duckdb.Error, match="lock"):
            cursor.execute("SET threads = 1")
    finally:
        connection.close()


def test_open_database_s3_secret_is_quoted(monkeypatch):
    connection = Mock()
    monkeypatch.setattr(db_module.duckdb, "connect", Mock(return_value=connection))
    config = Settings(
        _env_file=None,
        DATA_PATH="s3://bucket/o'clair.duckdb",
        S3_ACCESS_KEY_ID="id",
        S3_SECRET_ACCESS_KEY="se'cret",  # pragma: allowlist secret
        S3_ENDPOINT="s3.example.org",
    )
    assert open_database(config) is connection
    statements = [call.args[0] for call in connection.execute.call_args_list]
    assert statements == [
        "CREATE SECRET (TYPE s3, KEY_ID 'id', SECRET 'se''cret', ENDPOINT 's3.example.org')",
        "ATTACH 's3://bucket/o''clair.duckdb' AS clair (READ_ONLY)",
        "SET lock_configuration = true",
    ]
    with pytest.raises(ValueError, match="DATA_PATH"):
        open_database(Settings(_env_file=None, DATA_PATH=None))


def test_open_database_closes_on_failure(monkeypatch):
    connection = Mock()
    connection.execute.side_effect = duckdb.IOException("bucket absent")
    monkeypatch.setattr(db_module.duckdb, "connect", Mock(return_value=connection))
    with pytest.raises(duckdb.IOException):
        open_database(Settings(_env_file=None, DATA_PATH="s3://absent/clair.duckdb"))
    connection.close.assert_called_once()


@pytest.mark.parametrize("failure", ["runtime", "cancelled"])
async def test_lifecycle_and_request_cursors(data_file, failure):
    error_class = get_cancelled_exc_class() if failure == "cancelled" else RuntimeError
    app = main.create_app(Settings(_env_file=None, API_PASSWORD=None, DATA_PATH=data_file))
    with pytest.raises(error_class):
        async with app.router.lifespan_context(app):
            database = app.state.database
            dependency = get_db(Request({"type": "http", "app": app}))
            cursor = next(dependency)
            assert cursor.execute("SELECT current_database()").fetchall() == [("clair",)]
            dependency.close()
            raise error_class("arrêt simulé")
    assert app.state.database is None
    with pytest.raises(duckdb.ConnectionException):
        database.execute("SELECT 1")


def test_storage_failure_becomes_503(seeded_database):
    request = Request({"type": "http", "app": Mock(state=Mock(database=seeded_database))})
    dependency = get_db(request)
    next(dependency)
    with pytest.raises(HTTPException) as error:
        dependency.throw(duckdb.HTTPException("S3 indisponible"))
    assert error.value.status_code == 503
