"""API FastAPI de Democracy Watch.

Lancement en local :
uv run uvicorn democracy_watch.api:app --reload
"""

from fastapi import FastAPI

app = FastAPI(title="Democracy Watch API")


@app.get("/health")
def health() -> dict[str, str]:
    """Indique que l'API répond."""
    return {"status": "ok"}
