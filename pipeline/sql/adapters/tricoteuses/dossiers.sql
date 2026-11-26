-- =============================================================================
-- Table : `dossiers` (SQL DuckDB)
-- =============================================================================
-- Périmètre : 17e législature, Assemblée nationale (`legislature = 17`).
-- Grain : 1 ligne par dossier législatif (`assemblee.dossiers.uid`).
-- Sources :
--   - `assemblee.dossiers`              : métadonnées + arbre JSON `actesLegislatifs`
--   - `assemblee.organes`               : libellés des commissions saisies au fond
--   - `tisseuse.assemblee_text_search`  : exposés des motifs pré-découpés
-- =============================================================================

CREATE OR REPLACE TABLE dossiers AS
WITH RECURSIVE

-- -----------------------------------------------------------------------------
-- 1. SOURCES
-- -----------------------------------------------------------------------------

-- Dossiers sources (17e législature) : extraction des champs JSON scalaires
-- Grain : 1 ligne par dossier (uid)
source_dossiers AS (
    SELECT
        uid,
        legislature,
        (date_dernier_acte AT TIME ZONE 'Europe/Paris')::DATE AS date_dernier_acte,
        (date_prochain_acte AT TIME ZONE 'Europe/Paris')::DATE AS date_prochain_acte,
        data,
        json_extract_string(data, '$.procedureParlementaire.code') AS procedure_code,
        json_extract_string(data, '$.procedureParlementaire.libelle') AS procedure_libelle,
        json_extract_string(data, '$.titreDossier.titre') AS titre,
        json_extract_string(data, '$.titreDossier.titreChemin') AS titre_chemin,
        json_extract_string(data, '$.fusionDossier.cause') AS fusion_cause,
        json_extract_string(data, '$.fusionDossier.dossierAbsorbantRef') AS fusion_absorbant_ref
    FROM assemblee.dossiers
    WHERE legislature = 17
),

-- Organes parlementaires (commissions permanentes, groupes, etc.)
-- Grain : 1 ligne par organe (uid)
source_organes AS (
    SELECT
        uid,
        json_extract_string(data, '$.libelle') AS libelle
    FROM assemblee.organes
),

-- Fragments de texte correspondant aux exposés des motifs (17e législature)
-- Grain : 1 ligne par (document_uid, item_id)
source_expose_motifs AS (
    SELECT
        dossier_uid,
        document_uid,
        document_type_code,
        document_provenance,
        document_date,
        item_id,
        content
    FROM tisseuse.assemblee_text_search
    WHERE item_kind = 'expose_des_motifs'
      AND legislature = 17
      AND dossier_uid IS NOT NULL
      AND document_uid IS NOT NULL
      AND item_id IS NOT NULL
      AND content IS NOT NULL
),

-- -----------------------------------------------------------------------------
-- 2. APLATISSEMENT RÉCURSIF DE L'ARBRE `actesLegislatifs`
-- -----------------------------------------------------------------------------
-- Dans les données de l'Assemblée nationale, `data.actesLegislatifs` forme un
-- arbre hiérarchique (typiquement jusqu'à 4 niveaux : étape principale
-- `AN1` [Assemblée nationale — 1re lecture], `SN1` [Sénat — 1re lecture],
-- `CMP` [Commission mixte paritaire], `PROM` [Promulgation de la loi],
-- phase, sous-phase, acte feuille).
--
-- `TRY_CAST(json_extract(...) AS JSON[])` renvoie NULL si la clé est absente,
-- nulle ou non-tableau ; `CROSS JOIN UNNEST(...)` ignore alors proprement la ligne
-- et termine la récursion.
-- `sort_path` (`001.002.001.003`) préserve l'ordre chronologique/procédural en profondeur.

