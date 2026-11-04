#!/usr/bin/env python3
"""Prépare une fois l'index Meilisearch des amendements : index, embedders, filtrables, triables,
champs cherchés, langue et mots vides.

À lancer avant le premier meili_sync.py sur un index (et à relancer sans risque : il ne fait
qu'ajouter ce qui manque, sans retirer ni modifier l'existant). Créer les embedders avant
d'envoyer les documents : chaque document n'est vectorisé qu'une fois, à son indexation.

Les embedders appellent l'API d'embedding depuis Meilisearch ; leur clé (HF_TOKEN) est stockée
dans les réglages de l'index. meili_sync.py n'en a donc pas besoin.

Variables : MEILI_URL, MEILI_KEY (droits indexes.create, settings.get/update, tasks.get),
HF_TOKEN pour l'embedder hf-*.

Exemples :
  python3 sync/meili_setup.py --dry-run
  python3 sync/meili_setup.py --index amendements-sync-test
"""

import argparse
import os

import meilisearch

from config import CONFIG

# Réglages requis et embedders : voir config.yaml (index_settings, embedders).
TASK_TIMEOUT_MS = CONFIG["meili"]["task_timeout_ms"]
TASK_INTERVAL_MS = CONFIG["meili"]["task_interval_ms"]
FILTERABLE = CONFIG["index_settings"]["filterable"]
SORTABLE = CONFIG["index_settings"]["sortable"]
SEARCHABLE = CONFIG["index_settings"]["searchable"]
LOCALIZED = CONFIG["index_settings"]["localized"]
STOP_WORDS = CONFIG["index_settings"]["stop_words"] or []
EMBEDDERS = {name: e["settings"] for name, e in CONFIG["embedders"].items()}
EMBEDDER_KEYS = {name: e["api_key_env"] for name, e in CONFIG["embedders"].items() if e.get("api_key_env")}


def wait(client, task):
    done = client.wait_for_task(task.task_uid, timeout_in_ms=TASK_TIMEOUT_MS, interval_in_ms=TASK_INTERVAL_MS)
    if done.status != "succeeded":
        raise SystemExit(f"Tâche {task.task_uid} {done.status} : {done.error}")


def missing_embedders(index):
    """Noms de EMBEDDERS absents de l'index (tous si l'index n'existe pas)."""
    try:
        current = index.get_settings().get("embedders") or {}
    except meilisearch.errors.MeilisearchApiError as err:
        if err.code == "index_not_found":
            return list(EMBEDDERS)
        raise
    return [name for name in EMBEDDERS if name not in current]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--index", default=CONFIG["defaults"]["index"])
    p.add_argument("--dry-run", action="store_true", help="Afficher ce qui manque sans écrire.")
    args = p.parse_args()

    client = meilisearch.Client(os.environ["MEILI_URL"].rstrip("/"), os.environ["MEILI_KEY"])
    index = client.index(args.index)
    try:
        settings = index.get_settings()
    except meilisearch.errors.MeilisearchApiError as err:
        if err.code != "index_not_found":
            raise
        print(f"Index '{args.index}' absent : création (clé primaire uid)")
        if args.dry_run:
            settings = {}
        else:
            wait(client, client.create_index(args.index, {"primaryKey": "uid"}))
            settings = index.get_settings()

    update = {}
    for key, wanted in (("filterableAttributes", FILTERABLE), ("sortableAttributes", SORTABLE)):
        current = settings.get(key) or []
        missing = [attr for attr in wanted if attr not in current]
        if missing:
            print(f"  {key} : ajout {missing}")
            update[key] = current + missing
    # "*" (défaut) = tout est cherché : on le remplace ; une liste déjà choisie n'est pas touchée.
    if (settings.get("searchableAttributes") or ["*"]) == ["*"]:
        print(f"  searchableAttributes : {SEARCHABLE}")
        update["searchableAttributes"] = SEARCHABLE
    if not settings.get("localizedAttributes"):
        print(f"  localizedAttributes : {LOCALIZED}")
        update["localizedAttributes"] = LOCALIZED
    current = settings.get("stopWords") or []
    if missing := [w for w in STOP_WORDS if w not in current]:
        print(f"  stopWords : ajout de {len(missing)} mots")
        update["stopWords"] = current + missing
    embedders = {}
    for name in EMBEDDERS:
        if name in (settings.get("embedders") or {}):
            continue
        key = os.environ.get(EMBEDDER_KEYS[name]) if EMBEDDER_KEYS.get(name) else None
        if EMBEDDER_KEYS.get(name) and not key and not args.dry_run:
            raise SystemExit(f"Clé manquante pour l'embedder {name} : {EMBEDDER_KEYS[name]}.")
        embedders[name] = {**EMBEDDERS[name], **({"apiKey": key} if key else {})}
    if embedders:
        print(f"  embedders : ajout {list(embedders)} (vectorise les documents déjà présents)")
        update["embedders"] = embedders

    if not update:
        print(f"Index '{args.index}' : rien à ajouter.")
        return
    if args.dry_run:
        return
    wait(client, index.update_settings(update))
    print("Terminé.")


if __name__ == "__main__":
    main()
