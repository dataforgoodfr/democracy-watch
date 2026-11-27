"""Tests de l'API FastAPI."""

from fastapi.testclient import TestClient

from democracy_watch.api import app


def test_health_repond_ok():
    reponse = TestClient(app).get("/health")

    assert reponse.status_code == 200
    assert reponse.json() == {"status": "ok"}