-- Aplatissement récursif de tous les niveaux de `actesLegislatifs`
actes_tous AS (
    -- Cas de base (niveau 1 : étapes de premier niveau du dossier)
    SELECT
        d.uid AS dossier_uid,
        1 AS depth,
        elem.idx::INTEGER AS top_idx,
        json_extract_string(elem.acte_json, '$.codeActe') AS top_code,
        json_extract_string(elem.acte_json, '$.libelleActe.nomCanonique') AS top_libelle,
        LPAD(elem.idx::VARCHAR, 3, '0') AS sort_path,
        elem.acte_json
    FROM source_dossiers d
    CROSS JOIN UNNEST(TRY_CAST(json_extract(d.data, '$.actesLegislatifs') AS JSON[]))
        WITH ORDINALITY AS elem(acte_json, idx) -- WITH ORDINALITY ajoute la position 1-based (idx) de chaque élément déplié (acte_json)

    UNION ALL

    -- Étape récursive (sous-actes des niveaux 2..N)
    SELECT
        parent.dossier_uid,
        parent.depth + 1 AS depth,
        parent.top_idx,
        parent.top_code,
        parent.top_libelle,
        parent.sort_path || '.' || LPAD(elem.idx::VARCHAR, 3, '0') AS sort_path,
        elem.acte_json
    FROM actes_tous parent
    CROSS JOIN UNNEST(TRY_CAST(json_extract(parent.acte_json, '$.actesLegislatifs') AS JSON[]))
        WITH ORDINALITY AS elem(acte_json, idx)
),

-- Parsing unique des attributs JSON de chaque acte aplati.
-- Note date : `LEFT(..., 10)` avant `TRY_CAST(... AS DATE)` évite tout décalage
-- d'un jour dû au fuseau horaire (`+01:00`/`+02:00`) lors de la conversion.
actes_extraits AS (
    SELECT
        dossier_uid,
        top_idx,
        top_code,
        sort_path,
        json_extract_string(acte_json, '$.xsiType') AS xsi_type, -- type d'acte issu du schéma XML de l'Assemblée nationale (AN) (ex. Etape_Type, DepotInitiative_Type, Promulgation_Type)
        TRY_CAST(LEFT(json_extract_string(acte_json, '$.dateActe'), 10) AS DATE) AS date_acte,
        json_extract_string(acte_json, '$.texteAssocieRef') AS texte_associe_ref,
        json_extract_string(acte_json, '$.organeRef') AS organe_ref,
        json_extract_string(acte_json, '$.codeLoi') AS code_loi,
        json_extract_string(acte_json, '$.statutConclusion.libelle') AS statut_conclusion_libelle,
        json_extract_string(acte_json, '$.decision.libelle') AS decision_libelle
    FROM actes_tous
),

-- -----------------------------------------------------------------------------
-- 3. MÉTRIQUES ET DERNIERS ÉVÉNEMENTS PAR DOSSIER (`MAX_BY` / `MIN_BY`)
-- -----------------------------------------------------------------------------

