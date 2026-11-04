"""Charge sync/config.yaml (ou le fichier désigné par SYNC_CONFIG)."""

import os
from pathlib import Path

import yaml

SYNC_DIR = Path(__file__).resolve().parent
REPO_DIR = SYNC_DIR.parent

with open(os.environ.get("SYNC_CONFIG", SYNC_DIR / "config.yaml"), encoding="utf-8") as fh:
    CONFIG = yaml.safe_load(fh)
