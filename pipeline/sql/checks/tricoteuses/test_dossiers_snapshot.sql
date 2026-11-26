-- =============================================================================
-- Tests SQL statiques (extrait figé) pour la table `dossiers`
-- =============================================================================
-- Périmètre  : spot-checks sur des UID réels issus de l'extrait figé
--              `data/canutes_extract_big_search_20261120.duckdb` (17e législature).
--              Ces tests ne doivent PAS tourner en CI sur la base mise à jour
--              quotidiennement : certains vérifient des états transitoires
--              (`en_cours`, `adopté` avant promulgation, `etape_code`) qui
--              évoluent au fil de la navette parlementaire, ou des UID propres
--              à cet extrait.
--              Pour la CI quotidienne, voir `sql/canutes/tests/test_dossiers.sql`.
-- Prérequis  : exécuter `sql/canutes/dossiers.sql` sur l'extrait du 2026-11-20.
-- =============================================================================

-- 1. Spot-checks sur des dossiers représentatifs de la 17e législature
--    Loi promulguée (audiovisuel) : vérifie procédure, statut, dénouement, dernière décision, dates, étape `PROM` et URL.
SELECT error('FAIL [dossiers.spot_check.DLR5L17N50168]: valeurs inattendues ou dossier absent pour loi promulguée (audiovisuel)')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE procedure = 'Proposition de loi'
              AND statut = 'close'
              AND denouement = 'promulgué'
              AND derniere_decision = 'Loi n° 2024-1177 promulguée'
              AND date_depot = DATE '2024-07-10'
              AND date_promulgation = DATE '2024-12-13'
              AND etape_code = 'PROM'
              AND commission_saisie_au_fond_uid IS NOT NULL
              AND commission_saisie_au_fond_libelle IS NOT NULL
              AND dossier_url LIKE 'https://www.assemblee-nationale.fr/dyn/17/dossiers/%'
        ) AS match_cnt
    FROM dossiers
    WHERE uid = 'DLR5L17N50168'
) t
WHERE cnt != 1 OR match_cnt != 1;

--    PLFSS 2025 : vérifie que le dénouement `promulgué` prime sur les motions de censure 49.3.
SELECT error('FAIL [dossiers.spot_check.DLR5L17N50588]: priorité promulgué sur motion 49.3 (PLFSS 2025)')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE procedure = 'Projet de loi'
              AND statut = 'close'
              AND denouement = 'promulgué'
              AND derniere_decision = 'Loi n° 2025-199 promulguée'
        ) AS match_cnt
    FROM dossiers
    WHERE uid = 'DLR5L17N50588'
) t
WHERE cnt != 1 OR match_cnt != 1;

--    Motion de censure adoptée : vérifie `statut = 'close'`, `denouement = 'adopté'`, `derniere_decision = 'Motion adoptée'` et `etape_code = 'AN21'`.
SELECT error('FAIL [dossiers.spot_check.DLR5L17N50975]: motion de censure adoptée')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE statut = 'close'
              AND denouement = 'adopté'
              AND derniere_decision = 'Motion adoptée'
              AND etape_code = 'AN21'
        ) AS match_cnt
    FROM dossiers
    WHERE uid = 'DLR5L17N50975'
) t
WHERE cnt != 1 OR match_cnt != 1;

--    Résolution retirée : vérifie `statut = 'close'`, `denouement = 'retiré'`, `derniere_decision = 'Initiative retirée'` et `etape_code = 'ANLUNI'`.
SELECT error('FAIL [dossiers.spot_check.DLR5L17N50337]: résolution retirée')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE procedure = 'Résolution'
              AND statut = 'close'
              AND denouement = 'retiré'
              AND derniere_decision = 'Initiative retirée'
              AND etape_code = 'ANLUNI'
        ) AS match_cnt
    FROM dossiers
    WHERE uid = 'DLR5L17N50337'
) t
WHERE cnt != 1 OR match_cnt != 1;

--    Dossier fusionné (absorbé) : vérifie `statut = 'close'`, `denouement = 'fusionné'` et le lien vers le dossier absorbant dans `derniere_decision`.
SELECT error('FAIL [dossiers.spot_check.DLR5L17N54566]: dossier fusionné')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE statut = 'close'
              AND denouement = 'fusionné'
              AND derniere_decision = 'Dossier absorbé (DLR5L17N54608)'
        ) AS match_cnt
    FROM dossiers
    WHERE uid = 'DLR5L17N54566'
) t
WHERE cnt != 1 OR match_cnt != 1;

--    Procédure mixte (code 7) : vérifie sa résolution en `Projet de loi` à l'étape `AN2`.
SELECT error('FAIL [dossiers.spot_check.DLR5L17N54218]: procédure mixte (code 7) résolue en Projet de loi')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE procedure = 'Projet de loi'
              AND procedure_code = '7'
              AND etape_code = 'AN2'
        ) AS match_cnt
    FROM dossiers
    WHERE uid = 'DLR5L17N54218'
) t
WHERE cnt != 1 OR match_cnt != 1;