-- Dernière étape de niveau 1 atteinte par le dossier
-- (ex. AN1 : Assemblée nationale 1re lecture, SN1 : Sénat 1re lecture,
--  CMP : Commission mixte paritaire, PROM : Promulgation de la loi)
etape_en_cours AS (
    SELECT
        dossier_uid,
        MAX(top_idx) AS max_top_idx,
        -- STRUCT garantit que code et libelle proviennent du même top_idx en une seule passe MAX_BY (même si l'un est NULL)
        MAX_BY({'code': top_code, 'libelle': top_libelle}, top_idx) AS etape
    FROM actes_tous
    WHERE depth = 1
    GROUP BY dossier_uid
),

-- Agrégation unique des dates clés, indicateurs booléens et premier/derniers
-- actes par dossier (`MIN_BY` / `MAX_BY` ignorent les valeurs `NULL` issues du `CASE WHEN`)
actes_agreges AS (
    SELECT
        dossier_uid,
        MIN(CASE WHEN xsi_type = 'DepotInitiative_Type' THEN date_acte END) AS date_depot_initiative,
        MIN(date_acte) AS date_premier_acte,
        MAX(CASE WHEN xsi_type = 'Promulgation_Type' THEN date_acte END) AS date_promulgation,
        MAX(CASE WHEN xsi_type = 'Promulgation_Type' THEN 1 ELSE 0 END) = 1 AS has_promulgation,
        MAX(CASE WHEN xsi_type = 'RetraitInitiative_Type' THEN 1 ELSE 0 END) = 1 AS has_retrait,
        MAX(CASE WHEN xsi_type = 'DecisionMotionCensure_Type' AND decision_libelle ILIKE 'motion adoptée' THEN 1 ELSE 0 END) = 1 AS has_motion_adoptee,

        -- Premier document déposé à l'initiative (sert à distinguer PJL [Projet de loi]
        -- vs PPL [Proposition de loi] sur les procédures mixtes : code '5' [loi organique]
        -- et code '7' [loi constitutionnelle])
        MIN_BY(
            CASE WHEN xsi_type = 'DepotInitiative_Type' THEN texte_associe_ref END,
            sort_path
        ) AS first_depot_texte_ref,

        -- Dernière commission saisie au fond dans l'ordre du parcours législatif
        MAX_BY(
            CASE WHEN xsi_type = 'SaisieComFond_Type' THEN organe_ref END,
            sort_path
        ) AS commission_fond_uid,

        -- Numéro de loi promulguée issu du dernier acte `Promulgation_Type`
        MAX_BY(
            CASE WHEN xsi_type = 'Promulgation_Type' THEN code_loi END,
            sort_path
        ) AS code_loi,

        -- Dernière conclusion du Conseil constitutionnel (CC)
        MAX_BY(
            CASE WHEN xsi_type = 'ConclusionEtapeCC_Type' THEN statut_conclusion_libelle END, -- CC : Conseil constitutionnel
            sort_path
        ) AS conclusion_conseil_constitutionnel_libelle,

        -- Dernière décision sur une motion de censure (`Motion adoptée` / `Motion rejetée`)
        MAX_BY(
            CASE WHEN xsi_type = 'DecisionMotionCensure_Type' THEN decision_libelle END,
            sort_path
        ) AS last_motion_libelle,

        -- Dernière décision parlementaire (`Decision_Type`), avec son `top_idx` pour vérifier
        -- qu'elle appartient bien à l'étape finale du dossier.
        -- Tri par `(top_idx, date_acte, sort_path)` : au sein d'une même étape (notamment `CMP`
        -- [Commission mixte paritaire], où `CMP-DEC` [décision de la CMP] 'Accord' a un `sort_path`
        -- plus élevé que `CMP-DEBATS-AN-DEC` / `CMP-DEBATS-SN-DEC` [décisions en séance à l'Assemblée
        -- nationale / au Sénat]), la décision chronologiquement la plus récente l'emporte.
        MAX_BY(
            CASE
                WHEN xsi_type = 'Decision_Type' AND statut_conclusion_libelle IS NOT NULL
                THEN {'top_idx': top_idx, 'libelle': statut_conclusion_libelle}
            END,
            (top_idx, COALESCE(date_acte, DATE '1900-01-01'), sort_path)
        ) AS derniere_decision,

        -- 1re lecture rejetée par chambre (si AN1 et SN1 rejettent un PJL [Projet de loi] -> rejet définitif)
        COUNT(
            DISTINCT CASE
                WHEN top_idx IN (1, 2)
                 AND top_code IN ('AN1', 'SN1') -- AN1 : Assemblée nationale 1re lecture, SN1 : Sénat 1re lecture
                 AND xsi_type = 'Decision_Type'
                 AND (
                     statut_conclusion_libelle ILIKE 'rejet%'
                     OR statut_conclusion_libelle ILIKE 'considéré comme rejeté%'
                 )
                THEN top_idx
            END
        ) AS nb_rejets_1ere_lecture,

        -- Adoptions du texte de CMP (Commission mixte paritaire) par chambre (2 requises : AN [Assemblée nationale] + Sénat)
        COUNT(
            DISTINCT CASE
                WHEN top_code = 'CMP' -- CMP : Commission mixte paritaire
                 AND xsi_type = 'Decision_Type'
                 AND (
                     statut_conclusion_libelle ILIKE 'adopté%'
                     OR statut_conclusion_libelle ILIKE 'considéré comme adopté%'
                 )
                THEN sort_path
            END
        ) AS nb_adoptions_cmp
    FROM actes_extraits
    GROUP BY dossier_uid
),

-- -----------------------------------------------------------------------------
-- 4. EXPOSÉ DES MOTIFS (historique JSON par dossier)
-- exposé des motifs = justification rédigée par l'auteur / le rapporteur.
-- -----------------------------------------------------------------------------

-- Tableau JSON au grain `(document_uid, item_id)` ordonné chronologiquement
-- par `document_date`, puis `document_uid` et numéro de section (`item_id`)
expose_motifs AS (
    SELECT
        dossier_uid,
        to_json(
            LIST(
                {
                    'document_uid': document_uid,
                    'item_id': item_id,
                    'document_date': document_date,
                    'document_type_code': document_type_code,
                    'document_provenance': document_provenance,
                    'content': content
                }
                ORDER BY
                    document_date NULLS LAST,
                    document_uid,
                    TRY_CAST(SPLIT_PART(item_id, '-', -1) AS INTEGER) NULLS LAST,
                    item_id
            )
        ) AS expose_des_motifs
    FROM source_expose_motifs
    GROUP BY dossier_uid
),

