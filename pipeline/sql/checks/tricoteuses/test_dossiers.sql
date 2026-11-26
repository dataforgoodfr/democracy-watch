-- =============================================================================
-- Tests SQL CI (DuckDB) pour la table `dossiers`
-- =============================================================================
-- Périmètre  : 17e législature, Assemblée nationale (`legislature = 17`).
--              Invariants génériques compatibles avec une base mise à jour
--              quotidiennement (états évolutifs).
--              Les spot-checks figés sur l'extrait de référence sont isolés dans
--              `sql/canutes/tests/test_dossiers_snapshot.sql`.
-- Prérequis  : exécuter `sql/canutes/dossiers.sql` dans la même session DuckDB.
-- Convention : chaque assertion lève `error(...)` si une ligne viole la règle,
--              et la dernière requête renvoie un résumé `PASS` si tout réussit.
-- =============================================================================

-- 1. Grain unique (`uid`) et parité de volumétrie avec `assemblee.dossiers` (L17)
--    Vérifie l'absence de doublons sur `uid`, que la table n'est pas vide et que son volume correspond exactement à la source L17.
SELECT error(
    'FAIL [dossiers.grain]: COUNT(*)=' || cnt || ' vs DISTINCT uid=' || dist_cnt
    || ' vs assemblee.dossiers(L17)=' || src_cnt
)
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(DISTINCT uid) AS dist_cnt,
        (SELECT COUNT(*) FROM assemblee.dossiers WHERE legislature = 17) AS src_cnt
    FROM dossiers
) t
WHERE cnt != dist_cnt OR cnt != src_cnt OR cnt = 0;

-- 1b. Périmètre : uniquement la 17e législature
--     Vérifie qu'aucun dossier d'une autre législature n'a été ingéré.
SELECT error('FAIL [dossiers.scope_legislature]: ' || n_bad || ' dossier(s) hors 17e législature')
FROM (
    SELECT COUNT(*) AS n_bad
    FROM dossiers
    WHERE legislature IS DISTINCT FROM 17
) t
WHERE n_bad > 0;

-- 2. Colonnes obligatoires sans NULL ni titre vide
--    Vérifie que les identifiants, classifications, dates principales et informations d'étape sont toujours renseignés.
SELECT error('FAIL [dossiers.not_null]: ' || n_nulls || ' ligne(s) avec colonne obligatoire NULL ou titre vide')
FROM (
    SELECT COUNT(*) AS n_nulls
    FROM dossiers
    WHERE uid IS NULL
       OR legislature IS NULL
       OR procedure IS NULL
       OR procedure_code IS NULL
       OR procedure_libelle IS NULL
       OR titre IS NULL
       OR TRIM(titre) = ''
       OR statut IS NULL
       OR date_depot IS NULL
       OR date_dernier_acte IS NULL
       OR etape_code IS NULL
       OR etape_libelle IS NULL
) t
WHERE n_nulls > 0;

-- 3. Désambiguïsation complète des procédures mixtes (codes 5 organique & 7 constitutionnelle)
--    Vérifie qu'aucun dossier dont le libellé source est ambigu (« Projet ou proposition de loi... ») ne reste non tranché.
SELECT error(
    'FAIL [dossiers.procedure_mixte]: ' || n_unresolved || ' procédure(s) mixte(s) non départagée(s)'
)
FROM (
    SELECT COUNT(*) AS n_unresolved
    FROM dossiers
    WHERE procedure_libelle ILIKE 'Projet ou proposition de loi%'
      AND procedure NOT IN ('Projet de loi', 'Proposition de loi')
) t
WHERE n_unresolved > 0;

-- 4. Cohérence de la normalisation de `procedure`
--    Vérifie que les libellés non mixtes sont systématiquement normalisés vers la catégorie attendue.
SELECT error('FAIL [dossiers.procedure_norm]: normalisation inattendue "' || procedure || '" pour ' || uid)
FROM dossiers
WHERE (procedure_libelle ILIKE 'Projet de %' AND procedure != 'Projet de loi')
   OR (procedure_libelle ILIKE 'Proposition de loi%' AND procedure != 'Proposition de loi')
   OR (procedure_libelle ILIKE 'Résolution%' AND procedure != 'Résolution')
   OR (procedure_libelle ILIKE 'Rapport d''information%' AND procedure != 'Rapport d''information')
LIMIT 1;

-- 5. Domaines fermés de `statut` / `denouement` et cohérence avec `derniere_decision` / `date_promulgation` / `etape_code`
--    Vérifie que `statut` appartient au domaine binaire (`en_cours`, `close`).
SELECT error('FAIL [dossiers.statut_domain]: statut invalide "' || statut || '" pour ' || uid)
FROM dossiers
WHERE statut NOT IN ('en_cours', 'close')
LIMIT 1;

