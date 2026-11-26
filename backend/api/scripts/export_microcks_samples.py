"""Extrait de vrais exemples Microcks pour quelques dossiers, en lecture seule.

Produit des artefacts secondaires Microcks `APIExamples`, découpés sous la limite de
3 145 728 caractères que l'analyseur YAML de Microcks (SnakeYAML) impose à chaque fichier.
La sortie contient des données réelles : l'écrire sous `build/` (ignoré par Git), jamais dans
un fichier suivi. Usage : `make microcks-samples` ; argument : répertoire de sortie.
"""

import asyncio
import json
import re
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.api.app.amendements import adapter as amendements
from backend.api.app.articles import adapter as articles
from backend.api.app.core.config import Settings
from backend.api.app.dossiers import adapter as dossiers
from backend.api.app.schemas import Page, Pagination
from backend.api.app.textes import adapter as textes
from democracy_watch.db import connect_async

DOSSIER_UIDS = [
    "fe2523ff-452f-4cf7-8177-16c8b3a06607",
    "72efeeaf-78f6-4ca0-9b06-bdcc99fec3f7",
    "f39287e8-bc24-41df-b5f7-895a73e40b30",
    "ca646745-69ff-480c-9d0d-ec0023086c13",
    "843436f1-0161-4333-80f9-e190602da780",
    "7b0fad37-c97c-4e19-ab80-99858f7950e1",
    "e650bea4-4250-460f-908b-bbd5fe6ab8ca",
    "855a62e5-cf1c-4c30-a07d-16ff3ebfaf0f",
    "eab84e1e-3ad3-47fa-ab6b-3971f112bafe",
]
PAGE_SIZE = 100
# Caractères interdits en YAML, ou lus comme sauts de ligne (\x85, \u2028, \u2029).
YAML_FORBIDDEN = re.compile("[\x7f-\x9f\u2028\u2029\ufffe\uffff]")
# Marge sous la limite SnakeYAML de 3 145 728 caractères par fichier importé.
MAX_FILE_CHARS = 2_500_000
DEFAULT_PAGE = Pagination()

type Sample = dict[str, Any]
type Lister = Callable[..., Awaitable[list[Any]]]


def sample(path: str, name: str, parameters: dict[str, Any], response: Any) -> Sample:
    """Un exemple Microcks : même nom pour les paramètres et la réponse."""
    if isinstance(response, BaseModel):
        response = response.model_dump(mode="json")
    return {"path": path, "name": name, "parameters": parameters, "response": response}


async def collection(
    session: AsyncSession, path: str, name: str, list_items: Lister, filters: dict[str, str]
) -> tuple[list[Sample], list[Any]]:
    """Toutes les pages de `limit=100`, plus la première page sans pagination explicite."""
    samples, everything, offset = [], [], 0
    while True:
        rows = await list_items(session, **filters, limit=PAGE_SIZE + 1, offset=offset)
        page = Page.from_items(rows, Pagination(limit=PAGE_SIZE, offset=offset))
        parameters = {**filters, "limit": PAGE_SIZE, "offset": offset}
        samples.append(sample(path, f"{name}-offset-{offset}", parameters, page))
        everything += page.items
        if not page.has_more:
            break
        offset += PAGE_SIZE
    first = Page.from_items(everything[: DEFAULT_PAGE.limit + 1], DEFAULT_PAGE)
    samples.append(sample(path, name, filters, first))
    return samples, everything


async def collect(session: AsyncSession, dossier_uids: list[str]) -> list[Sample]:
    samples: list[Sample] = []
    for dossier_uid in dossier_uids:
        dossier = await dossiers.get_dossier(session, dossier_uid)
        if dossier is None:
            raise SystemExit(f"Dossier introuvable : {dossier_uid}")
        key = dossier_uid[:8]
        params = {"dossier_uid": dossier_uid}
        samples.append(sample("/api/v0/dossiers/{dossier_uid}", key, params, dossier))
        found, rows = await collection(session, "/api/v0/textes", key, textes.list_texts, params)
        samples += found
        found, rows = await collection(
            session, "/api/v0/articles", key, articles.list_articles, params
        )
        samples += found
        for article in rows:
            samples.append(
                sample("/api/v0/articles/{uid}", article.uid, {"uid": article.uid}, article)
            )
        for reference in dict.fromkeys(article.text_reference for article in rows):
            filters = {"dossier_uid": dossier_uid, "text_reference": reference}
            found, amendement_rows = await collection(
                session,
                "/api/v0/amendements",
                f"{key}-{reference}",
                amendements.list_amendements,
                filters,
            )
            samples += found
            for item in amendement_rows:
                samples.append(
                    sample("/api/v0/amendements/{uid}", item.uid, {"uid": item.uid}, item)
                )
            for article in (row for row in rows if row.text_reference == reference):
                found, _ = await collection(
                    session,
                    "/api/v0/amendements",
                    f"{key}-{article.uid}",
                    amendements.list_amendements,
                    {**filters, "article_uid": article.uid},
                )
                samples += found
    return samples


def to_yaml_flow(value: Any) -> str:
    """JSON valide en YAML : seuls les caractères interdits sont échappés en \\uXXXX."""
    text = json.dumps(value, ensure_ascii=False)
    return YAML_FORBIDDEN.sub(lambda match: f"\\u{ord(match[0]):04x}", text)


def api_examples(samples: list[Sample]) -> str:
    """Format Microcks APIExamples ; nom et version doivent égaler ceux du contrat OpenAPI."""
    settings = Settings(_env_file=None)
    operations: dict[str, dict[str, Any]] = {}
    for item in samples:
        operations.setdefault(f"GET {item['path']}", {})[item["name"]] = {
            "request": {"parameters": {k: str(v) for k, v in item["parameters"].items()}},
            "response": {
                "status": "200",
                "mediaType": "application/json",
                "body": item["response"],
            },
        }
    metadata = {"name": settings.PROJECT_NAME, "version": settings.VERSION}
    # YAML en style bloc pour l'en-tête (Microcks y détecte le type), JSON (flux YAML) ensuite.
    return (
        "apiVersion: mocks.microcks.io/v1alpha1\n"
        "kind: APIExamples\n"
        f"metadata: {json.dumps(metadata)}\n"
        f"operations: {to_yaml_flow(operations)}\n"
    )


def write_examples(samples: list[Sample], output: Path) -> None:
    """Écrit des fichiers YAML d'environ MAX_FILE_CHARS au plus."""
    output.mkdir(parents=True, exist_ok=True)
    for old in output.glob("examples-*.yaml"):
        old.unlink()
    chunks: list[list[Sample]] = [[]]
    size = 0
    for item in samples:
        item_size = len(json.dumps(item, ensure_ascii=False))
        if chunks[-1] and size + item_size > MAX_FILE_CHARS:
            chunks.append([])
            size = 0
        chunks[-1].append(item)
        size += item_size
    for index, chunk in enumerate(chunks):
        (output / f"examples-{index:02d}.yaml").write_text(api_examples(chunk))


async def main(output: Path) -> None:
    engine = create_async_engine(
        "postgresql+asyncpg://", async_creator=lambda: connect_async(read_only=True)
    )
    try:
        async with AsyncSession(engine) as session:
            samples = await collect(session, DOSSIER_UIDS)
    finally:
        await engine.dispose()
    write_examples(samples, output)


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1])))
