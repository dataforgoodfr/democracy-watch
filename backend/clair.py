"""Adaptateur CLAIR : les lectures du serveur dans la copie Postgres du dump CLAIR.

Les noms de colonnes CLAIR ne sortent pas de ce module (ils deviennent les clés des dicts).
"""

from democracy_watch.db import connect


def ping():
    """Vérifie que Postgres répond."""
    with connect() as conn:
        conn.execute("SELECT 1")


def dossier(uid):
    """Dossier législatif et la liste de ses textes (références), ou None s'il est inconnu."""
    with connect() as conn:
        row = conn.execute(
            """SELECT id, uid, legislature, titre, titre_court, procedure_libelle, etat, date_depot,
                      date_adoption, url_an, url_senat, url_legifrance
               FROM dossiers_legislatifs WHERE uid = %s""",
            (uid,),
        ).fetchone()
        if row is None:
            return None
        textes = conn.execute(
            """SELECT DISTINCT texte_ref FROM textes_articles
               WHERE dossier_id = %s ORDER BY texte_ref""",
            (row.pop("id"),),
        ).fetchall()
    return row | {"textes": [t["texte_ref"] for t in textes]}


def articles(texte_ref):
    """Articles d'un texte dans l'ordre du texte (liste vide si le texte est inconnu)."""
    with connect() as conn:
        return conn.execute(
            """SELECT numero, libelle, ordre, contenu FROM textes_articles
               WHERE texte_ref = %s ORDER BY ordre""",
            (texte_ref,),
        ).fetchall()


def amendement(uid):
    """Un amendement, ou None s'il est inconnu."""
    with connect() as conn:
        return conn.execute(
            """SELECT uid, numero, legislature, chambre, texte_ref, article_vise, alinea,
                      dispositif, expose_sommaire, auteur_libelle, auteur_ref, groupe_ref, sort,
                      date_depot, date_sort, amendement_parent_ref, source_url
               FROM amendements WHERE uid = %s""",
            (uid,),
        ).fetchone()
