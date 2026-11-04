#!/usr/bin/env python3
"""Synchronise l'index Meilisearch des amendements avec la base Postgres (dump CLAIR).

Plan : plans/meili_sync.md.
  - par défaut (quotidien) : envoie (PUT partiel) les amendements dont updated_at >= filigrane - 1 jour,
    le filigrane étant le plus grand updated_at déjà indexé. Index vide, ou base sans updated_at :
    tout est envoyé.
  - --reconcile (hebdomadaire) : tout envoyer, puis supprimer de l'index les uid absents de la base.

Réglages (embedders, filtrables, triables) : créés une fois par sync/meili_setup.py, à lancer avant
la première synchro d'un index. Meilisearch vectorise ensuite lui-même les documents nouveaux ou dont
le texte change.

Variables : MEILI_URL, MEILI_KEY (clé limitée à l'index, pas la master key), et pour Postgres
soit DATABASE_URL, soit les variables standard PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE, PGSSLMODE.
Dépendances : pip install -r sync/requirements.txt

Exemples :
  python3 sync/meili_sync.py --dry-run
  python3 sync/meili_sync.py --index amendements-sync-test
  python3 sync/meili_sync.py --reconcile
"""

import argparse
import json
import os
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import meilisearch
import psycopg
from psycopg.rows import dict_row

from config import CONFIG
from meili_setup import missing_embedders

SQL = (Path(__file__).parent / "amendements.sql").read_text(encoding="utf-8")
MARGIN = timedelta(days=CONFIG["sync"]["margin_days"])
# Taille max d'une requête : le proxy devant l'instance hébergée renvoie 413 au-delà de sa limite.
MAX_BATCH_BYTES = int(os.environ.get("MEILI_MAX_BATCH_BYTES", CONFIG["meili"]["max_batch_bytes"]))
TASK_TIMEOUT_MS = CONFIG["meili"]["task_timeout_ms"]
TASK_INTERVAL_MS = CONFIG["meili"]["task_interval_ms"]
PAGE_SIZE = CONFIG["meili"]["documents_page_size"]
MAX_DELETE_RATIO = CONFIG["sync"]["max_delete_ratio"]
RETRY = CONFIG["sync"]["retry"]
MAX_RETRIES = RETRY["max_retries"]
LOTS_EN_PARALLELE = CONFIG["sync"]["lots_en_parallele"]

def batches(docs):
    """Lots d'au plus MAX_BATCH_BYTES de JSON (un document plus gros part seul)."""
    batch, size = [], 0
    for doc in docs:
        n = len(json.dumps(doc)) + 2  # même encodage que le client (ASCII échappé) + séparateur ", "
        if batch and size + n > MAX_BATCH_BYTES:
            yield batch
            batch, size = [], 0
        batch.append(doc)
        size += n
    if batch:
        yield batch


def wait(client, tasks):
    """Attend les tâches ; sort en erreur si l'une échoue (→ alerte du job)."""
    for task in tasks:
        done = client.wait_for_task(task.task_uid, timeout_in_ms=TASK_TIMEOUT_MS, interval_in_ms=TASK_INTERVAL_MS)
        if done.status != "succeeded":
            raise SystemExit(f"Tâche {task.task_uid} {done.status} : {done.error}")


def embedder_requests(client, task_uids):
    """Requêtes d'embedding ({total, failed}) des lots Meilisearch qui ont traité ces tâches."""
    batch_uids = {client.http.get(f"tasks/{uid}").get("batchUid") for uid in task_uids} - {None}
    total = failed = 0
    for uid in batch_uids:
        req = client.http.get(f"batches/{uid}")["stats"].get("embedderRequests") or {}
        total, failed = total + req.get("total", 0), failed + req.get("failed", 0)
    return total, failed


def retry_delay(attempt):
    """Secondes d'attente avant de renvoyer un lot dont l'embedding a échoué (attempt = 1, 2…), ou None pour abandonner."""
    if attempt <= MAX_RETRIES:
        return 60*attempt
    else:
        return None


