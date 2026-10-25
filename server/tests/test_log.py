import logging

from democracy_watch.log import get_logger


def test_logger_is_attached_to_project_namespace():
    assert get_logger("ingestion").name == "democracy_watch.ingestion"


def test_project_logger_keeps_its_name():
    assert get_logger("democracy_watch.db").name == "democracy_watch.db"


def test_handler_is_configured_once():
    get_logger("a")
    get_logger("b")
    root = logging.getLogger("democracy_watch")
    # pytest ajoute ses propres handlers de capture : on ne compte que le nôtre
    ours = [h for h in root.handlers if type(h) is logging.StreamHandler]
    assert len(ours) == 1
    assert root.propagate is False
