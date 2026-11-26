FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.14-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY backend/api/app/ backend/api/app/
COPY democracy_watch/ democracy_watch/
COPY backend/schemas/database_mapping.py backend/schemas/database_mapping.py
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "backend.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
