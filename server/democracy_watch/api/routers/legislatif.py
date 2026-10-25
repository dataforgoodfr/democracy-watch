from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from democracy_watch.api.deps import get_repository
from democracy_watch.api.schemas import Amendement, Article, Dossier

router = APIRouter(prefix="/api", tags=["législatif"])

Repo = Annotated[object, Depends(get_repository)]


def _found(value, what):
    if value is None:
        raise HTTPException(status_code=404, detail=f"{what} introuvable")
    return value


@router.get("/dossiers/{dossier_uid}", response_model=Dossier)
def get_dossier(dossier_uid: str, repository: Repo):
    """Fiche d'un dossier législatif (projet ou proposition de loi), ses commissions et ses textes."""
    return _found(repository.get_dossier(dossier_uid), "Dossier")


@router.get("/textes/{texte_ref}/articles", response_model=list[Article])
def list_articles(texte_ref: str, repository: Repo):
    """Articles d'un texte, dans l'ordre."""
    return repository.list_articles(texte_ref)


@router.get("/textes/{texte_ref}/amendements", response_model=list[Amendement])
def list_amendements(
    texte_ref: str,
    repository: Repo,
    article: Annotated[
        str | None, Query(description="Article visé, ex. « Article 3 »")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
):
    """Amendements d'un texte, éventuellement d'un article (vue « avancement »). Ajout à la RFC."""
    return repository.list_amendements(texte_ref, article=article, limit=limit)


@router.get("/amendements/{uid}", response_model=Amendement)
def get_amendement(uid: str, repository: Repo):
    """Un amendement."""
    return _found(repository.get_amendement(uid), "Amendement")
