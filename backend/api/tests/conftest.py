from secrets import token_urlsafe
from unittest.mock import AsyncMock, Mock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.app.core.config import Settings
from backend.api.app.main import create_app


@pytest.fixture
async def application():
    config = Settings(_env_file=None, DATABASE_URL=None, API_PASSWORD=token_urlsafe(32))
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
async def db_session(application, monkeypatch):
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = Mock()
    session.execute.return_value.mappings.return_value.all.return_value = []
    session.execute.return_value.mappings.return_value.one_or_none.return_value = None
    context = AsyncMock()
    context.__aenter__.return_value = session
    with monkeypatch.context() as patch:
        patch.setattr(application.state, "session_factory", Mock(return_value=context))
        yield session
        if context.__aenter__.await_count:
            assert context.__aexit__.await_count == context.__aenter__.await_count
