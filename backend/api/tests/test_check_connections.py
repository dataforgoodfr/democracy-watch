from secrets import token_urlsafe
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from backend.api.app.core.config import Settings
from backend.api.scripts import check_connections

PG_PASSWORD = token_urlsafe(16)


def settings(**values):
    defaults = {
        "DATABASE_URL": f"postgresql+asyncpg://user:{PG_PASSWORD}@db.example:5432/base",
        "MEILI_URL": "http://meili.example:7700",
        "MEILI_API_KEY": token_urlsafe(16),
    }
    return Settings.model_validate({**defaults, **values})


def fake_connection(monkeypatch):
    """Remplace la connexion asyncpg ; aucun accès à la vraie base."""
    connection = AsyncMock()
    connection.get_server_version = Mock(return_value=SimpleNamespace(major=18, minor=1))
    connect = AsyncMock(return_value=connection)
    monkeypatch.setattr(check_connections, "connect_async", connect)
    return connect, connection


def meili_transport(version_status=200):
    """Faux Meilisearch : /health libre, /version soumis à la clé."""

    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "available"})
        return httpx.Response(version_status, json={"pkgVersion": "1.15.2"})

    return httpx.MockTransport(handler)


async def test_postgres_check_is_read_only_and_hides_credentials(monkeypatch):
    connect, connection = fake_connection(monkeypatch)
    result = await check_connections.check_postgres(settings())
    assert result == "db.example:5432 (PostgreSQL 18.1)"
    assert PG_PASSWORD not in result
    assert connect.await_args.kwargs.get("read_only", True) is True
    connection.fetchval.assert_awaited_once_with("SELECT 1")
    connection.close.assert_awaited_once()


async def test_postgres_check_requires_url():
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        await check_connections.check_postgres(settings(DATABASE_URL=None))


async def test_meilisearch_check_validates_key():
    config = settings()
    result = await check_connections.check_meilisearch(config, meili_transport())
    assert result == "meili.example:7700 (Meilisearch 1.15.2)"
    with pytest.raises(RuntimeError, match="clé refusée"):
        await check_connections.check_meilisearch(config, meili_transport(403))


async def test_run_reports_each_failure_without_secret(monkeypatch, capsys):
    config = settings()
    monkeypatch.setattr(check_connections, "connect_async", AsyncMock(side_effect=OSError("refus")))

    async def unreachable(_config):
        raise httpx.ConnectError("injoignable")

    monkeypatch.setattr(check_connections, "check_meilisearch", unreachable)
    assert await check_connections.run(config) == 1
    errors = capsys.readouterr().err
    assert "Postgres : ÉCHEC, OSError : refus" in errors
    assert "Meilisearch : ÉCHEC, ConnectError : injoignable" in errors
    assert config.MEILI_API_KEY.get_secret_value() not in errors


async def test_run_succeeds_when_both_services_answer(monkeypatch, capsys):
    fake_connection(monkeypatch)

    async def available(_config):
        return "meili.example:7700 (Meilisearch 1.15.2)"

    monkeypatch.setattr(check_connections, "check_meilisearch", available)
    assert await check_connections.run(settings()) == 0
    output = capsys.readouterr().out
    assert "Postgres : OK" in output and "Meilisearch : OK" in output
