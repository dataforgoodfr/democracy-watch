"""Lot 3 : construit le corpus d'évaluation an_premiere_lecture depuis l'API Tricoteuses et le
fige par un manifeste.

Une étape = (texte d'entrée, amendements déposés dessus, texte de sortie officiel), pour la première
lecture à l'Assemblée : commission (texte déposé → texte de la commission) et séance (texte de la
commission → texte adopté). Actes, textes découpés et amendements viennent de l'API Tricoteuses
(décision du 13 novembre 2026), via l'adaptateur datasources/tricoteuses.py. Les réponses sont
gardées dans donnees/tricoteuses/ : relancer ne retélécharge rien.

Le découpage développement/test se fait par dossier, par hachage : stable, et les deux étapes d'un
dossier restent ensemble. Le test ne sert qu'à la comparaison finale.


Usage : uv run python -m projection.eval.corpus
"""

import dataclasses
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from projection.datasources import tricoteuses

HERE = Path(__file__).parent
DATA = HERE / "donnees"
NAME = "an_premiere_lecture"  # le périmètre : la première lecture à l'Assemblée
CORPUS = DATA / f"{NAME}.jsonl"
MANIFEST = HERE / f"{NAME}_manifeste.json"
CACHE = DATA / "tricoteuses"
LEGISLATURE = 17
FIELDS = [f.name for f in dataclasses.fields(tricoteuses.Amendement) if f.name != "auteur"]
DEV_SHARE = 70
SALT = "moteur-v1"
# Dossiers vus pendant la construction du moteur (exemples, fixtures, tests) :
# ni développement ni test.
EXCLUDED_DOSSIERS = {
    "DLR5L17N51328": "PPL n° 822, tombée en test alors qu'elle a servi à construire le moteur"
}


def split_de(dossier):
    if dossier in EXCLUDED_DOSSIERS:
        return "exclu"
    return (
        "dev"
        if int(hashlib.sha256(f"{SALT}:{dossier}".encode()).hexdigest(), 16) % 100 < DEV_SHARE
        else "test"
    )


def is_finance(titre):
    return bool(re.search(r"finances|financement de la sécurité sociale", titre or "", re.I))


def cached(name, computation):
    """Résultat JSON de calcul(), lu dans le cache s'il y est, sinon calculé puis gardé."""
    path = CACHE / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    value = computation()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return value


def text(ref):
    """{uid, titre, articles} (un tricoteuses.Texte en JSON), ou None quand Tricoteuses n'a pas
    le texte ou qu'il n'a aucun article."""

    def read():
        try:
            return dataclasses.asdict(tricoteuses.read_text(ref))
        except tricoteuses.TextNotFound:
            return None

    return cached(f"textes/{ref}", read)


def amendements(ref):
    """Amendements déposés sur le texte, au format du corpus.

    Sans l'auteur, inutile à l'évaluation.
    """

    def read():
        return [{c: getattr(a, c) for c in FIELDS} for a in tricoteuses.text_amendements(ref)]

    return cached(f"amendements/{ref}", read)


def resolve(articles, source):
    """Les articles, ceux marqués inchangés reprenant les lignes et la suppression de l'article
    de même numéro dans source (les articles du texte précédent) ; vides si source ne l'a pas."""
    by_number = {a["numero"]: a for a in source or []}
    return [
        {
            **a,
            "lignes": by_number[a["numero"]]["lignes"],
            "supprime": by_number[a["numero"]]["supprime"],
        }
        if a.get("inchange") and a["numero"] in by_number
        else a
        for a in articles
    ]


def dossier_steps(lecture, excluded):
    """Les étapes retenues d'une PremiereLecture.

    Chaque étape écartée est comptée dans excluded, avec sa raison.
    """
    steps, dossier = [], lecture.dossier
    for name, previous, input_, output in (
        ("commission", None, lecture.depose, lecture.commission),
        ("seance", lecture.depose, lecture.commission, lecture.adopte),
    ):
        if not input_ or not output:
            excluded["acte manquant"] += 1
            continue
        deposited = amendements(input_)
        if not any(a["sort"] == "Adopté" for a in deposited):
            excluded["aucun amendement adopté"] += 1
            continue
        input_text, output_text = text(input_), text(output)
        if input_text is None:
            excluded["texte d'entrée introuvable"] += 1
            continue
        if output_text is None:
            excluded["texte de sortie introuvable"] += 1
            continue
        titre = input_text["titre"]
        # Un article inchangé n'a que sa mention : son texte est celui du texte précédent.
        before = text(previous) if previous else None
        entree = resolve(input_text["articles"], before and before["articles"])
        steps.append(
            {
                "id": f"{dossier}:{name}",
                "dossier": dossier,
                "titre": titre,
                "etape": name,
                "split": split_de(dossier),
                "finances": is_finance(titre),
                "entree": {"ref": input_, "articles": entree},
                "sortie": {"ref": output, "articles": resolve(output_text["articles"], entree)},
                "amendements": deposited,
            }
        )
    return steps


def build():
    excluded, steps = Counter(), []
    lectures = cached(
        f"premiere_lecture_{LEGISLATURE}",
        lambda: [
            dataclasses.asdict(lecture)
            for lecture in tricoteuses.premiere_lecture_texts(LEGISLATURE)
        ],
    )
    for lecture in (tricoteuses.PremiereLecture(**d) for d in lectures):
        steps += dossier_steps(lecture, excluded)
        print(f"{lecture.dossier} : {len(steps)} étapes retenues", flush=True)
    return steps, excluded


def main():
    steps, excluded = build()
    write(steps, excluded, CORPUS, MANIFEST, source=tricoteuses.URL)


def write(steps, excluded, corpus, manifest, source=None):
    """Écrit le corpus (une étape par ligne, triées) et son manifeste.

    Le manifeste fige le corpus par son empreinte.
    """
    steps.sort(key=lambda e: e["id"])
    body = "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in steps)
    corpus.write_text(body, encoding="utf-8")
    counted = Counter((e["etape"], e["split"]) for e in steps)
    manifest.write_text(
        json.dumps(
            {
                "nom": NAME,
                **({"source": source} if source else {}),
                "date": date.today().isoformat(),
                "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "etapes": len(steps),
                "par_etape_et_split": {f"{k[0]}/{k[1]}": v for k, v in sorted(counted.items())},
                "amendements_adoptes": sum(
                    a["sort"] == "Adopté" for e in steps for a in e["amendements"]
                ),
                "exclus": dict(excluded),
                "dossiers_exclus": EXCLUDED_DOSSIERS,
                "sel_split": SALT,
                "ids": {
                    "dev": [e["id"] for e in steps if e["split"] == "dev"],
                    "test": [e["id"] for e in steps if e["split"] == "test"],
                },
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(manifest.read_text(encoding="utf-8")[:400])


if __name__ == "__main__":
    main()
