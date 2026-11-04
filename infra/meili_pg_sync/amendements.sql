-- Documents Meilisearch des amendements, lus dans la base restaurée depuis le dump CLAIR
-- (schéma : https://github.com/accelaire/CLAIR, apps/api/prisma/schema.prisma), avec les noms
-- de champs de l'index existant. Paramètres psycopg : legislatures (liste), since (timestamptz ou NULL).
--
-- updated_at est lu via to_jsonb(a) : NULL si la colonne manque, sans erreur.
-- Discussions communes et séries identiques : colonnes id_/position_discussion_* d'amendements,
-- renommées comme dans l'index (position = discussion commune, position_identique = série identique).
-- Chaque membre d'une série porte la liste compacte de toute la série (identiques).
-- (Pas de signe pour-cent dans les commentaires : psycopg y lirait un paramètre.)

WITH docs AS (
    SELECT
        a.uid_canonique                      AS uid,     -- clé stable (uid sans TC)
        a.uid                                AS uid_an,  -- uid publié par l'AN : seul valide dans ses URL
        a.legislature,
        a.numero,
        a.texte_ref,
        a.article_vise                       AS article,
        a.groupe_ref                         AS groupe_politique,
        a.auteur_ref                         AS auteur,
        to_char(a.date_depot, 'YYYY-MM-DD')  AS date_depot,
        a.sort,
        a.dispositif,
        a.expose_sommaire                    AS expose,
        -- Nom du député ; à défaut, le libellé publié (Gouvernement, commission…).
        coalesce(nullif(trim(concat_ws(' ', p.prenom, p.nom)), ''), a.auteur_libelle) AS auteur_nom,
        g.nom_complet                        AS groupe_libelle,
        g.nom_court                          AS groupe_abrege,
        g.couleur                            AS groupe_couleur,
        d.uid                                AS dossier_uid,
        d.titre                              AS dossier_titre,
        a.id_discussion_commune,
        a.position_discussion_commune        AS position,
        a.id_discussion_identique,
        a.position_discussion_identique      AS position_identique,
        (to_jsonb(a) ->> 'updated_at')::timestamptz AS modifie
    FROM amendements a
    LEFT JOIN parlementaires p ON p.id = a.parlementaire_id
    -- Un groupe par (slug, chambre, législature) : celui de la législature de l'amendement en priorité.
    LEFT JOIN LATERAL (
        SELECT nom_complet, nom_court, couleur
        FROM groupes_politiques
        WHERE source_id = a.groupe_ref AND chambre = 'assemblee'
        ORDER BY legislature = a.legislature DESC NULLS LAST
        LIMIT 1
    ) g ON true
    LEFT JOIN dossiers_legislatifs d ON d.id = a.dossier_id
    WHERE a.chambre = 'assemblee'
      AND a.legislature = ANY(%(legislatures)s)
      -- Sans dispositif ni exposé : irrecevables jamais publiés (Charge, Cavalier…), rien à chercher.
      -- Exposé seul : amendements de crédits du PLF (état B), dont CLAIR n'a pas le tableau.
      AND (nullif(trim(a.dispositif), '') IS NOT NULL OR nullif(trim(a.expose_sommaire), '') IS NOT NULL)
),
-- Membres compacts de chaque série, parmi les documents de l'index (la page n'affiche qu'eux),
-- dans l'ordre d'appel en séance puis par numéro ; uid en dernier pour un ordre stable.
series AS (
    SELECT
        id_discussion_identique,
        count(*) AS nb_identiques,
        max(modifie) AS serie_modifie,  -- un membre change : toute la série est renvoyée
        jsonb_agg(jsonb_build_object(
            'uid', uid, 'uid_an', uid_an, 'numero', numero, 'sort', sort,
            'position_identique', position_identique, 'auteur_nom', auteur_nom,
            'groupe_abrege', groupe_abrege, 'groupe_libelle', groupe_libelle, 'groupe_couleur', groupe_couleur
        ) ORDER BY
            CASE position_identique WHEN 'Premier' THEN 0 WHEN 'Milieu' THEN 1 WHEN 'Dernier' THEN 2 END NULLS LAST,
            nullif(regexp_replace(numero::text, '[^0-9]', '', 'g'), '')::bigint NULLS LAST,
            uid
        ) AS identiques
    FROM docs
    WHERE id_discussion_identique IS NOT NULL
    GROUP BY id_discussion_identique
)
SELECT
    docs.uid, docs.uid_an, docs.legislature, docs.numero, docs.texte_ref, docs.article,
    docs.groupe_politique, docs.auteur, docs.date_depot, docs.sort, docs.dispositif, docs.expose,
    docs.auteur_nom, docs.groupe_libelle, docs.groupe_abrege, docs.groupe_couleur,
    docs.dossier_uid, docs.dossier_titre,
    docs.id_discussion_commune, docs.position,
    docs.id_discussion_identique, docs.position_identique,
    coalesce(series.nb_identiques, 1)            AS nb_identiques,
    coalesce(series.identiques, '[]'::jsonb)     AS identiques,
    extract(epoch FROM greatest(docs.modifie, series.serie_modifie))::bigint AS updated_at
FROM docs
LEFT JOIN series USING (id_discussion_identique)
WHERE %(since)s::timestamptz IS NULL OR greatest(docs.modifie, series.serie_modifie) >= %(since)s
