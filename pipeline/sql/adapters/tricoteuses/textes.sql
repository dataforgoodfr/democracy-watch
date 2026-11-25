-- =============================================================================
-- Table : `textes` (SQL DuckDB)
-- =============================================================================
-- Périmètre : 17e législature, Assemblée nationale (`assemblee.dossiers.legislature = 17`).
-- Grain : 1 ligne par document parlementaire (`assemblee.documents.uid`)
--         rattaché à un dossier de la 17e législature présent dans `assemblee.dossiers`.
-- Sources :
--   - `assemblee.documents` : métadonnées documentaires (type, dépôt, notice, dates)
--   - `assemblee.dossiers`  : périmètre des dossiers (17e législature / L17) + arbre `actesLegislatifs`
--                             pour ordonner chronologiquement les textes
-- =============================================================================

CREATE OR REPLACE TABLE textes AS
WITH RECURSIVE

-- -----------------------------------------------------------------------------
-- 1. SOURCES
-- -----------------------------------------------------------------------------

-- Dossiers sources (17e législature) : utilisés à la fois comme filtre
-- d'intégrité référentielle et comme source de l'arbre `actesLegislatifs`
-- Grain : 1 ligne par dossier (uid)
source_dossiers AS (
    SELECT
        uid,
        data
    FROM assemblee.dossiers
    WHERE legislature = 17
),

-- Documents sources : extraction des champs JSON utiles.
-- Grain : 1 ligne par document (uid)
-- Note date : `BTA` (Texte adopté) / `TAP` (Texte adopté provisoire) en séance n'ayant pas de `dateDepot`,
-- on se replie sur `dateCreation`, puis `datePublication`, en prenant `LEFT(..., 10)`
-- pour éviter tout décalage d'un jour lié aux fuseaux horaires.
source_documents AS (
    SELECT
        uid,
        json_extract_string(data, '$.dossierRef') AS dossier_uid,
        json_extract_string(data, '$.classification.type.code') AS type_code,
        json_extract_string(data, '$.classification.type.libelle') AS type_document,
        json_extract_string(data, '$.classification.famille.depot.code') AS depot_code,
        json_extract_string(data, '$.notice.numNotice') AS numero,
        COALESCE(
            TRY_CAST(LEFT(json_extract_string(data, '$.cycleDeVie.chrono.dateDepot'), 10) AS DATE),
            TRY_CAST(LEFT(json_extract_string(data, '$.cycleDeVie.chrono.dateCreation'), 10) AS DATE),
            TRY_CAST(LEFT(json_extract_string(data, '$.cycleDeVie.chrono.datePublication'), 10) AS DATE)
        ) AS date_depot
    FROM assemblee.documents
),

-- -----------------------------------------------------------------------------
-- 2. APLATISSEMENT RÉCURSIF DE L'ARBRE `actesLegislatifs`
-- -----------------------------------------------------------------------------
-- Parcours récursif de tous les niveaux de `actesLegislatifs` afin de calculer
-- `sort_path` (`001.002.001.003`), qui donne l'ordre procédural exact de chaque
-- événement dans le dossier.

actes_tous AS (
    -- Cas de base (niveau 1)
    SELECT
        d.uid AS dossier_uid,
        elem.idx::INTEGER AS top_idx,
        LPAD(elem.idx::VARCHAR, 3, '0') AS sort_path,
        elem.acte_json
    FROM source_dossiers d
    CROSS JOIN UNNEST(TRY_CAST(json_extract(d.data, '$.actesLegislatifs') AS JSON[]))
        WITH ORDINALITY AS elem(acte_json, idx)

    UNION ALL

    -- Étape récursive (niveaux 2..N)
    SELECT
        parent.dossier_uid,
        parent.top_idx,
        parent.sort_path || '.' || LPAD(elem.idx::VARCHAR, 3, '0') AS sort_path,
        elem.acte_json
    FROM actes_tous parent
    CROSS JOIN UNNEST(TRY_CAST(json_extract(parent.acte_json, '$.actesLegislatifs') AS JSON[]))
        WITH ORDINALITY AS elem(acte_json, idx)
),

-- -----------------------------------------------------------------------------
-- 3. PREMIÈRE APPARITION DE CHAQUE DOCUMENT DANS LE PARCOURS LÉGISLATIF
-- -----------------------------------------------------------------------------
-- Un acte peut référencer un ou plusieurs documents via 4 emplacements JSON.
-- `WITH ORDINALITY` numérote leur ordre d'extraction au sein d'un même acte
-- (texte associé, puis texte adopté, puis annexes, puis texte de loi promulguée).

-- Position la plus précoce du document dans `actesLegislatifs` du dossier
doc_premiere_position AS (
    SELECT
        a.dossier_uid,
        ref.doc_uid,
        MIN_BY(
            {
                'top_idx': a.top_idx,
                'acte_date': TRY_CAST(LEFT(json_extract_string(a.acte_json, '$.dateActe'), 10) AS DATE),
                'sort_key': a.sort_path || '.' || LPAD(ref.idx::VARCHAR, 3, '0')
            },
            (
                a.top_idx,
                COALESCE(TRY_CAST(LEFT(json_extract_string(a.acte_json, '$.dateActe'), 10) AS DATE), DATE '9999-12-31'),
                a.sort_path || '.' || LPAD(ref.idx::VARCHAR, 3, '0')
            )
        ) AS first_pos
    FROM actes_tous a
    -- Assemble les 4 champs JSON dans l'ordre logique du parcours législatif,
    -- puis déplie chaque entrée avec son rang 1-based (`idx`) avant de filtrer les NULL
    CROSS JOIN UNNEST(list_concat(
        [
            json_extract_string(a.acte_json, '$.texteAssocieRef'), -- 1 : texte associé principal
            json_extract_string(a.acte_json, '$.texteAdopteRef')   -- 2 : texte adopté à l'issue de l'acte
        ],
        -- 3..N : liste éventuelle de textes associés complémentaires (`[]` si absente pour éviter un NULL dans `list_concat`)
        COALESCE(json_extract_string(a.acte_json, '$.textesAssocies[*].texteAssocieRef'), []),
        [
            json_extract_string(a.acte_json, '$.texteLoiRef')      -- dernier : texte de loi promulguée
        ]
    )) WITH ORDINALITY AS ref(doc_uid, idx)
    WHERE ref.doc_uid IS NOT NULL -- écarte les emplacements JSON absents sur cet acte
    GROUP BY a.dossier_uid, ref.doc_uid
),