-- -----------------------------------------------------------------------------
-- 5. ASSEMBLAGE & NORMALISATION MÉTIER
-- -----------------------------------------------------------------------------

-- Jointure explicite et normalisation des dimensions et métriques au grain `dossiers.uid`
dossiers_enrichis AS (
    SELECT
        d.uid,
        d.legislature,
        d.procedure_code,
        d.procedure_libelle,
        -- Normalisation du type de procédure à partir de `procedure_libelle` :
        -- les procédures mixtes (`Projet ou proposition de loi ...`) sont départagées
        -- grâce au préfixe du premier document déposé (`PRJL%` vs `PION%`), avec repli
        -- sur le titre si l'acte de dépôt ne référence pas encore de document.
        CASE
            WHEN d.procedure_libelle ILIKE 'Projet de %'
              OR (
                  d.procedure_libelle ILIKE 'Projet ou proposition de loi%'
                  AND (
                      agg.first_depot_texte_ref ILIKE 'PRJL%' -- PRJL : Projet de loi (initiative gouvernementale)
                      OR (agg.first_depot_texte_ref IS NULL AND d.titre ILIKE 'Projet de loi%')
                  )
              )
                THEN 'Projet de loi'
            WHEN d.procedure_libelle ILIKE 'Proposition de loi%'
              OR (
                  d.procedure_libelle ILIKE 'Projet ou proposition de loi%'
                  AND (
                      agg.first_depot_texte_ref ILIKE 'PION%' -- PION : Proposition de loi (initiative parlementaire)
                      OR (agg.first_depot_texte_ref IS NULL AND d.titre ILIKE 'Proposition de loi%')
                  )
              )
                THEN 'Proposition de loi'
            WHEN d.procedure_libelle ILIKE 'Résolution%' THEN 'Résolution'
            WHEN d.procedure_libelle ILIKE 'Rapport d''information%' THEN 'Rapport d''information'
            ELSE d.procedure_libelle
        END AS procedure,
        d.titre,
        CASE
            WHEN d.titre_chemin IS NOT NULL AND d.legislature IS NOT NULL
                THEN 'https://www.assemblee-nationale.fr/dyn/' || d.legislature || '/dossiers/' || d.titre_chemin
            ELSE NULL
        END AS dossier_url,
        d.fusion_cause,
        d.fusion_absorbant_ref,
        -- Date de dépôt : premier dépôt d'initiative, sinon premier acte, sinon `date_dernier_acte`
        COALESCE(agg.date_depot_initiative, agg.date_premier_acte, d.date_dernier_acte) AS date_depot,
        d.date_dernier_acte,
        d.date_prochain_acte,
        agg.date_promulgation,
        ec.max_top_idx,
        ec.etape.code AS etape_code,
        -- Désambiguïsation du libellé d'étape par chambre (`AN*` vs `SN*`)
        CASE
            WHEN ec.etape.code ILIKE 'AN%' -- AN* : étapes Assemblée nationale (AN1, AN2, ANLUNI, ANNLEC, ANLDEF, AN20, AN21)
                THEN 'Assemblée nationale — ' || COALESCE(ec.etape.libelle, ec.etape.code)
            WHEN ec.etape.code ILIKE 'SN%' -- SN* : étapes Sénat (SN1, SN2, SNNLEC)
                THEN 'Sénat — ' || COALESCE(ec.etape.libelle, ec.etape.code)
            ELSE COALESCE(ec.etape.libelle, ec.etape.code)
        END AS etape_libelle,
        agg.has_promulgation,
        agg.has_retrait,
        agg.has_motion_adoptee,
        agg.code_loi,
        agg.conclusion_conseil_constitutionnel_libelle,
        agg.last_motion_libelle,
        agg.derniere_decision.top_idx AS derniere_decision_top_idx,
        agg.derniere_decision.libelle AS derniere_decision_libelle,
        agg.nb_rejets_1ere_lecture,
        agg.nb_adoptions_cmp,
        agg.commission_fond_uid AS commission_saisie_au_fond_uid,
        org.libelle AS commission_saisie_au_fond_libelle,
        em.expose_des_motifs
    FROM source_dossiers d
    LEFT JOIN etape_en_cours ec ON ec.dossier_uid = d.uid
    LEFT JOIN actes_agreges agg ON agg.dossier_uid = d.uid
    LEFT JOIN source_organes org ON org.uid = agg.commission_fond_uid
    LEFT JOIN expose_motifs em ON em.dossier_uid = d.uid
),

