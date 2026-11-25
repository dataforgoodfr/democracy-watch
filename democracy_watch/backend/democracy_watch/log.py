"""
from democracy_watch.log import get_logger

log = get_logger(__name__)
log.info("%s amendements lus", count)
"""

import logging
import os

FORMAT = "%(asctime)s %(levelname)-7s %(name)s : %(message)s"
DATEFMT = "%H:%M:%S"


def get_logger(name):
    """Logger `name`, rattaché au logger du projet (configuré au premier appel)."""
    root = logging.getLogger("democracy_watch")
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(FORMAT, DATEFMT))
        root.addHandler(handler)
        root.setLevel(os.environ.get("DW_LOG_LEVEL", "INFO").upper())
        root.propagate = False  # pas de doublon si l'appelant configure aussi logging
    if name != "democracy_watch" and not name.startswith("democracy_watch."):
        name = f"democracy_watch.{name}"
    return logging.getLogger(name)
