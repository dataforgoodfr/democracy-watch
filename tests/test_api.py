"""Tests du socle API FastAPI et de sa configuration."""

from fastapi.testclient import TestClient

from democracy_watch.api import create_app
from democracy_watch.config import DEFAULT_MEILISEARCH_URL, load_settings


def test_health_endpoint_returns_ok(monkeypatch):
    monkeypatch.delenv("MEILISEARCH_URL", raising=False)
    monkeypatch.delenv("MEILISEARCH_API_KEY", raising=False)

    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_load_settings_defaults_without_env(monkeypatch):
    monkeypatch.delenv("MEILISEARCH_URL", raising=False)
    monkeypatch.delenv("MEILISEARCH_API_KEY", raising=False)

    settings = load_settings()

    assert settings.meilisearch_url == DEFAULT_MEILISEARCH_URL
    assert settings.meilisearch_api_key == ""


def test_load_settings_reads_meilisearch_env(monkeypatch):
    expected_url = "https://search.example.org"
    expected_value = "local-dev-value"
    monkeypatch.setenv("MEILISEARCH_URL", f"{expected_url}/")
    monkeypatch.setenv("MEILISEARCH_API_KEY", expected_value)

    application = create_app()

    assert application.state.settings.meilisearch_url == expected_url
    assert application.state.settings.meilisearch_api_key == expected_value
