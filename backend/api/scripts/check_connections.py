"""Vérifie l'accès à Postgres et Meilisearch configurés dans l'environnement, en lecture seule.

Postgres : connexion en lecture seule puis `SELECT 1`. Meilisearch : `/health` (sans clé)
puis `/version`, qui exige une clé valide. N'affiche que l'hôte, jamais de secret.
Usage : `make check-connections` ; code de sortie 1 si une vérification échoue.
"""

import asyncio
import sys
from urllib.parse import urlsplit

import httpx

from backend.api.app.core.config import Settings
from democracy_watch.db import connect_async


def host_of(url: str) -> str:
    """Hôte et port d'une URL, sans identifiants."""
    parts = urlsplit(url)
    return f"{parts.hostname}:{parts.port}" if parts.port else str(parts.hostname)


async def check_postgres(config: Settings) -> str:
    """Ouvre une connexion en lecture seule et exécute `SELECT 1`."""
    if not config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL non défini")
    connection = await connect_async(
        dsn=config.DATABASE_URL,
        timeout=config.DATABASE_TIMEOUT,
        command_timeout=config.DATABASE_TIMEOUT,
    )
    try:
        await connection.fetchval("SELECT 1")
        version = connection.get_server_version()
    finally:
        await connection.close()
    return f"{host_of(config.DATABASE_URL)} (PostgreSQL {version.major}.{version.minor})"


async def check_meilisearch(
    config: Settings, transport: httpx.AsyncBaseTransport | None = None
) -> str:
    """Interroge `/health`, puis `/version` pour valider la clé."""
    if not config.MEILI_URL:
        raise RuntimeError("MEILI_URL non défini")
    key = config.MEILI_API_KEY
    async with httpx.AsyncClient(
        base_url=config.MEILI_URL,
        headers={"Authorization": f"Bearer {key.get_secret_value()}"} if key else {},
        timeout=config.MEILI_TIMEOUT,
        transport=transport,
    ) as client:
        (await client.get("/health")).raise_for_status()
        response = await client.get("/version")
        if response.status_code in (401, 403):
            raise RuntimeError(f"service joignable mais clé refusée ({response.status_code})")
        response.raise_for_status()
        version = response.json().get("pkgVersion", "?")
    return f"{host_of(config.MEILI_URL)} (Meilisearch {version})"


async def run(config: Settings) -> int:
    """Lance chaque vérification et affiche son résultat ; renvoie le code de sortie."""
    failed = False
    for name, check in (("Postgres", check_postgres), ("Meilisearch", check_meilisearch)):
        # Chaque échec est rapporté sans interrompre les autres vérifications.
        try:
            print(f"{name} : OK, {await check(config)}")
        except Exception as error:
            failed = True
            print(f"{name} : ÉCHEC, {type(error).__name__} : {error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run(Settings())))
