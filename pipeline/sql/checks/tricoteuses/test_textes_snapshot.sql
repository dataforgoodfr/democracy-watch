-- =============================================================================
-- Tests SQL statiques (extrait figé) pour la table `textes`
-- =============================================================================
-- Périmètre  : spot-checks sur des UID et rangs précis issus de l'extrait figé
--              `data/canutes_extract_big_search_20261120.duckdb` (17e législature).
--              Ces tests ne doivent PAS tourner en CI sur la base mise à jour
--              quotidiennement : ils reposent sur des UID propres à cet extrait
--              et des positions exactes (`rang_dans_dossier`) susceptibles de
--              changer si de nouveaux documents sont rattachés au dossier.
--              Pour la CI quotidienne, voir `sql/canutes/tests/test_textes.sql`.
-- Prérequis  : exécuter `sql/canutes/textes.sql` sur l'extrait du 2026-11-20.
-- =============================================================================

-- 1. Cohérence du tri procédural : `Texte déposé` (B) précède `Texte de commission` (BTC)
--    qui précède `Texte adopté` (BTA) au sein d'un dossier de 1re lecture simple (`DLR5L17N51979`).
SELECT error('FAIL [textes.stage_order]: ordre B -> BTC -> BTA non respecté sur DLR5L17N51979')
FROM (
    SELECT
        MAX(CASE WHEN uid = 'PIONANR5L17B1342' THEN rang_dans_dossier END) AS r_b,
        MAX(CASE WHEN uid = 'PIONANR5L17BTC1473' THEN rang_dans_dossier END) AS r_btc,
        MAX(CASE WHEN uid = 'PIONANR5L17BTA0135' THEN rang_dans_dossier END) AS r_bta
    FROM textes
    WHERE dossier_uid = 'DLR5L17N51979'
) t
WHERE NOT COALESCE(r_b < r_btc AND r_btc < r_bta, FALSE);

-- 2. Spot-checks sur des documents et cas limites réels
--    Vérifie les métadonnées et le rang initial (`rang_dans_dossier = 1`) du texte déposé du PLF 2025.
SELECT error('FAIL [textes.spot_check.PRJLANR5L17B0324]: métadonnées PLF 2025 absentes ou inattendues')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE dossier_uid = 'DLR5L17N50198'
              AND nature = 'Texte déposé'
              AND type_document = 'Projet de loi'
              AND numero = '324'
              AND rang_dans_dossier = 1
              AND date_depot = DATE '2024-10-10'
        ) AS ok_cnt
    FROM textes
    WHERE uid = 'PRJLANR5L17B0324'
) t
WHERE cnt != 1 OR ok_cnt != 1;

--    Vérifie l'ordre chronologique historique de la CMP sur DLR5L17N50198
--    (adoption AN via 49.3 le 2025-02-05 avant l'adoption Sénat le 2025-02-06).
SELECT error('FAIL [textes.spot_check.DLR5L17N50198_order]: ordre chronologique CMP AN -> Sénat non respecté')
FROM (
    SELECT
        MAX(CASE WHEN uid = 'PRJLANR5L17BTA0042' THEN rang_dans_dossier END) AS r_an_bta,
        MAX(CASE WHEN uid = 'PRJLANR5L17TAP0042' THEN rang_dans_dossier END) AS r_an_tap,
        MAX(CASE WHEN uid = 'PRJLSNR5S459BTA0048' THEN rang_dans_dossier END) AS r_sn_bta
    FROM textes
    WHERE dossier_uid = 'DLR5L17N50198'
) t
WHERE NOT COALESCE(r_an_bta = 18 AND r_an_tap = 19 AND r_sn_bta = 20, FALSE);

--    Vérifie qu'un texte adopté classifié `RION` (Résolution) par l'OpenData AN est bien normalisé en `Texte adopté`.
SELECT error('FAIL [textes.spot_check.RIONANR5L17BTA0067]: BTA classé Résolution absent ou non normalisé en Texte adopté')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE nature = 'Texte adopté'
              AND type_document = 'Résolution'
              AND dossier_uid = 'DLR5L17N50452'
        ) AS ok_cnt
    FROM textes
    WHERE uid = 'RIONANR5L17BTA0067'
) t
WHERE cnt != 1 OR ok_cnt != 1;

--    Vérifie la classification `Texte en navette` (`INITNAV`) pour une proposition de loi transmise entre chambres.
SELECT error('FAIL [textes.spot_check.PIONANR5L17B1249]: texte en navette absent ou mal classifié')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE dossier_uid = 'DLR5L17N50715'
              AND nature = 'Texte en navette'
              AND type_document = 'Proposition de loi'
              AND numero = '1249'
        ) AS ok_cnt
    FROM textes
    WHERE uid = 'PIONANR5L17B1249'
) t
WHERE cnt != 1 OR ok_cnt != 1;

--    Vérifie qu'une motion de censure est classifiée `Motion de censure` avec `numero IS NULL`.
SELECT error('FAIL [textes.spot_check.MIONANR5L17-N1]: motion de censure absente ou mal normalisée')
FROM (
    SELECT
        COUNT(*) AS cnt,
        COUNT(*) FILTER (
            WHERE dossier_uid = 'DLR5L17N50557'
              AND nature = 'Motion de censure'
              AND type_document = 'Motion'
              AND numero IS NULL
        ) AS ok_cnt
    FROM textes
    WHERE uid = 'MIONANR5L17-N1'
) t
WHERE cnt != 1 OR ok_cnt != 1;

SELECT 'PASS: test_textes_snapshot.sql (' || COUNT(*) || ' textes dans l''extrait)' AS result
FROM textes;
