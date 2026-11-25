-- =============================================================================
-- Tests SQL CI (DuckDB) pour la table `textes`
-- =============================================================================
-- Périmètre  : 17e législature, Assemblée nationale (`assemblee.dossiers.legislature = 17`).
--              Invariants génériques compatibles avec une base mise à jour
--              quotidiennement (états évolutifs).
--              Les spot-checks figés sur l'extrait de référence sont isolés dans
--              `sql/canutes/tests/test_textes_snapshot.sql`.
-- Prérequis  : exécuter `sql/canutes/textes.sql` dans la même session DuckDB.
-- Convention : chaque assertion lève `error(...)` si une ligne viole la règle,
--              et la dernière requête renvoie un résumé `PASS` si tout réussit.
-- =============================================================================

-- 1. Grain unique (`uid`) et parité exacte avec `assemblee.documents` ⋈ `assemblee.dossiers` (L17)
--    Vérifie l'absence de doublons sur `uid`, que la table n'est pas vide et que chaque document rattaché à un dossier L17 est présent.
SELECT error(
    'FAIL [textes.grain]: COUNT(*)=' || cnt || ' vs DISTINCT uid=' || dist_cnt
    || ' vs documents_in_dossiers(L17)=' || expected_cnt
)
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(DISTINCT uid) AS dist_cnt,
        (
            SELECT COUNT(*)
            FROM assemblee.documents doc
            INNER JOIN assemblee.dossiers dos
                ON dos.uid = json_extract_string(doc.data, '$.dossierRef')
            WHERE dos.legislature = 17
        ) AS expected_cnt
    FROM textes
) t
WHERE cnt != dist_cnt OR cnt != expected_cnt OR cnt = 0;

-- 2. Intégrité référentielle et périmètre L17 de `dossier_uid` vers `assemblee.dossiers`
--    Vérifie qu'aucun texte ne référence un dossier inexistant ou hors 17e législature.
SELECT error('FAIL [textes.fk_dossier]: dossier_uid orphelin ou hors L17 "' || t.dossier_uid || '" pour ' || t.uid)
FROM textes t
LEFT JOIN assemblee.dossiers d
    ON d.uid = t.dossier_uid
   AND d.legislature = 17
WHERE d.uid IS NULL
LIMIT 1;

-- 3. Colonnes obligatoires sans NULL ni libellés vides
--    Vérifie que les identifiants, nature/type, rang et date de dépôt sont toujours renseignés.
SELECT error('FAIL [textes.not_null]: ' || n_nulls || ' ligne(s) avec colonne obligatoire NULL ou vide')
FROM (
    SELECT COUNT(*) AS n_nulls
    FROM textes
    WHERE uid IS NULL
       OR dossier_uid IS NULL
       OR nature IS NULL
       OR TRIM(nature) = ''
       OR type_document IS NULL
       OR TRIM(type_document) = ''
       OR rang_dans_dossier IS NULL
       OR date_depot IS NULL
) t
WHERE n_nulls > 0;

-- 4. Plage cohérente de `date_depot` (Ve République)
--    Vérifie qu'aucun texte n'a une date antérieure à 1958 (détecte les erreurs de parsing ou de date sentinelle).
SELECT error('FAIL [textes.date_depot_bounds]: date_depot aberrante (' || date_depot || ') sur ' || uid)
FROM textes
WHERE date_depot < DATE '1958-01-01'
LIMIT 1;

-- 5. Continuité stricte de `rang_dans_dossier` (1..N sans trou ni doublon par dossier)
--    Vérifie que la numérotation séquentielle au sein de chaque dossier démarre à 1 et reste contiguë.
SELECT error(
    'FAIL [textes.rang_continuity]: dossier ' || dossier_uid
    || ' (cnt=' || cnt || ', min=' || min_r || ', max=' || max_r || ', dist=' || dist_r || ')'
)
FROM (
    SELECT
        dossier_uid,
        COUNT(*) AS cnt,
        MIN(rang_dans_dossier) AS min_r,
        MAX(rang_dans_dossier) AS max_r,
        COUNT(DISTINCT rang_dans_dossier) AS dist_r
    FROM textes
    GROUP BY dossier_uid
) s
WHERE min_r != 1 OR max_r != cnt OR dist_r != cnt
LIMIT 1;

-- 6. Priorité des marqueurs structurels (`%BTC%`, `%BTA%`, `%TAP%`) dans `nature`
--    Vérifie que ces marqueurs d'UID priment sur la classification générique pour distinguer commission, adopté et adopté provisoire.
SELECT error('FAIL [textes.nature_marker_priority]: nature="' || nature || '" inattendue pour ' || uid)
FROM textes
WHERE (uid ILIKE '%BTC%' AND nature != 'Texte de commission')
   OR (uid ILIKE '%BTA%' AND nature != 'Texte adopté')
   OR (uid ILIKE '%TAP%' AND nature != 'Texte adopté provisoire')
LIMIT 1;

-- 7. Cohérence `INITDEP` / `INITNAV` sur `PION` / `PRJL` / `PNRE` (hors marqueurs `BTC`/`BTA`/`TAP`)
--    Vérifie la distinction entre texte déposé initialement (`Texte déposé`) et texte transmis en navette (`Texte en navette`).
SELECT error('FAIL [textes.depot_nature_coherence]: nature="' || t.nature || '" inattendue pour ' || t.uid)
FROM textes t
JOIN assemblee.documents d ON d.uid = t.uid
WHERE t.uid NOT ILIKE '%BTC%'
  AND t.uid NOT ILIKE '%BTA%'
  AND t.uid NOT ILIKE '%TAP%'
  AND json_extract_string(d.data, '$.classification.type.code') IN ('PION', 'PRJL', 'PNRE')
  AND (
      (json_extract_string(d.data, '$.classification.famille.depot.code') = 'INITDEP' AND t.nature != 'Texte déposé')
      OR (json_extract_string(d.data, '$.classification.famille.depot.code') = 'INITNAV' AND t.nature != 'Texte en navette')
  )
LIMIT 1;

-- 8. `numero` NULL uniquement sur les motions de censure et déclarations du Gouvernement
--    Vérifie que tout autre type de texte dispose bien d'un numéro attribué.
SELECT error('FAIL [textes.numero_null]: numero NULL inattendu sur ' || uid || ' (' || nature || ')')
FROM textes
WHERE numero IS NULL
  AND nature NOT IN ('Motion de censure', 'Déclaration du Gouvernement')
LIMIT 1;

SELECT 'PASS: test_textes.sql (' || COUNT(*) || ' textes vérifiés)' AS result
FROM textes;
