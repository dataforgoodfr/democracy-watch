"""Lance l'évaluation : fait tourner des prédicteurs sur le corpus et affiche leurs scores.

Un prédicteur est la fonction F de la RFC, entrée → sortie : il reçoit les articles du texte
d'entrée et les amendements déposés dessus, et renvoie les articles prédits pour la sortie, au
format du corpus. Il ne voit jamais la sortie officielle. La référence « identity » (recopier
l'entrée) est toujours affichée : c'est le score à battre.

Usage, depuis la racine du repo, une fois le corpus construit (projection/eval/corpus.py) :
    uv run python -m projection.eval.run                           # la référence seule
    uv run python -m projection.eval.run paquet.module:fonction    # un algorithme
    uv run python -m projection.eval.run … --split test --json results.json

Seules les étapes du manifeste sont évaluées (un corpus reconstruit plus tard en contient de
nouvelles), sans les textes budgétaires (PLF, PLFSS), comme le prévoit la RFC.
"""

import argparse
import dataclasses
import importlib
import json
from collections.abc import Callable
from pathlib import Path

from projection.eval import corpus
from projection.eval.metrics import score_step, summarize
from projection.eval.metrics.formats import CorpusArticle, Step, SubsetSummary

type Predictor = Callable[[list[CorpusArticle], list[dict]], list[CorpusArticle]]

# Score affiché pour chaque métrique ; le JSON les contient tous.
SHOWN = {"identical": "identical", "presence": "presence", "words": "f1"}
TITLES = {
    "changed": "Articles the official text changes (the score that matters)",
    "all": "All articles",
    "unchanged": "Articles the official text leaves as they were (copying the input is perfect)",
}


def identity(entree: list[CorpusArticle], amendements: list[dict]) -> list[CorpusArticle]:
    """Référence : recopie l'entrée sans appliquer aucun amendement."""
    return entree


def load_predictor(name: str) -> Predictor:
    """« identity », ou une fonction donnée par « module:fonction »."""
    if name == "identity":
        return identity
    module, _, function = name.partition(":")
    return getattr(importlib.import_module(module), function)


def load_steps(split: str) -> tuple[list[Step], int]:
    """Les étapes du manifeste pour ce split, hors textes budgétaires, et le nombre d'étapes du
    manifeste absentes du corpus construit."""
    ids = set(json.loads(Path(corpus.MANIFEST).read_text(encoding="utf-8"))["ids"][split])
    lines = Path(corpus.CORPUS).read_text(encoding="utf-8").splitlines()
    steps = [step for step in map(json.loads, lines) if step["id"] in ids]
    return [step for step in steps if not step["finances"]], len(ids) - len(steps)


def evaluate(predict: Predictor, steps: list[Step]) -> dict[str, SubsetSummary]:
    rows = []
    for step in steps:
        rows += score_step(step, predict(step["entree"]["articles"], step["amendements"]))
    return summarize(rows)


def table(results: dict[str, dict[str, SubsetSummary]]) -> str:
    """Un tableau par sous-ensemble d'articles, une ligne par prédicteur."""
    lines = ["Scores per article, mean (median), from 0 to 1: 1 = perfect."]
    header = "".join(f"{f'{metric} ({key})':>24}" for metric, key in SHOWN.items())
    for subset, summary in next(iter(results.values())).items():
        lines += ["", f"{TITLES.get(subset, subset)}: {summary.articles} articles"]
        lines.append(f"  {'predictor':<30}{header}")
        for name, result in results.items():
            cells = []
            for metric, key in SHOWN.items():
                stats = result[subset].scores.get(metric, {}).get(key)
                if stats is None or stats["mean"] is None:
                    cells.append("—")
                else:
                    cells.append(f"{stats['mean']:.3f} ({stats['median']:.2f})")
            lines.append(f"  {name:<30}" + "".join(f"{cell:>24}" for cell in cells))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate predictors on the corpus.")
    parser.add_argument("predictors", nargs="*", help="functions given as module:function")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--json", type=Path, help="also write every score to this file")
    args = parser.parse_args(argv)
    steps, missing = load_steps(args.split)
    print(f"Corpus {corpus.NAME}, split {args.split}: {len(steps)} steps, budget texts excluded")
    if missing:
        print(f"Warning: {missing} steps of the manifest are missing from the built corpus.")
    names = ["identity", *[name for name in args.predictors if name != "identity"]]
    results = {name: evaluate(load_predictor(name), steps) for name in names}
    print(table(results))
    if args.json:
        data = {
            name: {s: dataclasses.asdict(v) for s, v in r.items()} for name, r in results.items()
        }
        args.json.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
