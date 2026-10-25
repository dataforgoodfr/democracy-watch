"""Lecture des données législatives dans Postgres (copie du dump CLAIR).

Tables : dossiers_legislatifs, dossier_commissions, commissions, textes_articles, amendements,
"_AmendementCosignataires" (jointure Prisma : "A" = amendement, "B" = parlementaire).
"""

from typing import Protocol


class Repository(Protocol):
    """Accès aux données utilisé par les routes (Postgres en production, doublure en test)."""

    def get_dossier(self, uid): ...

    def list_articles(self, texte_ref): ...

    def get_amendement(self, uid): ...

    def list_amendements(self, texte_ref, article=None, limit=500): ...

    def ping(self): ...


DOSSIER_SQL = """
SELECT d.id, d.uid, d.legislature, d.titre, d.titre_court, d.procedure_libelle, d.etat,
       d.date_depot, d.date_adoption, d.url_an, d.url_senat, d.url_legifrance
FROM dossiers_legislatifs d
WHERE d.uid = %s
"""

DOSSIER_COMMISSIONS_SQL = """
SELECT c.uid, c.slug, c.nom, c.nom_court, dc.role
FROM dossier_commissions dc JOIN commissions c ON c.id = dc.commission_id
WHERE dc.dossier_id = %s
ORDER BY dc.role DESC, c.nom
"""

# Textes d'un dossier : références vues dans ses articles et ses amendements.
DOSSIER_TEXTES_SQL = """
SELECT texte_ref, count(*) AS articles FROM textes_articles WHERE dossier_id = %s GROUP BY texte_ref
UNION
SELECT texte_ref, 0 FROM amendements
WHERE dossier_id = %s AND texte_ref IS NOT NULL
  AND texte_ref NOT IN (SELECT texte_ref FROM textes_articles WHERE dossier_id = %s)
GROUP BY texte_ref
ORDER BY texte_ref
"""

ARTICLES_SQL = """
SELECT texte_ref, numero, libelle, ordre, contenu, source_url
FROM textes_articles
WHERE texte_ref = %s
ORDER BY ordre
"""

AMENDEMENT_COLUMNS = """
a.uid, a.numero, a.legislature, a.chambre, a.auteur_libelle, a.groupe_ref, a.texte_ref,
a.article_vise, a.dispositif, a.expose_sommaire, a.sort, a.date_depot, a.date_sort,
a.source_url, d.uid AS dossier_uid,
(SELECT count(*) FROM "_AmendementCosignataires" c WHERE c."A" = a.id) AS cosignataires
"""

AMENDEMENT_SQL = f"""
SELECT {AMENDEMENT_COLUMNS}
FROM amendements a LEFT JOIN dossiers_legislatifs d ON d.id = a.dossier_id
WHERE a.uid = %s
"""

AMENDEMENTS_SQL = f"""
SELECT {AMENDEMENT_COLUMNS}
FROM amendements a LEFT JOIN dossiers_legislatifs d ON d.id = a.dossier_id
WHERE a.texte_ref = %s AND (%s::text IS NULL OR a.article_vise = %s)
ORDER BY a.numero_ordre NULLS LAST, a.numero
LIMIT %s
"""


class PostgresRepository:
    """Implémentation Postgres. `conn` : connexion psycopg avec des lignes en dict."""

    def __init__(self, conn):
        self._conn = conn

    def _one(self, sql, params):
        return self._conn.execute(sql, params).fetchone()

    def _all(self, sql, params):
        return self._conn.execute(sql, params).fetchall()

    def get_dossier(self, uid):
        dossier = self._one(DOSSIER_SQL, (uid,))
        if dossier is None:
            return None
        dossier_id = dossier.pop("id")
        dossier["commissions"] = self._all(DOSSIER_COMMISSIONS_SQL, (dossier_id,))
        dossier["textes"] = self._all(
            DOSSIER_TEXTES_SQL, (dossier_id, dossier_id, dossier_id)
        )
        return dossier

    def list_articles(self, texte_ref):
        return self._all(ARTICLES_SQL, (texte_ref,))

    def get_amendement(self, uid):
        return self._one(AMENDEMENT_SQL, (uid,))

    def list_amendements(self, texte_ref, article=None, limit=500):
        return self._all(AMENDEMENTS_SQL, (texte_ref, article, article, limit))

    def ping(self):
        return self._one("SELECT 1 AS ok", ()) is not None
