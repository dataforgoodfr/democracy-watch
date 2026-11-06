# API Democracy Watch (backend/api), déployée sur Coolify.
# Variables à fournir : API_KEY, DATABASE_URL, MEILI_URL, MEILI_KEY (et MEILI_INDEX, MEILI_EMBEDDER).
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

# curl : utilisé par le health check de Coolify à l'intérieur du conteneur
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY democracy_watch ./democracy_watch
COPY backend ./backend

EXPOSE 8000
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
CMD ["uv", "run", "--no-sync", "uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
