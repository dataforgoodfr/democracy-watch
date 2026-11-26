from unittest.mock import AsyncMock, Mock

import pytest
from anyio import get_cancelled_exc_class, sleep
from asyncer import create_task_group
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

from backend.api.app import main
from backend.api.app.core.config import Settings
from backend.api.app.core.database import get_db

PROTECTED_PATHS = [
    "/dossiers",
    "/dossiers/D1",
    "/amendements",
    "/amendements/A1",
    "/textes",
    "/articles",
    "/articles/A1",
    "/parlementaires",
    "/parlementaires/P1",
    "/groupes_politiques",
    "/groupes_politiques/G1",
    "/declarations_hatvp",
    "/declarations_hatvp/H1",
    "/search?q=loi",
]


@pytest.mark.parametrize("path", PROTECTED_PATHS)
@pytest.mark.parametrize(
    "authorization", [None, "", "Bearer ", "Bearer incorrect", "Basic incorrect"]
)
async def test_business_routes_require_password(client, db_session, path, authorization):
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
    db_session.execute.assert_not_awaited()


async def test_missing_password_fails_closed():
    app = main.create_app(Settings(_env_file=None, API_PASSWORD=None, DATABASE_URL=None))
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for path in PROTECTED_PATHS:
                assert (await client.get("/api/v0" + path)).status_code == 503
            with pytest.raises(HTTPException) as error:
                await anext(get_db(Request({"type": "http", "app": app})))
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


@pytest.mark.parametrize("failure", ["runtime", "cancelled", "startup"])
async def test_lifecycle_and_request_sessions(monkeypatch, failure):
    error_class = get_cancelled_exc_class() if failure == "cancelled" else RuntimeError
    engine = Mock(dispose=AsyncMock())
    context = AsyncMock()
    factory = Mock(return_value=context)
    build_engine = Mock(return_value=engine)
    build_sessions = Mock(return_value=factory)
    connection = object()
    connector = AsyncMock(return_value=connection)
    monkeypatch.setattr(main, "connect_async", connector)
    if failure == "startup":
        build_sessions.side_effect = RuntimeError("démarrage partiel")
    monkeypatch.setattr(main, "create_async_engine", build_engine)
    monkeypatch.setattr(main, "async_sessionmaker", build_sessions)
    config = Settings(
        _env_file=None,
        API_PASSWORD=None,
        DATABASE_URL="postgresql+asyncpg://unused",
        DATABASE_POOL_SIZE=2,
        DATABASE_POOL_TIMEOUT=3,
        DATABASE_TIMEOUT=4,
    )
    app = main.create_app(config)
    other = main.create_app(Settings(_env_file=None, API_PASSWORD=None, DATABASE_URL=None))
    assert other.state.settings.DATABASE_URL is None
    build_engine.assert_not_called()
    with pytest.raises(error_class):
        async with app.router.lifespan_context(app):
            dependency = get_db(Request({"type": "http", "app": app}))
            assert await anext(dependency) is context.__aenter__.return_value
            await dependency.aclose()
            context.__aexit__.assert_awaited_once()
            raise error_class("arrêt simulé")
    build_engine.assert_called_once()
    assert build_engine.call_args.args == ("postgresql+asyncpg://",)
    options = dict(build_engine.call_args.kwargs)
    creator = options.pop("async_creator")
    assert options == {
        "pool_size": 2,
        "max_overflow": 0,
        "pool_timeout": 3,
        "pool_pre_ping": True,
    }
    connector.assert_not_awaited()
    assert await creator() is connection
    connector.assert_awaited_once_with(
        dsn=config.DATABASE_URL,
        read_only=True,
        timeout=4,
        command_timeout=4,
    )
    engine.dispose.assert_awaited_once()
    assert app.state.session_factory is None
    async with other.router.lifespan_context(other):
        assert other.state.session_factory is None
    build_engine.assert_called_once()


async def test_engine_disposal_survives_cancellation(monkeypatch):
    completed = []

    async def dispose():
        await sleep(0)
        completed.append(True)

    engine = Mock(dispose=AsyncMock(side_effect=dispose))
    monkeypatch.setattr(main, "create_async_engine", Mock(return_value=engine))
    monkeypatch.setattr(main, "async_sessionmaker", Mock())
    app = main.create_app(
        Settings(_env_file=None, API_PASSWORD=None, DATABASE_URL="postgresql+asyncpg://unused")
    )
    async with create_task_group() as group:
        async with app.router.lifespan_context(app):
            group.cancel_scope.cancel()
    assert completed == [True]
    engine.dispose.assert_awaited_once()
    assert app.state.session_factory is None
