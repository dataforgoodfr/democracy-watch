-- =====================================================================
-- articles.sql
-- Lit tisseuse.assemblee_text_search (17e législature, articles uniquement ; nom à modifier selon la base)
-- et remplit la table "articles" : document_uid, item_id, numero, libelle, rang, supprime, contenu, alineas et nb_alineas
--      - docucment _uid = identifiant du texte (ex. : "JORFARTI000046622119") ;
--      - item_id = identifiant de l'article (ex: _TocArt1) ;
--      - "numero" = numéro de l'article (ex: 2 bis)
--      - "libelle" = libellé complet de l'article (ex: "Article 2 bis (nouveau)") ;
--      - "rang" = ordre de lecture dans le texte (comme numero mais sans prendre en compte bis, ter, etc) ;
--      - "supprime" = "True" si l'article est supprimé ;
--      - "contenu" = texte complet de l'article ;
--      - "alineas" est une liste de textes : alineas[4] = texte de l'alinéa 4
--      - "nb_alineas" est le nombre d'alinéas de l'article. Pour un article sans numéros d'alinéa, alineas = NULL et nb_alineas = NULL

-- CHOIX : les exposés des motifs ont été exclus.
-- =====================================================================


-- PARTIE 1 : Création dela table `articles`, sans les alinéas pour l'instant


CREATE OR REPLACE TABLE articles AS
WITH base AS (
    SELECT
        document_uid,
        item_id,
        article_number,
        item_label,
        content,
        regexp_matches(content, '^(Article [^()]*)?\(Supprimé\)') AS supprime,
        -- Numéro d'article décomposé pour pouvoir le trier : « 3 bis A » = 3 / bis / A
        TRY_CAST(regexp_extract(article_number, '^(\d+)', 1) AS INTEGER) AS num,
        coalesce(list_position(
            ['bis','ter','quater','quinquies','sexies','septies','octies','novies',
             'decies','undecies','duodecies'],
            regexp_extract(article_number, '^\d+ (\w+)', 1)), 0) AS multiplicatif,
        regexp_extract(article_number, '([A-Z]+)$', 1) AS lettres
    FROM tisseuse.assemblee_text_search
    WHERE legislature = 17
      AND item_kind = 'article'
)
SELECT
    document_uid,
    item_id,
    article_number AS numero,
    row_number() OVER (
        PARTITION BY document_uid
        ORDER BY (article_number IS DISTINCT FROM 'liminaire'),
                 num NULLS LAST,
                 multiplicatif,
                 (lettres = ''),
                 lettres,
                 item_id
    ) AS rang,
    item_label AS libelle,
    supprime,
    content AS contenu
FROM base;


-- PARTIE 2 : Ajout de la colonne `alineas` et de nb_alineas


-- Dans le texte, les numéros d'alinéa sont collés au premier mot ("1L'Assemblée nationale, 2Vu l'article… etc) mais le texte contient aussi des nombres qui ne sont PAS des alinéas (« L. 253-7 », « 2026 », « 1er », « article 12 »).
-- Principe : les vrais numéros se suivent 1, 2, 3… ; on cherche donc, l'un après l'autre, le « prochain numéro attendu ».

-- La règle : à quoi ressemble le numéro d'alinéa attendu ?
CREATE OR REPLACE TEMP MACRO est_numero_alinea(chiffres, suivant, attendu) AS (
    -- Cas 1 : le numéro attendu, collé à une lettre, un guillemet ou un tiret long (« 2Vu », « 10« », « 3– » )
    (chiffres = CAST(attendu AS VARCHAR)
        AND regexp_matches(suivant, '^[\p{L}«"“(\[–—]'))
    OR
    -- Cas 2 : le numéro attendu est collé à un numéro de liste (1 ou 2 chiffres, pas une année) : « 181. », « 21° », « 321) »
    (starts_with(chiffres, CAST(attendu AS VARCHAR))
        AND length(chiffres) - length(CAST(attendu AS VARCHAR)) BETWEEN 1 AND 2
        AND substr(chiffres, length(CAST(attendu AS VARCHAR)) + 1, 1) <> '0'
        AND NOT regexp_matches(chiffres, '^(19|20)\d{2}$')
        AND suivant IN ('.', '°', ')'))
);

-- Étape A : les articles à traiter.
CREATE OR REPLACE TEMP TABLE _articles_src AS
SELECT row_number() OVER (ORDER BY document_uid, item_id) AS id,
       document_uid, item_id, content
FROM tisseuse.assemblee_text_search
WHERE legislature = 17
  AND item_kind = 'article';

