"""Tests de sql/articles.sql (lancer avec : pytest) sur un petit extrait DuckDB en mémoire.

On recrée une table `tisseuse.assemblee_text_search` minimale (seulement les colonnes
utilisées), on y met quelques lignes, puis on exécute le fichier SQL.
"""

from pathlib import Path

import duckdb

SQL = (Path(__file__).parent.parent / "sql" / "articles.sql").read_text(encoding="utf-8")


def construire(lignes):
    """Crée la mini-base et lance articles.sql.

    lignes : liste de dicts.
    Clés facultatives : item_kind, legislature, numero, libelle, uid, item_id.
    """
    con = duckdb.connect()  # base en mémoire : rien n'est écrit sur disque
    con.execute("CREATE SCHEMA tisseuse")
    con.execute("""CREATE TABLE tisseuse.assemblee_text_search(
        document_uid VARCHAR, item_id VARCHAR, item_kind VARCHAR, item_label VARCHAR,
        article_number VARCHAR, content VARCHAR, legislature INTEGER)""")
    for i, ligne in enumerate(lignes):
        con.execute(
            "INSERT INTO tisseuse.assemblee_text_search VALUES (?,?,?,?,?,?,?)",
            [
                ligne.get("uid", "DOC1"),
                ligne.get("item_id", f"_TocArt{i}"),
                ligne.get("item_kind", "article"),
                ligne.get("libelle", f"Article {i}"),
                ligne.get("numero", str(i)),
                ligne["content"],
                ligne.get("legislature", 17),
            ],
        )
    con.execute(SQL)
    return con


def alineas_de(contenu):
    """Renvoie [(n° d'alinéa, texte), ...].

    Si l'article n'a pas d'alinéas : [(None, texte entier)].
    """
    con = construire([{"content": contenu}])
    liste = con.execute("SELECT alineas FROM articles").fetchone()[0]
    if liste is None:
        return [(None, contenu)]
    return [(i + 1, texte) for i, texte in enumerate(liste)]


def numeros(res):
    """Ne garde que les numéros d'alinéa : [(1, '…'), (2, '…')] -> [1, 2]."""
    return [a for a, _ in res]


# ---------- découpage en alinéas ----------


def test_cas_nominal():
    """« 1L'Assemblée…, 2Vu… » donne 2 alinéas propres, sans les numéros (exemple de la tâche)."""
    assert alineas_de("1L'Assemblée nationale, 2Vu l'article 3 du code.") == [
        (1, "L'Assemblée nationale,"),
        (2, "Vu l'article 3 du code."),
    ]


def test_reference_code_non_decoupee():  # « L. 253-7 »
    """« L. 253‑7 » n'est pas coupé."""
    res = alineas_de("1Vu l'article L. 253‑7 du code rural. 2Suite.")
    assert numeros(res) == [1, 2] and "L. 253‑7" in res[0][1]


def test_annee_non_decoupee():  # « 2026 »
    """« 2026, » n'est pas coupé."""
    res = alineas_de("1Applicable en 2026, sauf exception. 2Fin.")
    assert numeros(res) == [1, 2] and "2026," in res[0][1]


def test_ordinaux_non_decoupes():  # « 1er », « 2e »
    """« 1er » et « 2e » ne sont pas pris pour des alinéas."""
    res = alineas_de("1Le 1er janvier, le 2e alinéa s'applique. 2Fin.")
    assert numeros(res) == [1, 2] and "1er" in res[0][1] and "2e" in res[0][1]


def test_faux_numero_hors_sequence_recolle():  # « 12Faux » alors qu'on attend le 2
    """« 12Faux », alors qu'on attend 2, reste dans l'alinéa 1."""
    assert alineas_de("1Alinéa un 12Faux marqueur. 2Alinéa deux") == [
        (1, "Alinéa un 12Faux marqueur."),
        (2, "Alinéa deux"),
    ]


