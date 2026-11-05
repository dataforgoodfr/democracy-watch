from unittest.mock import AsyncMock

import pytest

from democracy_watch import db


@pytest.mark.parametrize(
    ("dsn", "expected"),
    [
        ("postgresql://example.invalid/test", "postgresql://example.invalid/test"),
        ("postgresql+asyncpg://example.invalid/test", "postgresql://example.invalid/test"),
    ],
)
async def test_async_connection_uses_explicit_dsn(monkeypatch, dsn, expected):
    monkeypatch.setenv("DATABASE_URL", "postgresql://other.invalid/test")
    connection = object()
    connect = AsyncMock(return_value=connection)
    monkeypatch.setattr(db.asyncpg, "connect", connect)
    assert await db.connect_async(dsn=dsn, timeout=4, command_timeout=3) is connection
    connect.assert_awaited_once_with(
        dsn=expected,
        timeout=4,
        command_timeout=3,
        server_settings={"default_transaction_read_only": "on", "statement_timeout": "3000"},
    )


@pytest.mark.parametrize("configured_dsn", [None, "postgresql://example.invalid/test"])
async def test_async_connection_uses_environment(monkeypatch, configured_dsn):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    if configured_dsn:
        monkeypatch.setenv("DATABASE_URL", configured_dsn)
    monkeypatch.setenv("PGHOST", "example.invalid")
    connect = AsyncMock()
    monkeypatch.setattr(db.asyncpg, "connect", connect)
    await db.connect_async()
    connect.assert_awaited_once_with(
        dsn=configured_dsn,
        timeout=15,
        command_timeout=15,
        server_settings={"default_transaction_read_only": "on", "statement_timeout": "15000"},
    )


async def test_async_connection_can_explicitly_disable_read_only(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    connect = AsyncMock()
    monkeypatch.setattr(db.asyncpg, "connect", connect)
    await db.connect_async(read_only=False, command_timeout=1)
    assert connect.call_args.kwargs["server_settings"] == {
        "default_transaction_read_only": "off",
        "statement_timeout": "1000",
    }


async def test_async_connection_propagates_failure(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    connect = AsyncMock(side_effect=TimeoutError)
    monkeypatch.setattr(db.asyncpg, "connect", connect)
    with pytest.raises(TimeoutError):
        await db.connect_async()
    connect.assert_awaited_once()
