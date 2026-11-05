"""Contrat public de la recherche, indépendant des index Meilisearch."""

from typing import Any, Literal

from pydantic import BaseModel, Field

SearchType = Literal["amendements", "dossiers", "articles"]
Label = Field(min_length=1, max_length=100)


class SearchQuery(BaseModel):
    q: str = Field(min_length=3, max_length=500, pattern=r"\S")
    types: list[SearchType] = Field(
        default=["amendements", "dossiers", "articles"], min_length=1, max_length=3
    )
    legislature: int | None = Field(default=None, ge=1, le=99)
    dossier_uid: str | None = Field(default=None, min_length=1, max_length=100)
    groupe_politique: list[str] = Field(default=[], max_length=20)
    outcome: list[str] = Field(default=[], max_length=20)
    semantic_ratio: float = Field(default=0.5, ge=0.0, le=1.0)
    page: int = Field(default=1, ge=1, le=1000)
    hits_per_page: int = Field(default=20, ge=1, le=100)


class SearchGroup(BaseModel):
    type: SearchType
    hits: list[dict[str, Any]]
    facets: dict[str, dict[str, int]]
    page: int
    hits_per_page: int
    total_pages: int
    total_hits: int


class SearchResults(BaseModel):
    results: list[SearchGroup]