def send(client, index, docs):
    """Envoie les lots par groupes de LOTS_EN_PARALLELE, chaque groupe attendu avant le suivant.

    Meilisearch regroupe toutes les tâches en file dans un seul lot, qui échoue en entier à la première
    erreur d'embedding : envoyés d'un coup, 100 000 documents saturent l'endpoint et sont tous perdus.
    Un groupe de K lots borne la charge et la perte, tout en donnant à Meilisearch assez de documents pour
    paralléliser les requêtes d'embedding. Les groupes déjà indexés le restent si le script s'arrête.
    """
    lots = list(batches(docs))
    groups = [list(range(i, min(i + LOTS_EN_PARALLELE, len(lots)))) for i in range(0, len(lots), LOTS_EN_PARALLELE)]
    for g, group in enumerate(groups, 1):
        pending, attempt = group, 0
        while pending:
            tasks = [(i, index.update_documents(lots[i], primary_key="uid")) for i in pending]
            failed = []
            for i, task in tasks:
                done = client.wait_for_task(task.task_uid, timeout_in_ms=TASK_TIMEOUT_MS, interval_in_ms=TASK_INTERVAL_MS)
                if done.status == "succeeded":
                    continue
                if (done.error or {}).get("code") != "vector_embedding_error":
                    raise SystemExit(f"Tâche {task.task_uid} {done.status} : {done.error}")
                failed.append(i)
            total, nb_failed = embedder_requests(client, [task.task_uid for _, task in tasks])
            print(f"  groupe {g}/{len(groups)} (lots {pending[0] + 1}-{pending[-1] + 1}/{len(lots)}, "
                  f"{sum(len(lots[i]) for i in pending)} docs) : {len(pending) - len(failed)}/{len(pending)} lots indexés, "
                  f"embeddings {total} (échecs {nb_failed})")
            pending = failed
            if not pending:
                break
            attempt += 1
            delay = retry_delay(attempt)
            if delay is None:
                raise SystemExit(f"Groupe {g}/{len(groups)} : embedding en échec après {attempt} essais. "
                                 f"Les groupes précédents sont indexés ; relancer reprend sans les ré-embedder.")
            print(f"    nouvel essai de {len(pending)} lots dans {delay:.0f} s")
            time.sleep(delay)
        if RETRY["pause_seconds"] and g < len(groups):
            time.sleep(RETRY["pause_seconds"])

def watermark(index):
    """Plus grand updated_at indexé, ou None (index absent, ou jamais synchronisé)."""
    try:
        hits = index.search("", {"sort": ["updated_at:desc"], "filter": "updated_at EXISTS", "limit": 1})["hits"]
    except meilisearch.errors.MeilisearchApiError as err:
        # Index absent, ou updated_at pas encore triable/filtrable : synchro complète.
        # Toute autre erreur (clé invalide…) doit arrêter le script, pas passer pour « pas de filigrane ».
        if err.code in ("index_not_found", "invalid_search_sort", "invalid_search_filter"):
            return None
        raise
    return datetime.fromtimestamp(hits[0]["updated_at"], timezone.utc) if hits else None


def index_uids(index, page=PAGE_SIZE):
    uids, offset = set(), 0
    while True:
        res = index.get_documents({"fields": ["uid"], "limit": page, "offset": offset})
        uids.update(doc.uid for doc in res.results)
        offset += page
        if offset >= res.total:
            return uids


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--index", default=CONFIG["defaults"]["index"])
    p.add_argument("--legislatures", type=int, nargs="+", default=CONFIG["defaults"]["legislatures"])
    p.add_argument("--reconcile", action="store_true", help="Tout envoyer et supprimer les absents de la base.")
    p.add_argument("--dry-run", action="store_true", help="Compter sans écrire.")
    p.add_argument("--limit", type=int, help="Test : n'envoyer que N amendements tirés au hasard (synchro complète, sans suppression).")
    args = p.parse_args()

    client = meilisearch.Client(os.environ["MEILI_URL"].rstrip("/"), os.environ["MEILI_KEY"])
    index = client.index(args.index)
    missing = missing_embedders(index)
    if missing:
        raise SystemExit(f"Index '{args.index}' : embedders absents {missing}. Lancer d'abord sync/meili_setup.py --index {args.index}.")
    if args.limit and args.reconcile:
        raise SystemExit("--limit et --reconcile sont incompatibles (suppression des absents).")
    mark = None if args.reconcile or args.limit else watermark(index)
    since = mark - MARGIN if mark else None
    print(f"Index '{args.index}' : {f'depuis {since:%Y-%m-%d %H:%M} UTC' if since else 'synchro complète'}")

    # Chaîne vide : libpq lit PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE, PGSSLMODE.
    with psycopg.connect(os.environ.get("DATABASE_URL", ""), row_factory=dict_row) as conn:
        docs = conn.execute(SQL, {"legislatures": args.legislatures, "since": since}).fetchall()
    for doc in docs:
        if doc["updated_at"] is None:  # base sans updated_at : ne pas fausser le filigrane
            del doc["updated_at"]
    if args.limit:
        docs = random.Random(0).sample(docs, min(args.limit, len(docs)))  # échantillon fixe : même tirage en --dry-run
        print("  uids :", ", ".join(doc["uid"] for doc in docs))
    print(f"  {len(docs)} amendements à envoyer")
    if since is None and not docs:
        raise SystemExit("Garde-fou : la base ne renvoie aucun amendement (dump vide ?).")

    stale = []
    if args.reconcile:
        indexed = index_uids(index)
        stale = sorted(indexed - {doc["uid"] for doc in docs})
        print(f"  {len(stale)} documents de l'index absents de la base")
        if indexed and len(stale) / len(indexed) > MAX_DELETE_RATIO:
            raise SystemExit(f"Garde-fou : plus de {MAX_DELETE_RATIO:.0%} de l'index à supprimer. Rien n'a été écrit.")

    if args.dry_run:
        return
    send(client, index, docs)
    if stale:
        wait(client, [index.delete_documents(stale)])
    print("Terminé.")


if __name__ == "__main__":
    main()