-- Calcul de l'issue législative (`denouement`, `statut`, `derniere_decision`)
dossiers_statuts AS (
    SELECT
        *,

        -- Dénouement normalisé par priorité décroissante (NULL tant que le dossier est `en_cours`) :
        --   1. `promulgué` : acte de promulgation présent (`Promulgation_Type`)
        --   2. `fusionné`  : dossier fusionné dans un dossier absorbant (`fusion_absorbant_ref IS NOT NULL`)
        --   3. `retiré`    : initiative retirée par son auteur (`RetraitInitiative_Type`)
        --   4. `adopté`    :
        --        - motion de censure adoptée (`procedure_code = '13'` : Engagement de la responsabilité gouvernementale)
        --        - résolution (`procedure_code IN ('8', '22')` [Résolution / Résolution Article 34-1], jamais promulguée)
        --          adoptée en `ANLUNI` (Assemblée nationale — Lecture unique) ou jugée conforme par le Conseil constitutionnel (CC)
        --        - texte de loi définitivement adopté par le Parlement en attente de promulgation
        --          (`adopté% sans modification`, `ANLDEF` [Assemblée nationale — Lecture définitive] adopté/49.3,
        --          `CMP` [Commission mixte paritaire] adopté par les 2 chambres, ou validé `conforme%` / `partiellement conforme%`
        --          par le Conseil constitutionnel [CC] avant promulgation)
        --   5. `rejeté`    :
        --        - dernière motion de censure rejetée (`procedure_code = '13'`)
        --        - résolution (`procedure_code IN ('8', '22')`) rejetée (séance, commission
        --          préalable, ou Conseil constitutionnel [CC] `Non conforme`)
        --        - texte de loi censuré totalement par le Conseil constitutionnel (CC : `Non conforme`)
        --        - texte considéré comme rejeté en application de l'article 49, alinéa 3
        --        - proposition de loi (PPL) rejetée en 1re lecture de la 1re assemblée saisie (`max_top_idx = 1`)
        --        - projet de loi (PJL) rejeté en 1re lecture par les deux assemblées (`max_top_idx = 2`)
        --   6. `caduc`     : domaine réservé (fin de législature / dissolution ; non déclenché sur la 17e législature active)
        --   7. `NULL`      : tous les autres cas (dossier encore `en_cours`)
        CASE
            WHEN COALESCE(has_promulgation, FALSE) THEN 'promulgué'
            WHEN fusion_absorbant_ref IS NOT NULL THEN 'fusionné'
            WHEN COALESCE(has_retrait, FALSE) THEN 'retiré'
            WHEN procedure_code = '13' -- code '13' : Engagement de la responsabilité gouvernementale (motion de censure)
             AND COALESCE(has_motion_adoptee, FALSE) THEN 'adopté'
            WHEN procedure_code = '13' -- code '13' : Engagement de la responsabilité gouvernementale (motion de censure)
             AND last_motion_libelle ILIKE 'motion rejetée' THEN 'rejeté'
            -- Conseil constitutionnel (CC) (résolutions et lois non encore promulguées) :
            -- une censure totale (`Non conforme%`) clôt en `rejeté`, une validation (`Conforme%` /
            -- `Partiellement conforme%`) clôt en `adopté` en attendant une éventuelle promulgation.
            WHEN etape_code = 'CC' -- CC : Conseil constitutionnel
             AND conclusion_conseil_constitutionnel_libelle ILIKE 'non conforme%' THEN 'rejeté'
            WHEN etape_code = 'CC' -- CC : Conseil constitutionnel
             AND (
                conclusion_conseil_constitutionnel_libelle ILIKE 'conforme%'
                OR conclusion_conseil_constitutionnel_libelle ILIKE 'partiellement conforme%'
            ) THEN 'adopté'
            -- Résolutions (codes '8' [Résolution] et '22' [Résolution Article 34-1], jamais promulguées) : adoptées en séance ou art. 151-7
            WHEN procedure_code IN ('8', '22') -- codes '8' (Résolution) et '22' (Résolution Article 34-1)
             AND derniere_decision_top_idx = max_top_idx
             AND (
                 derniere_decision_libelle ILIKE 'adopté%'
                 OR derniere_decision_libelle ILIKE 'considérée comme définitive%'
             ) THEN 'adopté'
            -- Résolutions : rejetées en séance ou en commission préalable
            WHEN procedure_code IN ('8', '22') -- codes '8' (Résolution) et '22' (Résolution Article 34-1)
             AND derniere_decision_top_idx = max_top_idx
             AND derniere_decision_libelle ILIKE 'rejet%'
                THEN 'rejeté'
            -- Lois votées en termes identiques (`adopté sans modification`) ou en lecture définitive (`ANLDEF`)
            WHEN derniere_decision_top_idx = max_top_idx AND (
                derniere_decision_libelle ILIKE 'adopté% sans modification'
                OR (
                    etape_code = 'ANLDEF' -- ANLDEF : Assemblée nationale — Lecture définitive
                    AND (
                        derniere_decision_libelle ILIKE 'adopté%'
                        OR derniere_decision_libelle ILIKE 'considéré comme adopté%'
                    )
                )
            ) THEN 'adopté'
            -- Texte de CMP (Commission mixte paritaire) voté par les 2 chambres (1 seul vote garde le dossier `en_cours`)
            WHEN etape_code = 'CMP' -- CMP : Commission mixte paritaire
             AND COALESCE(nb_adoptions_cmp, 0) >= 2 THEN 'adopté'
            -- Texte considéré comme rejeté en application de l'article 49, alinéa 3 (motion de censure adoptée)
            WHEN derniere_decision_top_idx = max_top_idx
             AND derniere_decision_libelle ILIKE 'considéré comme rejeté%'
                THEN 'rejeté'
            -- PPL (Proposition de loi) rejetée dès la 1re assemblée (`max_top_idx = 1`) : non transmise à l'autre chambre
            WHEN procedure = 'Proposition de loi'
             AND max_top_idx = 1
             AND etape_code IN ('AN1', 'SN1') -- AN1 : Assemblée nationale 1re lecture, SN1 : Sénat 1re lecture
             AND derniere_decision_top_idx = max_top_idx
             AND (
                 derniere_decision_libelle ILIKE 'rejet%'
                 OR derniere_decision_libelle ILIKE 'considéré comme rejeté%'
             )
                THEN 'rejeté'
            -- PJL (Projet de loi) rejeté en 1re lecture à la fois à l'AN (Assemblée nationale) et au Sénat (un seul rejet poursuit la navette)
            WHEN procedure = 'Projet de loi'
             AND max_top_idx = 2
             AND COALESCE(nb_rejets_1ere_lecture, 0) = 2
                THEN 'rejeté'
            ELSE NULL
        END AS denouement,

        -- Statut de cycle de vie binaire dérivé de `denouement` (`en_cours` si `denouement IS NULL`, `close` sinon)
        CASE
            WHEN denouement IS NULL THEN 'en_cours'
            ELSE 'close'
        END AS statut,

        -- Libellé lisible de la dernière décision parlementaire ou du motif d'aboutissement enregistré
        CASE
            WHEN COALESCE(has_promulgation, FALSE) THEN
                CASE
                    WHEN NULLIF(TRIM(code_loi), '') IS NOT NULL
                        THEN 'Loi n° ' || TRIM(code_loi) || ' promulguée'
                    ELSE 'Loi promulguée'
                END
            WHEN fusion_absorbant_ref IS NOT NULL
                THEN COALESCE(fusion_cause, 'Dossier absorbé') || ' (' || fusion_absorbant_ref || ')'
            WHEN COALESCE(has_retrait, FALSE)
                THEN 'Initiative retirée'
            WHEN conclusion_conseil_constitutionnel_libelle IS NOT NULL
                THEN 'Conseil constitutionnel : ' || conclusion_conseil_constitutionnel_libelle
            WHEN procedure_code = '13' -- code '13' : Engagement de la responsabilité gouvernementale
             AND COALESCE(has_motion_adoptee, FALSE)
                THEN 'Motion adoptée'
            WHEN procedure_code = '13' -- code '13' : Engagement de la responsabilité gouvernementale
             AND last_motion_libelle IS NOT NULL
                THEN last_motion_libelle
            WHEN derniere_decision_libelle IS NOT NULL AND derniere_decision_top_idx = max_top_idx
                THEN derniere_decision_libelle
            ELSE NULL
        END AS derniere_decision
    FROM dossiers_enrichis
)

