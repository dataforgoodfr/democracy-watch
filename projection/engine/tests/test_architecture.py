"""Règle de dépendance du moteur : le cœur ne connaît ni Lark ni les sources."""

import ast
import pathlib

import pytest

ENGINE = pathlib.Path(__file__).parent.parent

# Pour chaque couche : ce qu'elle n'a pas le droit d'importer.
FORBIDDEN = {
    "domain": ("lark", "datasources", "projection", "engine.actions", "engine.reading"),
    "actions": ("lark", "datasources", "projection", "engine.reading", "engine.usecases"),
    "reading": ("datasources", "projection", "engine.usecases", "engine.adapters"),
    "usecases": ("lark", "datasources", "projection", "engine.adapters"),
}


def imports(path):
    """Les modules importés par un fichier (hors `if TYPE_CHECKING`)."""
    names = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def violations(layer):
    found = []
    for path in sorted((ENGINE / layer).glob("*.py")):
        for name in imports(path):
            for banned in FORBIDDEN[layer]:
                if name == banned or name.startswith(banned + "."):
                    found.append(f"{path.relative_to(ENGINE)} importe {name}")
    return found


@pytest.mark.parametrize("layer", sorted(FORBIDDEN))
def test_layer_does_not_import_what_it_must_not(layer):
    assert violations(layer) == []


def test_layers_exist():
    assert all((ENGINE / layer).is_dir() for layer in FORBIDDEN)
