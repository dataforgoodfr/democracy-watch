"""Lance l'évaluation : fait tourner les prédicteurs sur le corpus et affiche leurs scores.

Usage, depuis la racine du repo, une fois le corpus construit (projection/eval/corpus.py) :
    uv run python -m projection.eval.run                  # tous les prédicteurs
    uv run python -m projection.eval.run identity         # ceux nommés
    uv run python -m projection.eval.run --split test --json results.json

La référence « identity » (recopier l'entrée) est toujours lancée : c'est le score à battre.
Seules les étapes du manifeste sont évaluées (un corpus reconstruit plus tard en contient de
nouvelles), sans les textes budgétaires (PLF, PLFSS), comme le prévoit la RFC.
"""

import argparse
import dataclasses
import json
from pathlib import Path

from projection.eval import corpus
from projection.eval.formats import Step, SubsetSummary
from projection.eval.metrics import score_step, summarize
from projection.eval.predictors import Identity, Predictor, all_predictors

# Score affiché pour chaque métrique ; le JSON les contient tous.
SHOWN = {"identical": "identical", "presence": "presence", "words": "f1"}
TITLES = {
    "changed": "Articles the official text changes",
    "all": "All articles",
    "unchanged": "Articles the official text leaves as they were",
}


def select(names: list[str]) -> list[Predictor]:
    """Les prédicteurs nommés, tous si aucun, toujours précédés de la référence."""
    available = {predictor.name: predictor for predictor in all_predictors()}
    unknown = [name for name in names if name not in available]
    if unknown:
        raise SystemExit(f"Unknown predictors: {unknown}. Available: {sorted(available)}")
    chosen = dict.fromkeys([Identity.name, *(names or available)])
    return [available[name] for name in chosen]


def load_steps(split: str) -> tuple[list[Step], int]:
    """Les étapes du manifeste pour ce split, hors textes budgétaires, et le nombre d'étapes du
    manifeste absentes du corpus construit."""
    ids = set(json.loads(Path(corpus.MANIFEST).read_text(encoding="utf-8"))["ids"][split])
    lines = Path(corpus.CORPUS).read_text(encoding="utf-8").splitlines()
    steps = [step for step in map(json.loads, lines) if step["id"] in ids]
    return [step for step in steps if not step["finances"]], len(ids) - len(steps)


def evaluate(predictor: Predictor, steps: list[Step]) -> dict[str, SubsetSummary]:
    rows = []
    for step in steps:
        prediction = predictor.predict(step["entree"]["articles"], step["amendements"])
        rows += score_step(step, prediction)
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
    parser.add_argument("predictors", nargs="*", help="predictor names (default: all)")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--json", type=Path, help="also write every score to this file")
    args = parser.parse_args(argv)
    predictors = select(args.predictors)
    steps, missing = load_steps(args.split)
    print(f"Corpus {corpus.NAME}, split {args.split}: {len(steps)} steps, budget texts excluded")
    if missing:
        print(f"Warning: {missing} steps of the manifest are missing from the built corpus.")
    results = {predictor.name: evaluate(predictor, steps) for predictor in predictors}
    print(table(results))
    if args.json:
        data = {
            name: {s: dataclasses.asdict(v) for s, v in r.items()} for name, r in results.items()
        }
        args.json.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