-- -----------------------------------------------------------------------------
-- 4. ENRICHISSEMENT ET CALCUL DU RÔLE / RANG DANS LE DOSSIER
-- -----------------------------------------------------------------------------

-- L'INNER JOIN sur `source_dossiers` garantit le périmètre de la 17e législature (L17) et l'intégrité
-- référentielle de `dossier_uid` : dans l'extrait L17, ~1 703 documents pointent
-- vers d'anciens dossiers des 8e à 16e législatures (L8-L16) absents de `assemblee.dossiers` et sont exclus ici.
documents_enrichis AS (
    SELECT
        doc.uid,
        doc.dossier_uid,
        doc.type_code,
        doc.type_document,
        doc.depot_code,
        doc.numero,
        doc.date_depot,
        pos.first_pos.top_idx AS first_top_idx,
        pos.first_pos.acte_date AS first_acte_date,
        pos.first_pos.sort_key AS first_sort_key
    FROM source_documents doc
    INNER JOIN source_dossiers d ON d.uid = doc.dossier_uid
    LEFT JOIN doc_premiere_position pos ON pos.dossier_uid = d.uid AND pos.doc_uid = doc.uid
),

-- Normalisation du rôle parlementaire (`nature`) et numérotation continue par dossier
final AS (
    SELECT
        uid,
        dossier_uid,

        -- Rôle parlementaire : les marqueurs structurels dans `uid` (`BTC`, `BTA`, `TAP`)
        -- priment sur le couple `(type_code, depot_code)` pour distinguer texte de
        -- commission, texte adopté et texte déposé/en navette.
        CASE
            WHEN uid ILIKE '%BTC%' THEN 'Texte de commission'     -- BTC : Texte de commission
            WHEN uid ILIKE '%BTA%' THEN 'Texte adopté'            -- BTA : Texte adopté (en séance publique)
            WHEN uid ILIKE '%TAP%' THEN 'Texte adopté provisoire' -- TAP : Texte adopté provisoire
            WHEN type_code IN (
                'PION', -- PION : Proposition de loi
                'PRJL', -- PRJL : Projet de loi
                'PNRE'  -- PNRE : Proposition de résolution
            ) AND depot_code = 'INITDEP' -- INITDEP : Initiative en 1er dépôt
                THEN 'Texte déposé'
            WHEN type_code IN (
                'PION', -- PION : Proposition de loi
                'PRJL', -- PRJL : Projet de loi
                'PNRE'  -- PNRE : Proposition de résolution
            ) AND depot_code = 'INITNAV' -- INITNAV : Initiative en navette (transmis d'une chambre à l'autre)
                THEN 'Texte en navette'
            WHEN type_code = 'RAPP' THEN 'Rapport'                     -- RAPP : Rapport (commission, CMP...)
            WHEN type_code = 'RINF' THEN 'Rapport d''information'      -- RINF : Rapport d'information
            WHEN type_code = 'AVIS' THEN 'Avis'                        -- AVIS : Avis (commission saisie pour avis)
            WHEN type_code = 'ETDI' THEN 'Étude d''impact'             -- ETDI : Étude d'impact
            WHEN type_code = 'AVCE' THEN 'Avis du Conseil d''État'     -- AVCE : Avis du Conseil d'État
            WHEN type_code = 'ACIN' THEN 'Accord international'        -- ACIN : Accord international (traité/convention)
            WHEN type_code = 'MION' THEN 'Motion de censure'           -- MION : Motion (motion de censure art. 49.2 / 49.3)
            WHEN type_code = 'DECL' THEN 'Déclaration du Gouvernement' -- DECL : Déclaration du Gouvernement
            WHEN type_code = 'ALCN' THEN 'Allocution'                  -- ALCN : Allocution (du Président de l'Assemblée nationale)
            WHEN type_code = 'LETT' THEN 'Lettre rectificative'        -- LETT : Lettre rectificative
            ELSE COALESCE(type_document, type_code, 'Autre document')
        END AS nature,
        type_document,
        numero,

        -- Rang consécutif (1..N) : préserve les étapes de premier niveau (`first_top_idx`),
        -- trie chronologiquement au sein de chaque étape (`first_acte_date NULLS LAST`),
        -- puis départage le même jour par `first_sort_key`, `date_depot` et `uid`.
        ROW_NUMBER() OVER (
            PARTITION BY dossier_uid
            ORDER BY
                first_top_idx NULLS LAST,
                first_acte_date NULLS LAST,
                first_sort_key NULLS LAST,
                date_depot NULLS LAST,
                uid
        )::INTEGER AS rang_dans_dossier,
        date_depot
    FROM documents_enrichis
)

SELECT
    uid,
    dossier_uid,
    nature,
    type_document,
    numero,
    rang_dans_dossier,
    date_depot
FROM final
ORDER BY dossier_uid, rang_dans_dossier;
