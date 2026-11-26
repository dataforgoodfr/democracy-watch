"""Vérifie l'accès aux données DuckDB et à Meilisearch configurés, en lecture seule.

Données : ouverture de DATA_PATH en lecture seule puis décompte des dossiers. Meilisearch :
`/health` (sans clé) puis `/version`, qui exige une clé valide. N'affiche ni clé ni secret.
Usage : `make check-connections` ; code de sortie 1 si une vérification échoue.
"""

import asyncio
import sys
from urllib.parse import urlsplit

import duckdb
import httpx

from backend.api.app.core.config import Settings
from backend.api.app.core.database import CATALOG, open_database


def host_of(url: str) -> str:
    """Hôte et port d'une URL, sans identifiants."""
    parts = urlsplit(url)
    return f"{parts.hostname}:{parts.port}" if parts.port else str(parts.hostname)


def check_data(config: Settings) -> str:
    """Ouvre DATA_PATH en lecture seule et compte les dossiers."""
    connection = open_database(config)
    try:
        connection.execute(f"USE {CATALOG}")
        row = connection.execute("SELECT count(*) FROM dossiers").fetchone()
    finally:
        connection.close()
    count = row[0] if row else 0
    return f"{config.DATA_PATH} (DuckDB {duckdb.__version__}, {count} dossiers)"


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
    checks = (
        ("Données", lambda config: asyncio.to_thread(check_data, config)),
        ("Meilisearch", check_meilisearch),
    )
    for name, check in checks:
        # Chaque échec est rapporté sans interrompre les autres vérifications.
        try:
            print(f"{name} : OK, {await check(config)}")
        except Exception as error:
            failed = True
            print(f"{name} : ÉCHEC, {type(error).__name__} : {error}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run(Settings())))