--    Dossier `en_cours` à l'AN (`AN1`) : vérifie que `denouement` et `derniere_decision` restent NULL en l'absence de décision.
SELECT error('FAIL [dossiers.spot_check.DLR5L17N50208]: dossier en_cours à l''AN sans denouement ni derniere_decision')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE statut = 'en_cours'
              AND etape_code = 'AN1'
              AND denouement IS NULL
              AND derniere_decision IS NULL
        ) AS match_cnt
    FROM dossiers
    WHERE uid = 'DLR5L17N50208'
) t
WHERE cnt != 1 OR match_cnt != 1;

-- 2. Spot-checks pour les dénouements `adopté` / `rejeté` étendus et la navette en cours
--    Résolutions adoptées : séance (ANLUNI), art. 151-7 (européenne), et conforme CC (Règlement)
SELECT error('FAIL [dossiers.spot_check.resolutions_adoptees]: résolution adoptée attendue')
FROM (
    SELECT
        COUNT(*) FILTER (WHERE uid = 'DLR5L17N50275' AND statut = 'close' AND denouement = 'adopté' AND derniere_decision = 'adoptée') AS c1,
        COUNT(*) FILTER (WHERE uid = 'DLR5L17N50335' AND statut = 'close' AND denouement = 'adopté' AND etape_code = 'ANLUNI') AS c2,
        COUNT(*) FILTER (WHERE uid = 'DLR5L17N51481' AND statut = 'close' AND denouement = 'adopté' AND etape_code = 'CC') AS c3
    FROM dossiers
    WHERE uid IN ('DLR5L17N50275', 'DLR5L17N50335', 'DLR5L17N51481')
) t
WHERE c1 != 1 OR c2 != 1 OR c3 != 1;

--    Lois définitivement votées en attente de promulgation (adoptée sans modification / CMP 2 chambres)
--    Vérifie aussi que la dernière décision de la CMP reflète le vote des chambres et non `Accord`.
SELECT error('FAIL [dossiers.spot_check.lois_adoptees]: loi définitivement adoptée attendue en statut close / denouement adopté avec derniere_decision CMP exacte')
FROM (
    SELECT
        COUNT(*) FILTER (WHERE uid = 'DLR5L17N51962' AND statut = 'close' AND denouement = 'adopté' AND etape_code = 'AN2') AS c1,
        COUNT(*) FILTER (
            WHERE uid = 'DLR5L17N51330'
              AND statut = 'close'
              AND denouement = 'adopté'
              AND etape_code = 'CMP'
              AND derniere_decision ILIKE 'adopté%, dans les conditions prévues à l''article 45, alinéa 3, de la Constitution'
              AND derniere_decision != 'Accord'
        ) AS c2
    FROM dossiers
    WHERE uid IN ('DLR5L17N51962', 'DLR5L17N51330')
) t
WHERE c1 != 1 OR c2 != 1;

--    Rejets définitifs : résolutions (séance / commission), PPL en 1re lecture, PJL rejeté AN1 + SN1
SELECT error('FAIL [dossiers.spot_check.rejets]: dossier définitivement rejeté attendu en statut close / denouement rejeté')
FROM (
    SELECT
        COUNT(*) FILTER (WHERE uid = 'DLR5L17N54841' AND statut = 'close' AND denouement = 'rejeté' AND procedure = 'Résolution') AS c1,
        COUNT(*) FILTER (WHERE uid = 'DLR5L17N51541' AND statut = 'close' AND denouement = 'rejeté' AND procedure = 'Résolution') AS c2,
        COUNT(*) FILTER (WHERE uid = 'DLR5L17N50453' AND statut = 'close' AND denouement = 'rejeté' AND procedure = 'Proposition de loi') AS c3,
        COUNT(*) FILTER (WHERE uid = 'DLR5L17N50172' AND statut = 'close' AND denouement = 'rejeté' AND procedure = 'Projet de loi') AS c4
    FROM dossiers
    WHERE uid IN ('DLR5L17N54841', 'DLR5L17N51541', 'DLR5L17N50453', 'DLR5L17N50172')
) t
WHERE c1 != 1 OR c2 != 1 OR c3 != 1 OR c4 != 1;

--    Navette : rejet en 2e chambre (SN1 -> AN2) et CMP votée par 1 seule chambre restent `en_cours` (`denouement IS NULL`)
--    (le vote de CMP déjà intervenu doit apparaître en `derniere_decision`, pas `Accord`).
SELECT error('FAIL [dossiers.spot_check.navette_en_cours]: dossier en navette ou CMP incomplète attendu en_cours / denouement NULL avec derniere_decision CMP exacte')
FROM (
    SELECT
        COUNT(*) FILTER (WHERE uid = 'DLR5L17N51215' AND statut = 'en_cours' AND denouement IS NULL AND etape_code = 'AN2') AS c1,
        COUNT(*) FILTER (
            WHERE uid = 'DLR5L17N53159'
              AND statut = 'en_cours'
              AND denouement IS NULL
              AND etape_code = 'CMP'
              AND derniere_decision ILIKE 'adopté%, dans les conditions prévues à l''article 45, alinéa 3, de la Constitution'
              AND derniere_decision != 'Accord'
        ) AS c2
    FROM dossiers
    WHERE uid IN ('DLR5L17N51215', 'DLR5L17N53159')
) t
WHERE c1 != 1 OR c2 != 1;

SELECT 'PASS: test_dossiers_snapshot.sql (' || COUNT(*) || ' dossiers dans l''extrait)' AS result
FROM dossiers;