--    Vérifie que `denouement` appartient à l'énumération normalisée (ou est NULL).
SELECT error('FAIL [dossiers.denouement_domain]: denouement invalide "' || denouement || '" pour ' || uid)
FROM dossiers
WHERE denouement IS NOT NULL
  AND denouement NOT IN ('promulgué', 'adopté', 'rejeté', 'caduc', 'fusionné', 'retiré')
LIMIT 1;

--    Vérifie l'équivalence stricte `statut = 'en_cours'` <=> `denouement IS NULL` (et `statut = 'close'` <=> `denouement IS NOT NULL`).
SELECT error(
    'FAIL [dossiers.statut_denouement_coherence]: incohérence statut="' || statut
    || '" / denouement="' || COALESCE(denouement, 'NULL') || '" sur ' || uid
)
FROM dossiers
WHERE (statut = 'en_cours' AND denouement IS NOT NULL)
   OR (statut = 'close' AND denouement IS NULL)
LIMIT 1;

--    Cohérence bidirectionnelle de `promulgué` : impose `statut = 'close'`, `date_promulgation`, étape `PROM` et libellé de loi promulguée dans `derniere_decision`, et interdit `date_promulgation` hors `promulgué`.
SELECT error('FAIL [dossiers.promulgue_coherence]: incohérence promulgation sur ' || uid)
FROM dossiers
WHERE (
        denouement = 'promulgué'
        AND (
            statut != 'close'
            OR date_promulgation IS NULL
            OR etape_code != 'PROM'
            OR derniere_decision IS NULL
            OR (derniere_decision NOT LIKE 'Loi n° % promulguée' AND derniere_decision != 'Loi promulguée')
        )
      )
   OR (
        denouement IS DISTINCT FROM 'promulgué'
        AND date_promulgation IS NOT NULL
      )
LIMIT 1;

--    Cohérence de `derniere_decision` pour les dossiers `retiré` (« Initiative retirée ») et `fusionné` (référence `(DLR...)`).
SELECT error('FAIL [dossiers.retire_fusionne_coherence]: incohérence derniere_decision pour ' || uid)
FROM dossiers
WHERE (denouement = 'retiré' AND COALESCE(derniere_decision, '') != 'Initiative retirée')
   OR (denouement = 'fusionné' AND COALESCE(derniere_decision, '') NOT LIKE '%(DLR%)')
LIMIT 1;

--    Tout dossier clôturé (`statut = 'close'`) doit porter une `derniere_decision` explicite.
SELECT error('FAIL [dossiers.terminal_derniere_decision]: statut close (' || COALESCE(denouement, 'NULL') || ') sans derniere_decision sur ' || uid)
FROM dossiers
WHERE statut = 'close'
  AND derniere_decision IS NULL
LIMIT 1;

--    Cohérence des motions de censure (`procedure_code = '13'`) et isolation vis-à-vis des autres procédures.
SELECT error('FAIL [dossiers.motion_coherence]: incohérence motion sur ' || uid || ' (code=' || procedure_code || ', denouement=' || COALESCE(denouement, 'NULL') || ')')
FROM dossiers
WHERE (procedure_code != '13' AND COALESCE(derniere_decision, '') ILIKE 'motion %')
   OR (procedure_code = '13' AND denouement = 'adopté' AND COALESCE(derniere_decision, '') != 'Motion adoptée')
   OR (procedure_code = '13' AND denouement = 'rejeté' AND COALESCE(derniere_decision, '') NOT ILIKE 'motion rejetée')
LIMIT 1;

--    Cohérence du dénouement des dossiers à l'étape Conseil constitutionnel (`CC`) hors cas prioritaires (`promulgué`/`fusionné`/`retiré`).
SELECT error('FAIL [dossiers.cc_coherence]: incohérence statut/denouement CC sur ' || uid || ' (' || statut || '/' || COALESCE(denouement, 'NULL') || ')')
FROM dossiers
WHERE etape_code = 'CC'
  AND COALESCE(denouement, '') NOT IN ('promulgué', 'fusionné', 'retiré')
  AND (
      (COALESCE(derniere_decision, '') ILIKE 'Conseil constitutionnel : non conforme%' AND (statut != 'close' OR denouement IS DISTINCT FROM 'rejeté'))
      OR (
          (
              COALESCE(derniere_decision, '') ILIKE 'Conseil constitutionnel : conforme%'
              OR COALESCE(derniere_decision, '') ILIKE 'Conseil constitutionnel : partiellement conforme%'
          )
          AND (statut != 'close' OR denouement IS DISTINCT FROM 'adopté')
      )
  )