SELECT
    uid,
    legislature,
    procedure,
    procedure_code,
    procedure_libelle,
    titre,
    dossier_url,
    statut,
    denouement,
    derniere_decision,
    date_depot,
    date_dernier_acte,
    date_prochain_acte,
    date_promulgation,
    commission_saisie_au_fond_uid,
    commission_saisie_au_fond_libelle,
    etape_code,
    etape_libelle,
    expose_des_motifs
FROM dossiers_statuts
ORDER BY uid;

-- -----------------------------------------------------------------------------
-- 6. MÉTADONNÉES DUCKDB (`COMMENT ON TABLE` / `COMMENT ON COLUMN`)
-- -----------------------------------------------------------------------------

COMMENT ON TABLE dossiers IS
    'Périmètre : 17e législature, Assemblée nationale (legislature = 17). Grain : 1 ligne par dossier législatif (assemblee.dossiers.uid), enrichi par l''aplatissement récursif de actesLegislatifs, les libellés de assemblee.organes et les exposés des motifs de tisseuse.assemblee_text_search. Ordonné par uid.';

COMMENT ON COLUMN dossiers.uid IS
    'Source : assemblee.dossiers.uid. Signification : identifiant unique du dossier législatif. Transformation : aucune.';

COMMENT ON COLUMN dossiers.legislature IS
    'Source : assemblee.dossiers.legislature. Signification : numéro de législature du dossier (filtré à 17). Transformation : filtre WHERE legislature = 17.';

