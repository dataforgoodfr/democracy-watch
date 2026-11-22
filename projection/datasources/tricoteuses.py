"""Adaptateur de l'API Tricoteuses (https://parlement.tricoteuses.fr).

Seul ce module connaît les noms de champs de Tricoteuses. Il ne dépend pas du moteur : il produit
ses propres données (Text découpé en Article, Amendement, PremiereLecture), que le serveur et
l'évaluation passent au moteur.

Pièges traités (voir learnings/categories/tricoteuses.md) :
- pas de champ numéro d'article : on le lit dans le titre
  (« Article 5 bis (nouveau) » → « 5 BIS ») ;
  l'identifiant (`article-1`) ne suit pas toujours le numéro officiel (« Article unique ») ;
- une mention seule (« (Non modifié) », « (Supprimé) ») est rangée comme un alinéa : on l'écarte,
  sinon tous les numéros d'alinéas de l'article sont décalés d'un cran ;
- un article inchangé (« (Non modifié) », « (Conforme) ») n'a que cette mention : il est marqué
  `inchange`, son texte est à prendre dans le texte précédent ;
- un tableau de dispositions applicables outre-mer peut arriver typé « Article » : écarté.
"""

import dataclasses
import html
import re

import requests

URL = "https://parlement.tricoteuses.fr"
TIMEOUT = 120  # secondes : un texte long pèse plusieurs Mo
PER_PAGE = 100
MENTION = re.compile(
    r"\((non modifié|supprimés?|suppression maintenue|suppression conforme|conforme)\)\.?", re.I
)
RANGE = re.compile(r"^(\d+) À (\d+)$")
# Un vrai titre d'article : « Article 5 bis », « Article 1er », « Article unique »…
ARTICLE_TITLE = re.compile(r"\s*Articles?\s+(\d|unique\b|liminaire\b|premier\b)", re.I)


@dataclasses.dataclass
class Amendement:
    """Un amendement tel que le donne Tricoteuses.

    Le moteur n'en lit que quelques champs ; les autres sont
    ce que l'interface et l'évaluation affichent.
    """

    uid: str
    numero: str  # « CE11 », « 3 (Rect) »
    texte_ref: str  # texte sur lequel l'amendement est déposé
    article_vise: str | None  # « ART. UNIQUE », « APRÈS ART. UNIQUE », « TITRE »
    alinea: str | None  # indice seulement : peut contredire le dispositif
    dispositif: str  # HTML, un <p> par alinéa
    parent_uid: str | None  # sous-amendement : l'amendement qu'il modifie
    tri_amendement: str | None
    date_sort: str | None  # heure de la décision (ISO, UTC)
    sort: str | None = None
    id_identique: str | None = None  # série d'amendements identiques, votés ensemble
    auteur: str | None = None
    numero_ordre: int | None = None


@dataclasses.dataclass(frozen=True)
class Article:
    """Un article tel que le donne Tricoteuses, avant le moteur."""

    numero: str  # « PREMIER », « 5 BIS »
    lignes: tuple[str, ...]  # un alinéa par élément, mentions seules retirées
    supprime: bool = False
    inchange: bool = False  # mention seule « (Non modifié) » ou « (Conforme) » : lignes vides
    issu_de_plage: bool = (
        False  # « Articles 2 à 4 » : les lignes sont partagées, non propres à l'article
    )


@dataclasses.dataclass(frozen=True)
class Text:
    uid: str
    titre: str
    articles: tuple[Article, ...]


@dataclasses.dataclass(frozen=True)
class PremiereLecture:
    """Textes de la première lecture à l'Assemblée d'un dossier ; None quand l'acte manque."""

    dossier: str
    depose: str | None = None
    commission: str | None = None
    adopte: str | None = None  # le BTA, jamais le TAP


class TextNotFound(Exception):
    """Le texte demandé n'existe pas chez Tricoteuses, ou n'a aucun article."""