LIMIT 1;

-- 6. Cohérence chronologique des dates
--    Vérifie que `date_depot` précède ou égale `date_dernier_acte`, `date_promulgation` et `date_prochain_acte`.
SELECT error(
    'FAIL [dossiers.date_order]: date incohérente sur ' || uid
    || ' (depot=' || date_depot || ', dernier=' || date_dernier_acte
    || ', prom=' || COALESCE(date_promulgation::VARCHAR, 'NULL')
    || ', prochain=' || COALESCE(date_prochain_acte::VARCHAR, 'NULL') || ')'
)
FROM dossiers
WHERE date_depot > date_dernier_acte
   OR (date_promulgation IS NOT NULL AND date_promulgation < date_depot)
   OR (date_prochain_acte IS NOT NULL AND date_prochain_acte < date_depot)
LIMIT 1;

-- 7. Préfixage chambre sur `etape_libelle` (`AN*` / `SN*`)
--    Vérifie que les étapes de l'Assemblée nationale et du Sénat portent bien le préfixe de chambre correspondant.
SELECT error('FAIL [dossiers.etape_prefix]: préfixe manquant sur ' || uid || ' (' || etape_code || ')')
FROM dossiers
WHERE (etape_code ILIKE 'AN%' AND etape_libelle NOT LIKE 'Assemblée nationale — %')
   OR (etape_code ILIKE 'SN%' AND etape_libelle NOT LIKE 'Sénat — %')
LIMIT 1;

-- 8. Fidélité du LEFT JOIN `commission_saisie_au_fond` avec `assemblee.organes`
--    Vérifie que le libellé reste NULL sans UID et correspond exactement à `assemblee.organes` lorsque l'organe existe.
SELECT error('FAIL [dossiers.commission_join]: incohérence commission sur ' || d.uid)
FROM dossiers d
LEFT JOIN assemblee.organes o ON o.uid = d.commission_saisie_au_fond_uid
WHERE (d.commission_saisie_au_fond_uid IS NULL AND d.commission_saisie_au_fond_libelle IS NOT NULL)
   OR (
       d.commission_saisie_au_fond_uid IS NOT NULL
       AND json_extract_string(o.data, '$.libelle') IS NOT NULL
       AND d.commission_saisie_au_fond_libelle IS DISTINCT FROM json_extract_string(o.data, '$.libelle')
   )
LIMIT 1;

-- 9. Validité et complétude de `dossier_url`
--    Vérifie que chaque URL correspond à la législature du dossier, puis la parité de remplissage avec `titreChemin` (L17).
SELECT error('FAIL [dossiers.dossier_url_format]: URL invalide "' || dossier_url || '" pour ' || uid)
FROM dossiers
WHERE dossier_url IS NOT NULL
  AND dossier_url NOT LIKE ('https://www.assemblee-nationale.fr/dyn/' || legislature || '/dossiers/%')
LIMIT 1;

SELECT error(
    'FAIL [dossiers.dossier_url_count]: non-NULL dossier_url=' || url_cnt
    || ' vs non-NULL titreChemin=' || src_cnt
)
FROM (
    SELECT
        (SELECT COUNT(*) FROM dossiers WHERE dossier_url IS NOT NULL) AS url_cnt,
        (
            SELECT COUNT(*)
            FROM assemblee.dossiers
            WHERE legislature = 17
              AND json_extract_string(data, '$.titreDossier.titreChemin') IS NOT NULL
        ) AS src_cnt
) t
WHERE url_cnt != src_cnt;

-- 10. Validité JSON et complétude de `expose_des_motifs`
--     Vérifie que chaque champ non NULL est un tableau JSON non vide dont TOUS les éléments ont `document_uid`, `item_id` et `content`,
--     et que le nombre total d'éléments correspond exactement aux indexations de `tisseuse.assemblee_text_search` (L17).
SELECT error('FAIL [dossiers.expose_des_motifs_shape]: tableau JSON vide sur ' || uid)
FROM dossiers
WHERE expose_des_motifs IS NOT NULL
  AND (
      json_type(expose_des_motifs) != 'ARRAY'
      OR json_array_length(expose_des_motifs) = 0
  )
LIMIT 1;