COMMENT ON COLUMN dossiers.procedure IS
    'Source : assemblee.dossiers.data ($.procedureParlementaire.libelle) et $.texteAssocieRef du 1er acte DepotInitiative_Type dans actesLegislatifs. Signification : type de procédure normalisé (Projet de loi, Proposition de loi, Résolution, Rapport d''information, ou libellé brut). Transformation : CASE sur procedure_libelle ; les procédures mixtes (Projet ou proposition de loi%) sont départagées par le préfixe du 1er document déposé (PRJL% vs PION%).';

COMMENT ON COLUMN dossiers.procedure_code IS
    'Source : assemblee.dossiers.data ($.procedureParlementaire.code). Signification : code brut de la procédure parlementaire. Transformation : extraction JSON.';

COMMENT ON COLUMN dossiers.procedure_libelle IS
    'Source : assemblee.dossiers.data ($.procedureParlementaire.libelle). Signification : libellé brut de la procédure parlementaire. Transformation : extraction JSON.';

COMMENT ON COLUMN dossiers.titre IS
    'Source : assemblee.dossiers.data ($.titreDossier.titre). Signification : titre officiel du dossier législatif. Transformation : extraction JSON.';

COMMENT ON COLUMN dossiers.dossier_url IS
    'Source : assemblee.dossiers.data ($.titreDossier.titreChemin) et assemblee.dossiers.legislature. Signification : URL du dossier sur le site de l''Assemblée nationale (NULL si titreChemin absent). Transformation : construction de https://www.assemblee-nationale.fr/dyn/<legislature>/dossiers/<titreChemin> lorsque $.titreDossier.titreChemin IS NOT NULL.';

COMMENT ON COLUMN dossiers.statut IS
    'Source : dérivé de dossiers.denouement. Signification : état d''avancement binaire du dossier (en_cours ou close). Transformation : ''en_cours'' lorsque denouement IS NULL, ''close'' dès qu''un dénouement terminal est établi.';

COMMENT ON COLUMN dossiers.denouement IS
    'Source : assemblee.dossiers.data (arbre $.actesLegislatifs : xsiType, statutConclusion.libelle, decision.libelle ; $.procedureParlementaire.code ; et $.fusionDossier.dossierAbsorbantRef). Signification : issue normalisée du dossier lorsqu''il est clos (promulgué, fusionné, retiré, adopté, rejeté, caduc ; NULL tant que le dossier est en_cours). La valeur caduc fait partie du domaine cible (fin de législature / dissolution) mais reste à 0 sur la 17e législature active. Transformation : CASE par priorité décroissante (Promulgation_Type -> promulgué, fusion_absorbant_ref IS NOT NULL -> fusionné, RetraitInitiative_Type -> retiré, motions de censure procedure_code = ''13'', décisions CC sur résolutions et lois non promulguées, résolutions 8/22 adoptées ou rejetées, lois définitivement adoptées en attente de promulgation via adopté sans modification / ANLDEF / CMP 2 chambres, texte considéré comme rejeté art. 49.3, PPL rejetée en 1re lecture de 1re assemblée ou PJL rejeté en 1re lecture des 2 assemblées -> rejeté, sinon NULL).';

