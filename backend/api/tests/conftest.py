from pathlib import Path
from secrets import token_urlsafe

import duckdb
import pytest
from httpx import ASGITransport, AsyncClient

from backend.api.app.core.config import Settings
from backend.api.app.core.database import CATALOG
from backend.api.app.main import create_app

ROOT = Path(__file__).resolve().parents[3]
DATA_MODEL = ROOT / "backend/source_data/DATA_MODEL_V3_DUCKDB.sql"
SEED = Path(__file__).with_name("seed.sql")


@pytest.fixture(scope="session")
def seeded_database():
    """Base en mémoire au modèle V3 réel, remplie de données synthétiques."""
    connection = duckdb.connect()
    connection.execute(f"ATTACH ':memory:' AS {CATALOG}")
    connection.execute(f"USE {CATALOG}")
    connection.execute(DATA_MODEL.read_text())
    connection.execute(SEED.read_text())
    yield connection
    connection.close()


@pytest.fixture
async def application():
    config = Settings(_env_file=None, DATA_PATH=None, API_PASSWORD=token_urlsafe(32))
    app = create_app(config)
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
async def client(application):
    password = application.state.settings.API_PASSWORD.get_secret_value()
    async with AsyncClient(
        transport=ASGITransport(app=application, raise_app_exceptions=False),
        base_url="http://test",
        headers={"Authorization": f"Bearer {password}"},
    ) as client:
        yield client


@pytest.fixture
def database(application, seeded_database, monkeypatch):
    """Branche la base synthétique à l'application, à la place de DATA_PATH."""
    monkeypatch.setattr(application.state, "database", seeded_database)
    return seeded_database