SELECT error('FAIL [dossiers.expose_des_motifs_elements]: élément JSON incomplet sur ' || uid)
FROM (
    SELECT
        uid,
        UNNEST(TRY_CAST(expose_des_motifs AS JSON[])) AS item
    FROM dossiers
    WHERE expose_des_motifs IS NOT NULL
) t
WHERE json_extract_string(item, '$.document_uid') IS NULL
   OR json_extract_string(item, '$.item_id') IS NULL
   OR json_extract_string(item, '$.content') IS NULL
LIMIT 1;

SELECT error(
    'FAIL [dossiers.expose_des_motifs_count]: total items dossiers=' || d_items
    || ' vs source tisseuse=' || s_items
)
FROM (
    SELECT
        (SELECT COALESCE(SUM(json_array_length(expose_des_motifs)), 0) FROM dossiers WHERE expose_des_motifs IS NOT NULL) AS d_items,
        (
            SELECT COUNT(*)
            FROM tisseuse.assemblee_text_search s
            INNER JOIN assemblee.dossiers d ON d.uid = s.dossier_uid
            WHERE d.legislature = 17
              AND s.legislature = 17
              AND s.item_kind = 'expose_des_motifs'
              AND s.document_uid IS NOT NULL
              AND s.item_id IS NOT NULL
              AND s.content IS NOT NULL
        ) AS s_items
) t
WHERE d_items != s_items;

-- 11. Non-régression : aucun dossier `en_cours` (hors étape `CC`) ne doit porter une `derniere_decision`
--     issue d'une `Decision_Type` d'une étape antérieure (`top_idx < max_top_idx`).
--     Garantit qu'une décision d'une lecture précédente ne persiste pas après passage à une nouvelle étape législative.
WITH RECURSIVE actes AS (
    SELECT
        d.uid AS dossier_uid,
        1 AS depth,
        elem.idx::INTEGER AS top_idx,
        LPAD(elem.idx::VARCHAR, 3, '0') AS sort_path,
        elem.acte_json
    FROM assemblee.dossiers d
    CROSS JOIN UNNEST(TRY_CAST(json_extract(d.data, '$.actesLegislatifs') AS JSON[]))
        WITH ORDINALITY AS elem(acte_json, idx)
    WHERE d.legislature = 17
    UNION ALL
    SELECT
        p.dossier_uid,
        p.depth + 1 AS depth,
        p.top_idx,
        p.sort_path || '.' || LPAD(elem.idx::VARCHAR, 3, '0') AS sort_path,
        elem.acte_json
    FROM actes p
    CROSS JOIN UNNEST(TRY_CAST(json_extract(p.acte_json, '$.actesLegislatifs') AS JSON[]))
        WITH ORDINALITY AS elem(acte_json, idx)
),
stats AS (
    SELECT
        dossier_uid,
        MAX(CASE WHEN depth = 1 THEN top_idx END) AS max_top_idx,
        MAX_BY(
            CASE
                WHEN json_extract_string(acte_json, '$.xsiType') = 'Decision_Type'
                 AND json_extract_string(acte_json, '$.statutConclusion.libelle') IS NOT NULL
                THEN top_idx
            END,
            (
                top_idx,
                COALESCE(TRY_CAST(LEFT(json_extract_string(acte_json, '$.dateActe'), 10) AS DATE), DATE '1900-01-01'),
                sort_path
            )
        ) AS derniere_decision_top_idx
    FROM actes
    GROUP BY dossier_uid
)
SELECT error(
    'FAIL [dossiers.stale_derniere_decision]: ' || d.uid || ' en_cours (' || d.etape_code
    || ') a une derniere_decision issue d''une étape antérieure (' || COALESCE(s.derniere_decision_top_idx::VARCHAR, 'NULL')
    || ' < ' || s.max_top_idx || ')'
)
FROM dossiers d
JOIN stats s ON s.dossier_uid = d.uid
WHERE d.statut = 'en_cours'
  AND d.etape_code != 'CC'
  AND d.derniere_decision IS NOT NULL
  AND (
      s.derniere_decision_top_idx IS NULL
      OR s.derniere_decision_top_idx < s.max_top_idx
  )
LIMIT 1;

-- 12. Non-régression : toute résolution ayant déjà une décision sur son étape finale (`derniere_decision`) ne doit plus être `en_cours`
SELECT error('FAIL [dossiers.resolution_en_cours_decision]: résolution en_cours avec derniere_decision non NULL sur ' || uid)
FROM dossiers
WHERE procedure_code IN ('8', '22')
  AND statut = 'en_cours'
  AND derniere_decision IS NOT NULL
LIMIT 1;

SELECT 'PASS: test_dossiers.sql (' || COUNT(*) || ' dossiers vérifiés)' AS result
FROM dossiers;