COMMENT ON COLUMN dossiers.derniere_decision IS
    'Source : assemblee.dossiers.data ($.actesLegislatifs : Promulgation_Type/codeLoi, RetraitInitiative_Type, ConclusionEtapeCC_Type, DecisionMotionCensure_Type, Decision_Type ; $.procedureParlementaire.code ; et $.fusionDossier). Signification : libellé lisible de la dernière décision parlementaire ou du motif d''aboutissement enregistré (ex. Loi n° ... promulguée, modifié, adoptée sans modification ; NULL si aucune décision sur l''étape en cours). Transformation : CASE hiérarchique construisant le libellé (Loi promulguée avec ou sans codeLoi, motif/référence de fusion, retrait, conclusion du Conseil constitutionnel, décision de motion restreinte à procedure_code = ''13'', ou dernière Decision_Type ordonnée par (top_idx, date_acte, sort_path) uniquement si derniere_decision_top_idx = max_top_idx).';

COMMENT ON COLUMN dossiers.date_depot IS
    'Source : assemblee.dossiers.data ($.actesLegislatifs[*].dateActe) et assemblee.dossiers.date_dernier_acte. Signification : date de dépôt initial du dossier. Transformation : LEFT(dateActe, 10) casté en DATE (évite les décalages de fuseau horaire), puis COALESCE(MIN sur DepotInitiative_Type, MIN sur tous les actes, date_dernier_acte).';

COMMENT ON COLUMN dossiers.date_dernier_acte IS
    'Source : assemblee.dossiers.date_dernier_acte. Signification : date du dernier acte enregistré sur le dossier. Transformation : AT TIME ZONE ''Europe/Paris'' avant cast explicite en ::DATE.';

COMMENT ON COLUMN dossiers.date_prochain_acte IS
    'Source : assemblee.dossiers.date_prochain_acte. Signification : date du prochain acte prévu sur le dossier. Transformation : AT TIME ZONE ''Europe/Paris'' avant cast explicite en ::DATE.';

COMMENT ON COLUMN dossiers.date_promulgation IS
    'Source : assemblee.dossiers.data ($.actesLegislatifs[*].dateActe sur Promulgation_Type). Signification : date de promulgation de la loi (NULL si non promulgué). Transformation : LEFT(dateActe, 10) casté en DATE puis MAX sur les actes Promulgation_Type.';

COMMENT ON COLUMN dossiers.commission_saisie_au_fond_uid IS
    'Source : assemblee.dossiers.data ($.actesLegislatifs[*].organeRef sur SaisieComFond_Type). Signification : identifiant de la dernière commission saisie au fond. Transformation : MAX_BY(organe_ref, sort_path) sur les actes SaisieComFond_Type.';

COMMENT ON COLUMN dossiers.commission_saisie_au_fond_libelle IS
    'Source : assemblee.organes.data ($.libelle), joint sur assemblee.organes.uid = commission_saisie_au_fond_uid. Signification : libellé de la dernière commission saisie au fond. Transformation : extraction JSON et LEFT JOIN sur assemblee.organes.';

COMMENT ON COLUMN dossiers.etape_code IS
    'Source : assemblee.dossiers.data ($.actesLegislatifs[*].codeActe au niveau 1). Signification : code de la dernière étape de premier niveau atteinte (ex. AN1, SN1, CMP, PROM). Transformation : MAX_BY(top_code, top_idx) à depth = 1.';

COMMENT ON COLUMN dossiers.etape_libelle IS
    'Source : assemblee.dossiers.data ($.actesLegislatifs[*].libelleActe.nomCanonique et codeActe au niveau 1). Signification : libellé de la dernière étape de premier niveau, désambiguïsé par chambre. Transformation : MAX_BY(top_libelle, top_idx) à depth = 1, puis préfixage par ''Assemblée nationale — '' (AN%) ou ''Sénat — '' (SN%).';

COMMENT ON COLUMN dossiers.expose_des_motifs IS
    'Source : tisseuse.assemblee_text_search (item_kind = ''expose_des_motifs'', legislature = 17, dossier_uid IS NOT NULL). Signification : historique chronologique des exposés des motifs du dossier au format tableau JSON. Transformation : agrégation par dossier_uid via to_json(LIST({...})) ordonnée par document_date NULLS LAST, document_uid, numéro de section extrait de item_id (SPLIT_PART(item_id, ''-'', -1)::INTEGER), puis item_id.';
