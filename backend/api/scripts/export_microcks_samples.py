"""Extrait de vrais exemples Microcks pour quelques dossiers, en lecture seule.

Produit des artefacts secondaires Microcks `APIExamples`, découpés sous la limite de
3 145 728 caractères que l'analyseur YAML de Microcks (SnakeYAML) impose à chaque fichier.
La sortie contient des données réelles : l'écrire sous `build/` (ignoré par Git), jamais dans
un fichier suivi. Usage : `make microcks-samples` ; argument : répertoire de sortie.
"""

import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from duckdb import DuckDBPyConnection
from pydantic import BaseModel

from backend.api.app.amendements import adapter as amendements
from backend.api.app.articles import adapter as articles
from backend.api.app.core.config import Settings
from backend.api.app.core.database import CATALOG, open_database
from backend.api.app.dossiers import adapter as dossiers
from backend.api.app.schemas import Page, Pagination
from backend.api.app.textes import adapter as textes

# Petits dossiers de la XVIIe législature, avec articles et amendements.
DOSSIER_UIDS = ["DLR5L17N50879", "DLR5L17N50838", "DLR5L17N53940"]
PAGE_SIZE = 100
# Caractères interdits en YAML, ou lus comme sauts de ligne (\x85, \u2028, \u2029).
YAML_FORBIDDEN = re.compile("[\x7f-\x9f\u2028\u2029\ufffe\uffff]")
# Marge sous la limite SnakeYAML de 3 145 728 caractères par fichier importé.
MAX_FILE_CHARS = 2_500_000
DEFAULT_PAGE = Pagination()

type Sample = dict[str, Any]
type Lister = Callable[..., list[Any]]


def sample(path: str, name: str, parameters: dict[str, Any], response: Any) -> Sample:
    """Un exemple Microcks : même nom pour les paramètres et la réponse."""
    if isinstance(response, BaseModel):
        response = response.model_dump(mode="json")
    return {"path": path, "name": name, "parameters": parameters, "response": response}


def collection(
    db: DuckDBPyConnection, path: str, name: str, list_items: Lister, filters: dict[str, str]
) -> tuple[list[Sample], list[Any]]:
    """Toutes les pages de `limit=100`, plus la première page sans pagination explicite."""
    samples, everything, offset = [], [], 0
    while True:
        rows = list_items(db, **filters, limit=PAGE_SIZE + 1, offset=offset)
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


def one(path: str, item: Any) -> Sample:
    return sample(path, item.uid, {"uid": item.uid}, item)


def collect(db: DuckDBPyConnection, dossier_uids: list[str]) -> list[Sample]:
    """Parcourt la hiérarchie de chaque dossier : textes, articles, amendements."""
    samples: list[Sample] = []
    for dossier_uid in dossier_uids:
        dossier = dossiers.get_dossier(db, dossier_uid)
        if dossier is None:
            raise SystemExit(f"Dossier introuvable : {dossier_uid}")
        samples.append(one("/api/v0/dossiers/{uid}", dossier))
        params = {"dossier_uid": dossier_uid}
        found, texte_rows = collection(
            db, "/api/v0/textes", dossier_uid, textes.list_textes, params
        )
        samples += found + [one("/api/v0/textes/{uid}", texte) for texte in texte_rows]
        found, article_rows = collection(
            db, "/api/v0/articles", dossier_uid, articles.list_articles, params
        )
        samples += found + [one("/api/v0/articles/{uid}", article) for article in article_rows]
        for texte in texte_rows:
            filters = {**params, "texte_uid": texte.uid}
            found, rows = collection(
                db, "/api/v0/amendements", texte.uid, amendements.list_amendements, filters
            )
            samples += found + [one("/api/v0/amendements/{uid}", item) for item in rows]
            for article in (row for row in article_rows if row.texte.uid == texte.uid):
                found, _ = collection(
                    db,
                    "/api/v0/amendements",
                    article.uid,
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


def main(output: Path) -> None:
    connection = open_database(Settings())
    try:
        connection.execute(f"USE {CATALOG}")
        samples = collect(connection, DOSSIER_UIDS)
    finally:
        connection.close()
    write_examples(samples, output)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