def test_liste_collee_au_numero():  # cas réel : « 181. Affirme… » = alinéa 18 + « 1. »
    """« 181. Affirme » donne l'alinéa 18, qui commence par « 1. »."""
    debut = " ".join(f"{i}Vu le texte {i}," for i in range(1, 18))
    res = alineas_de(debut + " 181. Affirme que C ; 192. Souligne que D ; 203. Appelle E.")
    assert numeros(res) == list(range(1, 21))
    assert res[17] == (18, "1. Affirme que C ;")


def test_puces_degre_collees():  # cas réel : « 21° Au 2° de l'article… »
    """« 21° Au 2° » donne l'alinéa 2, qui commence par « 1° »."""
    res = alineas_de(
        "1I. – Le code civil est ainsi modifié : 21° Au 2° de l’article 255, sont insérés "
        "les mots : « X » ; 32° Au deuxième alinéa, sont insérés : « Y ». "
        "4II. – Le code pénal est ainsi modifié : 51° A (nouveau) Au 1° du II."
    )
    assert numeros(res) == [1, 2, 3, 4, 5]
    assert res[1][1].startswith("1° Au 2° de l’article 255")


def test_tirets_apres_numero():  # cas réel : « 3– l'organisation… »
    """« 3– l'organisation » donne l'alinéa 3, qui commence par « – »."""
    res = alineas_de(
        "1En application des articles 137, il est créé une commission. "
        "2La commission examine : 3– l’organisation ; 4– les critères ; 5– les moyens."
    )
    assert numeros(res) == [1, 2, 3, 4, 5] and res[2][1] == "– l’organisation ;"


def test_guillemets_apres_numero():  # cas réel : « 9« Section 1 ter 10« Du mariage forcé »
    """« 9« Section » donne l'alinéa 9, qui commence par « « »."""
    debut = " ".join(f"{i}Texte {i}." for i in range(1, 9))
    res = alineas_de(
        debut
        + " 9« Section 1 ter 10« Du mariage forcé 11« Art. 224‑5‑3. – Constitue un mariage forcé."
    )
    assert numeros(res) == list(range(1, 12))
    assert res[8][1] == "« Section 1 ter"


def test_annee_avec_point_non_decoupee():  # « 2026. » ne doit pas être pris pour l'alinéa 20
    """« 2026. » n'est pas lu comme « alinéa 20 + 26. »."""
    debut = " ".join(f"{i}Texte {i}." for i in range(1, 19))
    res = alineas_de(debut + " 19Avant le 1er janvier 2026. Suite. 20Alinéa vingt.")
    assert numeros(res) == list(range(1, 21))
    assert "2026. Suite." in res[18][1] and res[19][1] == "Alinéa vingt."


def test_article_sans_numeros_un_seul_enregistrement():
    """Un article sans numéros (résolution avec des « 1° … 2° ») n'est pas découpé."""
    texte = (
        "L’Assemblée nationale, Vu l’article 34‑1, "
        "Invite le Gouvernement : 1° À examiner ; 2° À permettre."
    )
    assert alineas_de(texte) == [(None, texte)]


# ---------- table articles ----------


def test_colonnes_numero_libelle_contenu_alineas():
    """numero, libelle, contenu et alineas sont remplis avec les bonnes valeurs."""
    con = construire([{"numero": "2", "libelle": "Article 2", "content": "1Texte. 2Suite."}])
    assert con.execute("SELECT numero, libelle, contenu, alineas FROM articles").fetchall() == [
        ("2", "Article 2", "1Texte. 2Suite.", ["Texte.", "Suite."])
    ]


def test_nb_alineas():
    """nb_alineas vaut 3 pour un article à 3 alinéas, et est vide pour un article sans alinéas."""
    con = construire(
        [
            {"item_id": "avec", "content": "1Premier. 2Deuxième. 3Troisième."},
            {"item_id": "sans", "content": "Texte sans numéro d'alinéa."},
        ]
    )
    res = dict(con.execute("SELECT item_id, nb_alineas FROM articles").fetchall())
    assert res == {"avec": 3, "sans": None}


