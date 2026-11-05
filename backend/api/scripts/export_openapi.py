"""Exporte le contrat avec des exemples Microcks, sans lire les données métier."""

import json
from typing import Any

from backend.api.app.core.config import Settings
from backend.api.app.main import create_app


def build_document() -> dict[str, Any]:
    """Ajoute des scénarios nommés aux collections et à la vivacité uniquement."""
    app = create_app(Settings(_env_file=None, DATABASE_URL=None, API_PASSWORD=None))
    document = app.openapi()
    schemas = document["components"]["schemas"]
    for path, methods in document["paths"].items():
        if "{" in path or "get" not in methods:
            continue
        operation = methods["get"]
        content = (
            operation.get("responses", {}).get("200", {}).get("content", {}).get("application/json")
        )
        if content is None:
            continue
        if path == "/health":
            example = {"status": "ok"}
        else:
            reference = content.get("schema", {}).get("$ref", "").rsplit("/", 1)[-1]
            properties = schemas.get(reference, {}).get("properties", {})
            if not {"items", "limit", "offset", "has_more"}.issubset(properties):
                continue
            example = {"items": [], "limit": 20, "offset": 0, "has_more": False}
            for parameter in operation.get("parameters", []):
                if parameter["in"] == "query" and parameter["name"] in ("limit", "offset"):
                    parameter["examples"] = {"default": {"value": example[parameter["name"]]}}
        content["examples"] = {
            "default": {"summary": "Exemple synthétique sans données réelles", "value": example}
        }
    return document


if __name__ == "__main__":
    print(json.dumps(build_document(), ensure_ascii=False, indent=2))
