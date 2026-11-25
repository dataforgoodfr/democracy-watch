"""Lance l'évaluation : fait tourner les algorithmes sur le corpus et affiche leurs scores.

Usage, depuis la racine du repo, une fois le corpus construit (projection/eval/corpus.py) :
    uv run python -m projection.eval.run                  # tous les algorithmes
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
from projection.eval.algorithms import Algorithm, Identity, all_algorithms
from projection.eval.formats import Step, SubsetSummary
from projection.eval.metrics import score_step, summarize

# Colonnes du tableau : titre → (métrique, score). Le JSON contient tous les scores.
SHOWN = {
    "identical": ("identical", "identical"),
    "presence": ("presence", "presence"),
    "words f1": ("words", "f1"),
}
TITLES = {
    "changed": "Articles with changes",
    "all": "All articles",
    "unchanged": "Articles without changes",
}


def select(names: list[str]) -> list[Algorithm]:
    """Les algorithmes nommés, tous si aucun, toujours précédés de la référence."""
    available = {algorithm.name: algorithm for algorithm in all_algorithms()}
    unknown = [name for name in names if name not in available]
    if unknown:
        raise SystemExit(f"Unknown algorithms: {unknown}. Available: {sorted(available)}")
    chosen = dict.fromkeys([Identity.name, *(names or available)])
    return [available[name] for name in chosen]


def load_steps(split: str) -> tuple[list[Step], int]:
    """Les étapes du manifeste pour ce split, hors textes budgétaires, et le nombre d'étapes du
    manifeste absentes du corpus construit."""
    ids = set(json.loads(Path(corpus.MANIFEST).read_text(encoding="utf-8"))["ids"][split])
    lines = Path(corpus.CORPUS).read_text(encoding="utf-8").splitlines()
    steps = [step for step in map(json.loads, lines) if step["id"] in ids]
    return [step for step in steps if not step["finances"]], len(ids) - len(steps)


def evaluate(algorithm: Algorithm, steps: list[Step]) -> dict[str, SubsetSummary]:
    rows = []
    for step in steps:
        prediction = algorithm.predict(step["entree"]["articles"], step["amendements"])
        rows += score_step(step, prediction)
    return summarize(rows)


def table(results: dict[str, dict[str, SubsetSummary]]) -> str:
    """Un tableau par sous-ensemble d'articles, une ligne par algorithme."""
    lines = ["Mean score per article, from 0 to 1, where 1 is perfect."]
    header = "".join(f"{title:>12}" for title in SHOWN)
    for subset, summary in next(iter(results.values())).items():
        lines += ["", f"{TITLES.get(subset, subset)}: {summary.articles} articles"]
        lines.append(f"  {'algorithm':<20}{header}")
        for name, result in results.items():
            cells = []
            for metric, key in SHOWN.values():
                stats = result[subset].scores.get(metric, {}).get(key)
                if stats is None or stats["mean"] is None:
                    cells.append("—")
                else:
                    cells.append(f"{stats['mean']:.3f}")
            lines.append(f"  {name:<20}" + "".join(f"{cell:>12}" for cell in cells))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate algorithms on the corpus.")
    parser.add_argument("algorithms", nargs="*", help="algorithm names, all by default")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--json", type=Path, help="also write every score to this file")
    args = parser.parse_args(argv)
    algorithms = select(args.algorithms)
    steps, missing = load_steps(args.split)
    print(f"Corpus {corpus.NAME}, split {args.split}: {len(steps)} steps, budget texts excluded")
    if missing:
        print(f"Warning: {missing} steps of the manifest are missing from the built corpus.")
    results = {algorithm.name: evaluate(algorithm, steps) for algorithm in algorithms}
    print(table(results))
    if args.json:
        data = {
            name: {s: dataclasses.asdict(v) for s, v in r.items()} for name, r in results.items()
        }
        args.json.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
