from secrets import token_urlsafe

import duckdb
import httpx
import pytest

from backend.api.app.core.config import Settings
from backend.api.scripts import check_connections


def settings(**values):
    defaults = {
        "DATA_PATH": None,
        "MEILI_URL": "http://meili.example:7700",
        "MEILI_API_KEY": token_urlsafe(16),
    }
    return Settings.model_validate({**defaults, **values})


def data_file(tmp_path):
    """Petite base locale : aucun accès aux vraies données."""
    path = tmp_path / "clair.duckdb"
    with duckdb.connect(path) as connection:
        connection.execute("CREATE TABLE dossiers AS SELECT * FROM range(3)")
    return str(path)


def meili_transport(version_status=200):
    """Faux Meilisearch : /health libre, /version soumis à la clé."""

    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "available"})
        return httpx.Response(version_status, json={"pkgVersion": "1.15.2"})

    return httpx.MockTransport(handler)


def test_data_check_counts_dossiers(tmp_path):
    path = data_file(tmp_path)
    assert check_connections.check_data(settings(DATA_PATH=path)) == (
        f"{path} (DuckDB {duckdb.__version__}, 3 dossiers)"
    )


def test_data_check_requires_path():
    with pytest.raises(ValueError, match="DATA_PATH"):
        check_connections.check_data(settings())


async def test_meilisearch_check_validates_key():
    config = settings()
    result = await check_connections.check_meilisearch(config, meili_transport())
    assert result == "meili.example:7700 (Meilisearch 1.15.2)"
    with pytest.raises(RuntimeError, match="clé refusée"):
        await check_connections.check_meilisearch(config, meili_transport(403))


async def test_run_reports_each_failure_without_secret(monkeypatch, capsys):
    config = settings(DATA_PATH="/chemin/absent.duckdb")

    async def unreachable(_config):
        raise httpx.ConnectError("injoignable")

    monkeypatch.setattr(check_connections, "check_meilisearch", unreachable)
    assert await check_connections.run(config) == 1
    errors = capsys.readouterr().err
    assert "Données : ÉCHEC, IOException" in errors
    assert "Meilisearch : ÉCHEC, ConnectError : injoignable" in errors
    assert config.MEILI_API_KEY.get_secret_value() not in errors


async def test_run_succeeds_when_both_services_answer(monkeypatch, capsys, tmp_path):
    path = data_file(tmp_path)

    async def available(_config):
        return "meili.example:7700 (Meilisearch 1.15.2)"

    monkeypatch.setattr(check_connections, "check_meilisearch", available)
    assert await check_connections.run(settings(DATA_PATH=path)) == 0
    output = capsys.readouterr().out
    assert "Données : OK" in output and "Meilisearch : OK" in output
