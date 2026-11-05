"""Conventions de pagination partagées, indépendantes des modèles de stockage."""

from typing import Annotated, Self

from fastapi import Query
from pydantic import BaseModel, Field


class Pagination(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=10000)


PaginationQuery = Annotated[Pagination, Query()]


class Page[T](BaseModel):
    items: list[T]
    limit: int
    offset: int
    has_more: bool

    @classmethod
    def from_items(cls, items: list[T], pagination: Pagination) -> Self:
        """Retire la ligne de contrôle et construit les métadonnées de page."""
        return cls(
            items=items[: pagination.limit],
            has_more=len(items) > pagination.limit,
            **pagination.model_dump(),
        )