def get(path, params=None):
    """GET sur l'API, renvoie la réponse (lève requests.HTTPError si le statut n'est pas 2xx)."""
    response = requests.get(f"{URL}{path}", params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response


def numbers_from_title(titre):
    """Numéros d'un titre d'article.

    « Article 1er » → [PREMIER] ; « Article 5 bis (nouveau) » → [5 BIS] ;
    « Articles 2 à 4 » → [2, 3, 4] ; « Articles 15, 16 à 18 et 20 » → [15, 16, 17, 18, 20].
    """
    body = re.sub(r"\(.*?\)", "", titre).replace("\xa0", " ")
    body = re.sub(r"^\s*Articles?\s+", "", body, flags=re.I)
    body = re.sub(r"\s+", " ", body).strip().upper()
    # Espaces manquants dans certains titres : « 1erbis », « 25C », « 4 nonies et4 decies ».
    body = re.sub(r"(\d(?:ER)?+)(?=[A-Z])", r"\1 ", body)
    body = re.sub(r" ET(?=\d)", " ET ", body)
    numbers = []
    for piece in (m.strip() for m in re.split(r",| ET ", body)):
        if range_ := RANGE.match(piece):
            numbers += [str(n) for n in range(int(range_[1]), int(range_[2]) + 1)]
        elif piece:
            numbers.append("PREMIER" if re.fullmatch(r"1 ?ER|PREMIER", piece) else piece)
    return numbers


def articles_from_document(document):
    """Réponse de /documents/{uid} → les Article, dans l'ordre du texte.

    La réponse doit inclure les subdivisions et les alinéas.
    """
    alineas = {}
    for alinea in document.get("alineas") or []:
        alineas.setdefault(alinea["articleRefHash"], []).append(alinea)
    articles = []
    subdivisions = sorted(document.get("subdivisions") or [], key=lambda s: s.get("sequence") or 0)
    for subdivision in subdivisions:
        if subdivision["type"] != "Article" or not ARTICLE_TITLE.match(subdivision["titre"]):
            continue
        lignes, supprime, inchange = [], "supprim" in subdivision["titre"].lower(), False
        for alinea in sorted(alineas.get(subdivision["hash"], []), key=lambda a: a["numero"]):
            # Un tableau arrive aplati en un seul alinéa, cellules séparées par des tabulations et
            # lignes par des retours : sans ce remplacement, chaque ligne du tableau deviendrait un
            # faux alinéa.
            text = re.sub(r"[ \t]*[\t\n][ \t\n]*", " ", alinea["texte"] or "").strip()
            if MENTION.fullmatch(text):
                supprime = supprime or "suppr" in text.lower()
                inchange = "suppr" not in text.lower()
            elif text:
                lignes.append(text)
        numeros = numbers_from_title(subdivision["titre"])
        for numero in numeros:
            articles.append(
                Article(
                    numero,
                    tuple(lignes),
                    supprime,
                    inchange and not lignes and not supprime,
                    issu_de_plage=len(numeros) > 1,
                )
            )
    if not articles:
        raise TextNotFound(f"{document.get('uid')} : aucun article")
    return tuple(articles)


def amendement_from(data):
    """Un amendement de /amendements/json → Amendement."""
    identical = data.get("idDiscussionIdentique")
    date_sort = data.get("dateSort")
    return Amendement(
        uid=data["uid"],
        numero=data.get("numeroLong") or "",
        texte_ref=data.get("documentRefUid") or "",
        article_vise=data.get("divisionArticleDesignationCourte"),
        alinea=data.get("alineaDesignation"),
        # Le HTML garde un <p> par alinéa ; la version texte coupe les lignes à 80 caractères.
        dispositif=data.get("dispositifHtml") or data.get("dispositif") or "",
        parent_uid=data.get("amendementParentRefUid"),
        tri_amendement=data.get("triAmendement"),
        # Seul l'ordre compte : on garde l'heure UTC, sans millisecondes ni fuseau.
        date_sort=date_sort[:19] if date_sort else None,
        sort=data.get("sortAmendement"),
        id_identique=str(identical) if identical is not None else None,
        # Les noms arrivent parfois avec des entités HTML (« Barth&#232;s »).
        auteur=html.unescape(data.get("signatairesLibelle") or "") or None,
        # Arrive en texte ou en entier selon les amendements.
        numero_ordre=int(order)
        if (order := str(data.get("numeroOrdreDepot") or "")).isdigit()
        else None,
    )


def document(uid):
    """Réponse brute de /documents/{uid}, avec subdivisions et alinéas."""
    try:
        response = get(f"/documents/{uid}", {"include": "subdivisions,alineas"})
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            raise TextNotFound(uid) from error
        raise
    return response.json().get("data") or {}


def document_title(data):
    return data.get("titrePrincipal") or data.get("uid")


def read_text(uid):
    """Le Texte uid, découpé en articles.

    Lève TexteIntrouvable s'il n'existe pas ou n'a aucun article.
    """
    data = document(uid)
    return Text(uid, document_title(data), articles_from_document(data))


def all_pages(path, params):
    """Tous les éléments d'une liste paginée de l'API."""
    page, pages = 1, 1
    while page <= pages:
        response = get(path, {**params, "page": page, "perPage": PER_PAGE})
        yield from response.json().get("data") or []
        pages = int(response.headers.get("total-page") or 1)
        page += 1


def text_amendements(uid):
    """Tous les amendements déposés sur le texte, toutes pages lues."""
    return [amendement_from(a) for a in all_pages("/amendements/json", {"documentRefUid": uid})]


def premiere_lecture_texts(legislature):
    """Les PremiereLecture des dossiers de la législature, triées par dossier.

    Pour la décision en séance, `texteAssocieRefUid` donne le texte adopté (BTA) ;
    `documentRefUid` donnerait le TAP.
    """
    dossiers = {}
    acts = (
        ("depose", "AN1-DEPOT", "texteAssocieRefUid"),
        ("commission", "AN1-COM-FOND-RAPPORT", "texteAdopteRefUid"),
        ("adopte", "AN1-DEBATS-DEC", "texteAssocieRefUid"),
    )
    for key, code, field in acts:
        for act in all_pages(
            "/actesLegislatifs/json", {"codeActe": code, "legislature": legislature}
        ):
            ref = act.get(field)
            if act.get("dossierRefUid") and ref and (key != "adopte" or "BTA" in ref):
                dossiers.setdefault(act["dossierRefUid"], {})[key] = ref
    return [PremiereLecture(dossier, **texts) for dossier, texts in sorted(dossiers.items())]