-- Étape B : repérer tous les « candidats » : un nombre précédé d'une espace ou du début, suivi d'un caractère qui n'est ni un chiffre ni une espace), puis couper le texte à chaque candidat.
-- On protège d'abord les ordinaux (1er, 2e, 3ème) avec un caractère invisible chr(1).
CREATE OR REPLACE TEMP TABLE _candidats AS
WITH marque AS (
    SELECT id,
           regexp_replace(
               regexp_replace(content, '(\d+)(er|ère|re|e|ème|nd|nde)\b', '\1' || chr(1) || '\2', 'g'),
               '(^|\s)(\d+)([^\s\d])',
               '\1' || chr(2) || '\2' || chr(3) || '\3',
               'g') AS t
    FROM _articles_src
    WHERE regexp_matches(content, '^\s*\d')          -- seuls les articles qui commencent par un nombre
)
SELECT id,
       ord - 1 AS ord,
       CASE WHEN strpos(piece, chr(3)) > 0 THEN split_part(piece, chr(3), 1) END AS chiffres,
       CASE WHEN strpos(piece, chr(3)) > 0 THEN substr(piece, strpos(piece, chr(3)) + 1)
            ELSE piece END AS corps
FROM marque, unnest(string_split(t, chr(2))) WITH ORDINALITY AS u(piece, ord);

-- Étape C : garder la suite 1, 2, 3… (chaque numéro doit venir après le précédent).
CREATE OR REPLACE TEMP TABLE _chaine AS
WITH RECURSIVE chaine(id, ord, n) AS (
    -- Départ : le numéro 1 doit être tout au début de l'article
    SELECT c.id, c.ord, 1
    FROM _candidats c
    JOIN _candidats debut ON debut.id = c.id AND debut.ord = 0 AND trim(debut.corps) = ''
    WHERE c.ord = 1 AND est_numero_alinea(c.chiffres, left(c.corps, 1), 1)
    UNION ALL
    -- Répétition : On cherche le « numéro suivant » qui apparaît après le précédent
    SELECT c.id, min(c.ord), ch.n + 1
    FROM chaine ch
    JOIN _candidats c
      ON c.id = ch.id AND c.ord > ch.ord
     AND est_numero_alinea(c.chiffres, left(c.corps, 1), ch.n + 1)
    GROUP BY c.id, ch.n
)
SELECT * FROM chaine;

-- Étape D : reconstruire le texte de chaque alinéa.
-- Un faux numéro (« 12 » au milieu d'un alinéa) est remis dans le texte ; un numéro de liste collé (« 181. ») garde sa partie « 1. ».
CREATE OR REPLACE TEMP TABLE _alineas AS
WITH morceaux AS (
    SELECT c.id, c.ord, c.chiffres, c.corps,
           ch.n AS n_valide,
           max(ch.n) OVER (PARTITION BY c.id ORDER BY c.ord) AS alinea
    FROM _candidats c
    LEFT JOIN _chaine ch ON ch.id = c.id AND ch.ord = c.ord
)
SELECT s.document_uid, s.item_id, m.alinea,
       trim(replace(string_agg(
           CASE WHEN m.n_valide IS NOT NULL
                     THEN substr(m.chiffres, length(CAST(m.n_valide AS VARCHAR)) + 1) || m.corps
                WHEN m.chiffres IS NOT NULL
                     THEN m.chiffres || m.corps
                ELSE m.corps END,
           '' ORDER BY m.ord), chr(1), '')) AS texte                -- string_agg colle les morceaux de chaque alinéa dans l'ordre, puis on retire le caractère invisible chr(1).
FROM morceaux m
JOIN _articles_src s USING (id)
WHERE m.alinea IS NOT NULL
GROUP BY s.document_uid, s.item_id, m.alinea;

-- Étape E : ranger les alinéas dans la colonne `alineas` de la table `articles`
-- (les articles sans numéros gardent alineas = NULL).
ALTER TABLE articles ADD COLUMN alineas VARCHAR[];
UPDATE articles
SET alineas = l.alineas
FROM (SELECT document_uid, item_id, list(texte ORDER BY alinea) AS alineas
      FROM _alineas
      GROUP BY document_uid, item_id) AS l
WHERE articles.document_uid = l.document_uid
  AND articles.item_id = l.item_id;

-- Étape F : le nombre d'alinéas (vide si l'article n'a pas d'alinéas numérotés).
ALTER TABLE articles ADD COLUMN nb_alineas INTEGER;
UPDATE articles SET nb_alineas = len(alineas);

DROP TABLE _alineas;
DROP TABLE _chaine;
DROP TABLE _candidats;
DROP TABLE _articles_src;