def test_perimetre_legislature_17_et_articles_seulement():
    """Une ligne de la 16e législature et un exposé des motifs sont exclus."""
    con = construire(
        [
            {"content": "Article de la 17e", "item_id": "a"},
            {"content": "Autre législature", "legislature": 16, "item_id": "b"},
            {
                "content": "Mesdames, Messieurs,",
                "item_kind": "expose_des_motifs",
                "numero": None,
                "item_id": "c",
            },
        ]
    )
    assert con.execute("SELECT item_id FROM articles").fetchall() == [("a",)]


def test_article_supprime():
    """Un article entièrement supprimé est marqué ; un article supprimé en partie ne l'est pas."""
    con = construire(
        [
            {"item_id": "s1", "content": "(Supprimé)"},
            {"item_id": "s2", "content": "(Supprimé)[SDdL-H251]"},
            {"item_id": "s3", "content": "Article 2 bis C (Supprimé)"},
            {
                "item_id": "p1",
                "content": "1I. – (Supprimé) 2I bis (nouveau). – Le code est modifié.",
            },  # partiel
            {"item_id": "n1", "content": "1Texte normal. 2Suite."},
        ]
    )
    res = dict(con.execute("SELECT item_id, supprime FROM articles").fetchall())
    assert res == {"s1": True, "s2": True, "s3": True, "p1": False, "n1": False}


def test_rang_ordre_de_lecture():
    """Ordre : liminaire, 1, 2, 2 bis, 3 A, 3, 3 bis A, 3 bis, 10."""
    nums = ["10", "3", "3 bis", "3 bis A", "2 bis", "liminaire", "1", "2", "3 A"]
    con = construire(
        [{"item_id": "x" + n.replace(" ", "_"), "numero": n, "content": "t"} for n in nums]
    )
    ordre = [r[0] for r in con.execute("SELECT numero FROM articles ORDER BY rang").fetchall()]
    assert ordre == ["liminaire", "1", "2", "2 bis", "3 A", "3", "3 bis A", "3 bis", "10"]


def test_rang_recommence_pour_chaque_document():
    """Le rang repart à 1 pour chaque texte."""
    con = construire(
        [
            {"uid": "D1", "item_id": "a", "numero": "1", "content": "t"},
            {"uid": "D2", "item_id": "b", "numero": "1", "content": "t"},
        ]
    )
    assert con.execute("SELECT rang FROM articles ORDER BY document_uid").fetchall() == [(1,), (1,)]


def test_liste_parenthese_petits_numeros():
    """« 21) D'évaluer » donne l'alinéa 2, qui commence par « 1) » (cas réel PNREANR5L17B2147)."""
    res = alineas_de(
        "1La commission est chargée : 21) D’évaluer les dispositifs ; "
        "32) De mettre en lumière les difficultés ; 43) D’émettre des recommandations."
    )
    assert numeros(res) == [1, 2, 3, 4]
    assert res[1] == (2, "1) D’évaluer les dispositifs ;")
    assert res[3] == (4, "3) D’émettre des recommandations.")


def test_nombre_avec_parenthese_non_decoupe():  # cas réels : « 200). », « 6) et aux informations »
    """Quand on attend l'alinéa 20, « 200). » n'est pas lu comme « alinéa 20 + 0) »."""
    # On attend l'alinéa 20 : « 200). » commence par « 20 » mais n'est PAS l'alinéa 20 + « 0) ».
    debut = " ".join(f"{i}Texte {i}." for i in range(1, 19))
    res = alineas_de(debut + " 19Montant (voir 200). Tableau 6) et aux informations. 20Fin.")
    assert numeros(res) == list(range(1, 21))
    assert res[18][1] == "Montant (voir 200). Tableau 6) et aux informations."


def test_premier_numero_doit_etre_au_debut():
    """« 12 mois après, 1Vu… » ne commence pas par un numéro d'alinéa : pas de découpage."""
    assert alineas_de("12 mois après, 1Vu le code. 2Suite.") == [
        (None, "12 mois après, 1Vu le code. 2Suite.")
    ]
