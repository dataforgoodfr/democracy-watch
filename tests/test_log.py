"""Tests du logger du projet."""

from democracy_watch.log import get_logger


def test_logger_rattache_au_projet():
    assert get_logger("sync").name == "democracy_watch.sync"
    assert get_logger("democracy_watch.db").name == "democracy_watch.db"


def test_logger_configure_une_seule_fois():
    projet = get_logger("democracy_watch")
    avant = list(projet.handlers)

    get_logger("a")
    get_logger("b")

    assert projet.handlers == avant
