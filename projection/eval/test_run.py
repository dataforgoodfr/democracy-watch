"""Lancement de l'évaluation, sur un petit corpus écrit dans tmp_path (sans réseau)."""

import json

import pytest

from projection.eval import corpus, run
from projection.eval.algorithms import Algorithm


def step(id_, split, finances=False):
    articles = [{"numero": "PREMIER", "lignes": ["Texte déposé."], "supprime": False}]
    sortie = [{"numero": "PREMIER", "lignes": ["Texte modifié."], "supprime": False}]
    return {
        "id": id_,
        "split": split,
        "finances": finances,
        "entree": {"ref": "B1", "articles": articles},
        "sortie": {"ref": "BTC1", "articles": sortie},
        "amendements": [],
    }


@pytest.fixture
def built(monkeypatch, tmp_path):
    """Corpus : D1 (dev), D2 (dev, budgétaire), D3 (absent du manifeste), D4 (test)."""
    steps = [step("D1", "dev"), step("D2", "dev", True), step("D3", "dev"), step("D4", "test")]
    (tmp_path / "corpus.jsonl").write_text("".join(json.dumps(s) + "\n" for s in steps))
    ids = {"dev": ["D1", "D2", "D5"], "test": ["D4"]}  # D5 : dans le manifeste, pas construit
    (tmp_path / "manifeste.json").write_text(json.dumps({"ids": ids}))
    monkeypatch.setattr(corpus, "CORPUS", tmp_path / "corpus.jsonl")
    monkeypatch.setattr(corpus, "MANIFEST", tmp_path / "manifeste.json")
    return tmp_path


def test_load_steps(built):
    steps, missing = run.load_steps("dev")
    assert [s["id"] for s in steps] == ["D1"] and missing == 1


class Deleting(Algorithm):
    """Défini hors du paquet algorithms : pas lancé par défaut."""

    name = "deleting"

    def predict(self, entree, amendements):
        return []


def test_select():
    assert [p.name for p in run.select([])] == ["identity"]
    assert [p.name for p in run.select(["identity", "identity"])] == ["identity"]
    with pytest.raises(SystemExit, match="Unknown algorithms"):
        run.select(["deleting"])


def test_main(built, capsys):
    run.main(["--json", str(built / "results.json")])
    out = capsys.readouterr().out
    assert "1 steps" in out and "missing from the built corpus" in out
    results = json.loads((built / "results.json").read_text())
    assert list(results) == ["identity"]
    assert results["identity"]["changed"]["scores"]["identical"]["identical"]["mean"] == 0.0
