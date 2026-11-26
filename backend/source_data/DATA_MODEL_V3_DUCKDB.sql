-- =====================================================================
-- Clair : modèle de données V3, version DuckDB (v2.0)
-- Base de travail du pipeline (staging.duckdb), reconstruite vide à chaque
-- passage. Toute ligne incohérente est refusée à l'insertion, ce qui arrête
-- le chargement ; les règles que DuckDB ne sait pas vérifier à l'insertion
-- sont des macros de contrôle (fin de fichier), appelées en étape 7.
-- Exécution : duckdb staging.duckdb -c ".read DATA_MODEL_V3_DUCKDB.sql"
--
-- Conventions (reprises du modèle Postgres DATA_MODEL_V3.sql) :
--   - clés internes INTEGER (SMALLINT pour les petits référentiels),
--     attribuées par le pipeline (tables de correspondance id_*), sauf
--     imports qui a sa séquence ; identifiants sources en VARCHAR UNIQUE ;
--   - noms en français snake_case ; booléens préfixés est_ ;
--   - colonnes de contexte = copie d'un identifiant du parent, vérifiée
--     par une clé étrangère composite ;
--   - colonnes d'entrepôt sur toutes les tables : created_at, updated_at,
--     import_id ; plus source_hash sur les tables alimentées document par
--     document depuis une source ;
--   - chaque colonne de type ENUM rappelle ses valeurs en commentaire ;
--   - libellés d'affichage des ENUM dans des macros libelle_*() ;
--   - un contrôle qui dépend d'une valeur d'ENUM cite toutes les valeurs
--     (CASE exhaustif, ELSE false) : une valeur ajoutée sans règle, ou mal
--     orthographiée dans le contrôle, fait échouer l'insertion au lieu de
--     passer sans contrôle.
--
-- Adaptations à DuckDB (mesures : ../../target_archi/MESURES_DUCKDB.md) :
--   - stockage en colonnes : l'ordre des colonnes n'a plus d'effet sur la
--     place ; colonnes rangées dans un ordre logique (clés, attributs,
--     colonnes d'entrepôt) ;
--   - tables *_contenus fusionnées dans leur table principale (articles,
--     amendements, interventions) : une requête ne lit que les colonnes
--     qu'elle cite, séparer le texte long n'apporte rien ;
--   - pas de daterange : date_debut / date_fin + CHECK d'ordre ; les
--     chevauchements (EXCLUDE de Postgres) deviennent des macros de contrôle ;
--   - colonnes booléennes générées (cibles de clés composites) remplacées
--     par des colonnes normales + CHECK qui imposent la même valeur ;
--   - pas de cascade (ON UPDATE / ON DELETE CASCADE refusés) : la base est
--     reconstruite à chaque passage, l'ordre de chargement suffit ;
--   - pas de ALTER TABLE ... ADD FOREIGN KEY : chaque table référencée est
--     créée avant ses enfants (reunions avant amendement_discussions) ;
--   - auto-références : parent et enfant en instructions INSERT séparées ;
--   - une ligne référencée par une clé étrangère ne peut être ni supprimée
--     ni mise à jour sur une colonne indexée (DuckDB traite l'UPDATE en
--     suppression + insertion) : la base se recharge, elle ne se corrige pas ;
--   - pas de déclencheurs : created_at / updated_at posés par le pipeline,
--     DEFAULT current_timestamp en secours, CHECK updated_at >= created_at ;
--   - pas de tsvector : l'index plein texte (extension fts) est construit
--     par l'API sur amendements et interventions, pas dans cette base ;
--   - pas d'index secondaires : DuckDB crée un index (ART) pour chaque clé
--     primaire, UNIQUE et clé étrangère ; les filtres s'appuient sur les
--     statistiques min/max par bloc ;
--   - ENUM non modifiables (pas de ALTER TYPE) : modifier ce fichier suffit,
--     la base est recréée à chaque passage ;
--   - pas de COLLATE "C" : la comparaison binaire est celle par défaut.
--
-- Contrôles en plus du modèle Postgres (profilés sur les données de clair) :
--   chaînes obligatoires non vides, formats d'identifiants (uid AN, PA,
--   matricule Sénat, Wikidata), cohérence uid / colonnes dérivées (nature,
--   numéro, délibération), dates dans le bon ordre, décomptes positifs et
--   cohérents, couleurs, URL, courriels, champs de loi réservés aux
--   dossiers promulgués.
-- Écart au modèle Postgres : amendements reçoit organe_examen_id et
--   deliberation, car le numéro n'est unique que par texte, organe
--   d'examen et délibération (23 620 doublons (texte, numéro) dans clair).
-- =====================================================================

SET force_compression = 'zstd';

-- =====================================================================
-- MACROS GÉNÉRALES
-- =====================================================================

-- Chaîne renseignée : NULL accepté (la nullité relève de NOT NULL), mais
-- pas une chaîne vide ou faite d'espaces.
CREATE MACRO non_vide(s) AS s IS NULL OR trim(s) <> '';

-- Empreinte md5 en hexadécimal (32 caractères), telle que produite par
-- md5(ligne::VARCHAR) au chargement.
CREATE MACRO est_md5(h) AS h IS NULL OR regexp_full_match(h, '[0-9a-f]{32}');

-- URL absolue http(s).
CREATE MACRO est_url(u) AS u IS NULL OR regexp_full_match(u, 'https?://\S+');

-- Deux périodes [debut, fin] se chevauchent (fin NULL = en cours).
-- Remplace l'opérateur && des daterange.
CREATE MACRO se_chevauchent(debut_a, fin_a, debut_b, fin_b) AS
  debut_a <= coalesce(fin_b, DATE '9999-12-31') AND debut_b <= coalesce(fin_a, DATE '9999-12-31');

-- Une période [debut, fin] contient la date d. Remplace plage @> d.
-- Requête : WHERE organe_id = X AND en_cours_le(date_debut, date_fin, D).
CREATE MACRO en_cours_le(debut, fin, d) AS
  (debut IS NULL OR debut <= d) AND (fin IS NULL OR d <= fin);


-- =====================================================================
-- VOCABULAIRES FERMÉS (ENUM)
-- Un ENUM est stocké comme un entier (1 octet jusqu'à 255 valeurs).
-- Récapitulatif d'usage : ../ENUMS_V3.md.
-- =====================================================================

-- Assemblée élue : les deux chambres du Parlement, et le Parlement européen
-- (prévu ; aucun chargement ne l'alimente encore).
CREATE TYPE chambre AS ENUM ('assemblee', 'senat', 'parlement_europeen');

-- Unité de numérotation d'une chambre : législature (AN), session (Sénat),
-- législature européenne (PE, ex. 10 pour 2024-2029).
CREATE TYPE type_periode AS ENUM ('legislature', 'session_senat', 'legislature_europeenne');

-- Type d'organe : codeType des données AN (« AMO »), pour les deux chambres
-- (l'AN code aussi les organes du Sénat : SENAT, COMSENAT, GROUPESENAT...).
-- Seul ALLIANCE n'est pas un code AN : coalition de groupes ou de partis
-- (ex. NUPES, NFP), reliée à ses membres par organe_liens. Famille et
-- libellé de chaque type : macros famille_du_type() et libelle_type_organe().
-- Les circonscriptions (codeType CIRCONSCRIPTION) ont leur propre table.
CREATE TYPE type_organe AS ENUM (
  -- instances
  'ASSEMBLEE', 'SENAT', 'BUREAU', 'CONFPT',
  -- groupes
  'GP', 'GROUPESENAT', 'PARPOL', 'ALLIANCE', 'GA', 'GE', 'GEVI',
  -- commissions
  'COMPER', 'COMSENAT', 'CMP', 'CNPE', 'CNPS', 'COMSPSENAT', 'COMNL',
  -- missions
  'MISINFO', 'MISINFOCOM', 'MISINFOPRE',
  -- délégations et offices
  'DELEG', 'DELEGBUREAU', 'DELEGSENAT', 'OFFPAR',
  -- exécutif
  'GOUVERNEMENT', 'MINISTERE', 'PRESREP',
  -- juridictions et organismes extérieurs
  'CONSTITU', 'HCJ', 'CJR', 'API', 'ORGEXTPARL');

-- Famille d'un type d'organe, pour les regroupements et filtres.
CREATE TYPE famille_organe AS ENUM (
  'instance', 'groupe', 'commission', 'mission', 'delegation', 'gouvernement', 'juridiction', 'externe');

-- Lien daté entre deux organes (organe_liens).
-- ex. membre_de = groupe LFI-NUPES membre de l'alliance NUPES ;
--     succede_a = groupe SOC de la XVIIe vers SOC de la XVIe ;
--     affilie_a = groupe politique vers son parti, ou vers un groupe du PE.
CREATE TYPE type_lien_organe AS ENUM ('membre_de', 'succede_a', 'affilie_a');

-- Qualité d'une personne dans un organe (mandats). Codes neutres ; le
-- libellé accordé (Présidente, Président, Président·e) vient de la macro
-- libelle_qualite(). Rang (« Premier vice-président ») dans mandats.rang,
-- libellé source plus précis (« Rapporteur spécial au nom de la commission
-- des finances : Sécurité ») dans mandats.qualite_precision.
CREATE TYPE qualite_mandat AS ENUM (
  'membre', 'membre_titulaire', 'membre_suppleant', 'membre_de_droit', 'membre_bureau',
  'president', 'president_de_droit', 'president_delegue', 'president_executif', 'co_president',
  'vice_president', 'vice_president_delegue', 'vice_president_honneur',
  'secretaire', 'secretaire_adjoint', 'secretaire_general', 'secretaire_general_adjoint',
  'questeur', 'tresorier', 'tresorier_adjoint',
  'rapporteur', 'co_rapporteur', 'rapporteur_adjoint', 'rapporteur_general', 'rapporteur_special',
  'rapporteur_pour_avis', 'rapporteur_thematique',
  'porte_parole', 'delegue', 'representant', 'representant_suppleant', 'chef',
  'president_republique', 'premier_ministre', 'ministre', 'ministre_delegue', 'secretaire_etat', 'en_mission',
  'collaborateur', 'autre');

-- Civilité publiée par la source (AN : civ ; Sénat : quacod, « Mlle » = mme).
CREATE TYPE civilite AS ENUM ('m', 'mme');

-- Genre déclaré publiquement par la personne. Jamais déduit du prénom ni de
-- la civilité : NULL tant qu'aucune déclaration n'est connue.
CREATE TYPE genre AS ENUM ('femme', 'homme', 'non_binaire');

-- Niveau du diplôme le plus élevé d'une formation.
CREATE TYPE niveau_formation AS ENUM (
  'sans_diplome', 'secondaire', 'bac', 'bac_2', 'licence', 'master', 'doctorat', 'grande_ecole');

-- Type de coordonnée publique. Union des types AN (adresses de type
-- AdresseMail, AdresseTelephonique, AdresseSiteWeb) et Sénat (sens_typurl).
-- Adresses postales hors modèle. Format : macro coordonnee_valide() ; URL
-- d'un identifiant de réseau : macro url_coordonnee().
CREATE TYPE type_coordonnee AS ENUM (
  'email', 'telephone', 'telecopie', 'site', 'blog', 'page_institutionnelle',
  'x', 'facebook', 'instagram', 'linkedin', 'bluesky', 'threads', 'tiktok', 'youtube', 'tumblr',
  'mediapart', 'huffpost');

-- Procédure parlementaire d'un dossier. Codes communs aux deux chambres :
-- la correspondance des codes sources (AN : procedureParlementaire.code
-- numérique ; Sénat : dosleg_typloi) est faite à l'import. Projet ou
-- proposition : nature du premier texte du dossier. Libellé : macro
-- libelle_procedure().
CREATE TYPE procedure_parlementaire AS ENUM (
  'loi_ordinaire', 'loi_organique', 'loi_constitutionnelle', 'loi_programmation',
  'loi_finances', 'loi_finances_rectificative', 'loi_approbation_comptes',
  'loi_financement_secu', 'loi_financement_secu_rectificative',
  'ratification_traite', 'loi_referendum_art11',
  'resolution', 'resolution_34_1', 'resolution_europeenne', 'resolution_reglement',
  'commission_enquete', 'prerogatives_commission_enquete', 'mission_information', 'rapport_information',
  'motion_referendaire', 'engagement_responsabilite', 'declaration_gouvernement',
  'message_president_republique', 'allocution_president_assemblee', 'responsabilite_penale_president',
  'immunite', 'petition');

-- Nature d'un texte dans la navette.
-- ex. projet = PRJLANR5L17B3058, proposition = PIONANR5L17B1364 (ou PNRE...),
--     texte_commission = ...BTC1364, texte_adopte = ...BTA0749
CREATE TYPE nature_texte AS ENUM ('projet', 'proposition', 'texte_commission', 'texte_adopte');

-- Avancement d'un dossier législatif.
CREATE TYPE statut_dossier AS ENUM ('en_cours', 'clos');

-- Dénouement d'un dossier clos (NULL tant qu'il est en cours).
CREATE TYPE denouement_dossier AS ENUM ('promulgue', 'adopte', 'rejete', 'caduc', 'fusionne', 'retire');

-- Avancement d'un amendement. Seul « traite » implique un dénouement.
CREATE TYPE statut_amendement AS ENUM ('en_recevabilite', 'a_discuter', 'en_traitement', 'traite');

-- Dénouement d'un amendement traité : la catégorie, qui sert aux statistiques.
-- Le détail éventuel est dans motif_denouement. Analyse : ../DENOUEMENTS.md.
CREATE TYPE categorie_denouement AS ENUM (
  'adopte', 'rejete', 'retire', 'tombe', 'non_soutenu', 'irrecevable', 'autre');

-- Motif détaillé d'un dénouement, quand la source le précise. Les valeurs
-- sont rangées par catégorie ; la macro categorie_du_motif() donne la
-- catégorie de chaque motif, et un CHECK impose la cohérence des deux.
-- Pas de motif pour un simple 'rejete', 'tombe' ou 'non_soutenu'.
CREATE TYPE motif_denouement AS ENUM (
  -- catégorie adopte
  'adopte_modifie',
  -- catégorie retire
  'retire_avant_publication', 'retire_apres_publication', 'retire_avant_seance',
  -- catégorie irrecevable (un motif par libellé AN ; 'irrecevable' du Sénat = pas de motif)
  'irrecevable_40_charge', 'irrecevable_40_autre', 'irrecevable_gage', 'irrecevable_credits',
  'irrecevable_lolf', 'irrecevable_lolf_autre', 'irrecevable_lolfss', 'irrecevable_lolfss_autre',
  'irrecevable_premiere_partie', 'irrecevable_seconde_partie', 'irrecevable_98', 'irrecevable_autre',
  'cavalier_45', 'cavalier_social', 'cavalier_budgetaire', 'entonnoir_45', 'cmp_45',
  'satisfait_inoperant_42', 'domaine_loi_41', 'reglementaire_37', 'habilitation_38',
  'injonction_20', 'ordre_du_jour_48', 'ratification_53', 'loi_organique_127',
  'hors_champ', 'hors_delais',
  -- catégorie autre
  'doublon', 'efface', 'satisfait', 'non_examine');

-- Place d'un amendement dans sa discussion groupée (commune ou identique).
CREATE TYPE position_discussion AS ENUM ('premier', 'milieu', 'dernier');

-- Avancement d'un lot d'import.
CREATE TYPE statut_import AS ENUM ('en_cours', 'termine', 'echoue');

-- Catégorie de chaque motif de dénouement (macro utilisable dans un CHECK
-- et dans les requêtes). Un motif absent de la liste donne NULL, et le
-- CHECK le refuse : tout nouveau motif doit être ajouté ici.
CREATE MACRO categorie_du_motif(m) AS CAST(CASE
  WHEN m = 'adopte_modifie' THEN 'adopte'
  WHEN m IN ('retire_avant_publication', 'retire_apres_publication', 'retire_avant_seance') THEN 'retire'
  WHEN m IN ('doublon', 'efface', 'satisfait', 'non_examine') THEN 'autre'
  WHEN m IN ('irrecevable_40_charge', 'irrecevable_40_autre', 'irrecevable_gage', 'irrecevable_credits',
             'irrecevable_lolf', 'irrecevable_lolf_autre', 'irrecevable_lolfss', 'irrecevable_lolfss_autre',
             'irrecevable_premiere_partie', 'irrecevable_seconde_partie', 'irrecevable_98', 'irrecevable_autre',
             'cavalier_45', 'cavalier_social', 'cavalier_budgetaire', 'entonnoir_45', 'cmp_45',
             'satisfait_inoperant_42', 'domaine_loi_41', 'reglementaire_37', 'habilitation_38',
             'injonction_20', 'ordre_du_jour_48', 'ratification_53', 'loi_organique_127',
             'hors_champ', 'hors_delais') THEN 'irrecevable'
END AS categorie_denouement);

-- Famille de chaque type d'organe. Un type absent de la liste donne NULL :
-- tout nouveau type doit être ajouté ici (contrôle types_sans_famille()).
CREATE MACRO famille_du_type(t) AS CAST(CASE
  WHEN t IN ('ASSEMBLEE', 'SENAT', 'BUREAU', 'CONFPT') THEN 'instance'
  WHEN t IN ('GP', 'GROUPESENAT', 'PARPOL', 'ALLIANCE', 'GA', 'GE', 'GEVI') THEN 'groupe'
  WHEN t IN ('COMPER', 'COMSENAT', 'CMP', 'CNPE', 'CNPS', 'COMSPSENAT', 'COMNL') THEN 'commission'
  WHEN t IN ('MISINFO', 'MISINFOCOM', 'MISINFOPRE') THEN 'mission'
  WHEN t IN ('DELEG', 'DELEGBUREAU', 'DELEGSENAT', 'OFFPAR') THEN 'delegation'
  WHEN t IN ('GOUVERNEMENT', 'MINISTERE', 'PRESREP') THEN 'gouvernement'
  WHEN t IN ('CONSTITU', 'HCJ', 'CJR') THEN 'juridiction'
  WHEN t IN ('API', 'ORGEXTPARL') THEN 'externe'
END AS famille_organe);

-- Chambre imposée par le type d'organe ; NULL = type commun ou hors chambre
-- (ex. CMP, GA : la chambre vient de l'organe ; GP : AN, ou PE plus tard).
CREATE MACRO chambre_du_type(t) AS CAST(CASE
  WHEN t = 'ASSEMBLEE' THEN 'assemblee'
  WHEN t IN ('SENAT', 'COMSENAT', 'COMSPSENAT', 'DELEGSENAT', 'GROUPESENAT') THEN 'senat'
END AS chambre);

-- Libellé de chaque type d'organe.
CREATE MACRO libelle_type_organe(t) AS CASE t
  WHEN 'ASSEMBLEE' THEN 'Assemblée nationale'           WHEN 'SENAT' THEN 'Sénat'
  WHEN 'BUREAU' THEN 'Bureau'                           WHEN 'CONFPT' THEN 'Conférence des présidents'
  WHEN 'GP' THEN 'Groupe politique'                     WHEN 'GROUPESENAT' THEN 'Groupe politique du Sénat'
  WHEN 'PARPOL' THEN 'Parti politique'                  WHEN 'ALLIANCE' THEN 'Alliance politique'
  WHEN 'GA' THEN 'Groupe d''amitié'                     WHEN 'GE' THEN 'Groupe d''études'
  WHEN 'GEVI' THEN 'Groupe d''études à vocation internationale'
  WHEN 'COMPER' THEN 'Commission permanente'            WHEN 'COMSENAT' THEN 'Commission du Sénat'
  WHEN 'CMP' THEN 'Commission mixte paritaire'          WHEN 'CNPE' THEN 'Commission d''enquête'
  WHEN 'CNPS' THEN 'Commission spéciale'                WHEN 'COMSPSENAT' THEN 'Commission spéciale du Sénat'
  WHEN 'COMNL' THEN 'Autre commission'                  WHEN 'MISINFO' THEN 'Mission d''information'
  WHEN 'MISINFOCOM' THEN 'Mission d''information commune'
  WHEN 'MISINFOPRE' THEN 'Mission d''information de la Conférence des présidents'
  WHEN 'DELEG' THEN 'Délégation parlementaire'          WHEN 'DELEGBUREAU' THEN 'Délégation du Bureau'
  WHEN 'DELEGSENAT' THEN 'Délégation du Sénat'          WHEN 'OFFPAR' THEN 'Office parlementaire'
  WHEN 'GOUVERNEMENT' THEN 'Gouvernement'               WHEN 'MINISTERE' THEN 'Ministère'
  WHEN 'PRESREP' THEN 'Présidence de la République'     WHEN 'CONSTITU' THEN 'Conseil constitutionnel'
  WHEN 'HCJ' THEN 'Haute Cour'                          WHEN 'CJR' THEN 'Cour de justice de la République'
  WHEN 'API' THEN 'Assemblée parlementaire internationale'
  WHEN 'ORGEXTPARL' THEN 'Organisme extra-parlementaire'
END;

-- Libellé d'une qualité, accordé à la civilité : 'mme' => féminin,
-- 'm' => masculin, NULL => écriture inclusive (point médian).
-- Requête : libelle_qualite(m.qualite, p.civilite).
CREATE MACRO libelle_qualite(q, civ) AS (
  SELECT CASE civ WHEN 'mme' THEN f WHEN 'm' THEN h ELSE n END
  FROM (VALUES
    ('membre', 'Membre', 'Membre', 'Membre'),
    ('membre_titulaire', 'Membre titulaire', 'Membre titulaire', 'Membre titulaire'),
    ('membre_suppleant', 'Membre suppléant', 'Membre suppléante', 'Membre suppléant·e'),
    ('membre_de_droit', 'Membre de droit', 'Membre de droit', 'Membre de droit'),
    ('membre_bureau', 'Membre du bureau', 'Membre du bureau', 'Membre du bureau'),
    ('president', 'Président', 'Présidente', 'Président·e'),
    ('president_de_droit', 'Président de droit', 'Présidente de droit', 'Président·e de droit'),
    ('president_delegue', 'Président délégué', 'Présidente déléguée', 'Président·e délégué·e'),
    ('president_executif', 'Président exécutif', 'Présidente exécutive', 'Président·e exécutif·ve'),
    ('co_president', 'Coprésident', 'Coprésidente', 'Coprésident·e'),
    ('vice_president', 'Vice-président', 'Vice-présidente', 'Vice-président·e'),
    ('vice_president_delegue', 'Vice-président délégué', 'Vice-présidente déléguée', 'Vice-président·e délégué·e'),
    ('vice_president_honneur', 'Vice-président d''honneur', 'Vice-présidente d''honneur', 'Vice-président·e d''honneur'),
    ('secretaire', 'Secrétaire', 'Secrétaire', 'Secrétaire'),
    ('secretaire_adjoint', 'Secrétaire adjoint', 'Secrétaire adjointe', 'Secrétaire adjoint·e'),
    ('secretaire_general', 'Secrétaire général', 'Secrétaire générale', 'Secrétaire général·e'),
    ('secretaire_general_adjoint', 'Secrétaire général adjoint', 'Secrétaire générale adjointe', 'Secrétaire général·e adjoint·e'),
    ('questeur', 'Questeur', 'Questrice', 'Questeur·rice'),
    ('tresorier', 'Trésorier', 'Trésorière', 'Trésorier·e'),
    ('tresorier_adjoint', 'Trésorier adjoint', 'Trésorière adjointe', 'Trésorier·e adjoint·e'),
    ('rapporteur', 'Rapporteur', 'Rapporteure', 'Rapporteur·e'),
    ('co_rapporteur', 'Corapporteur', 'Corapporteure', 'Corapporteur·e'),
    ('rapporteur_adjoint', 'Rapporteur adjoint', 'Rapporteure adjointe', 'Rapporteur·e adjoint·e'),
    ('rapporteur_general', 'Rapporteur général', 'Rapporteure générale', 'Rapporteur·e général·e'),
    ('rapporteur_special', 'Rapporteur spécial', 'Rapporteure spéciale', 'Rapporteur·e spécial·e'),
    ('rapporteur_pour_avis', 'Rapporteur pour avis', 'Rapporteure pour avis', 'Rapporteur·e pour avis'),
    ('rapporteur_thematique', 'Rapporteur thématique', 'Rapporteure thématique', 'Rapporteur·e thématique'),
    ('porte_parole', 'Porte-parole', 'Porte-parole', 'Porte-parole'),
    ('delegue', 'Délégué', 'Déléguée', 'Délégué·e'),
    ('representant', 'Représentant', 'Représentante', 'Représentant·e'),
    ('representant_suppleant', 'Représentant suppléant', 'Représentante suppléante', 'Représentant·e suppléant·e'),
    ('chef', 'Chef', 'Cheffe', 'Chef·fe'),
    ('president_republique', 'Président de la République', 'Présidente de la République', 'Président·e de la République'),
    ('premier_ministre', 'Premier ministre', 'Première ministre', 'Premier·ère ministre'),
    ('ministre', 'Ministre', 'Ministre', 'Ministre'),
    ('ministre_delegue', 'Ministre délégué', 'Ministre déléguée', 'Ministre délégué·e'),
    ('secretaire_etat', 'Secrétaire d''État', 'Secrétaire d''État', 'Secrétaire d''État'),
    ('en_mission', 'En mission', 'En mission', 'En mission'),
    ('collaborateur', 'Collaborateur', 'Collaboratrice', 'Collaborateur·rice'),
    ('autre', 'Autre fonction', 'Autre fonction', 'Autre fonction')
  ) t(code, h, f, n)
  WHERE code = CAST(q AS VARCHAR));

-- Libellé de chaque procédure.
CREATE MACRO libelle_procedure(p) AS CASE p
  WHEN 'loi_ordinaire' THEN 'Loi ordinaire'
  WHEN 'loi_organique' THEN 'Loi organique'
  WHEN 'loi_constitutionnelle' THEN 'Loi constitutionnelle'
  WHEN 'loi_programmation' THEN 'Loi de programmation'
  WHEN 'loi_finances' THEN 'Loi de finances de l''année'
  WHEN 'loi_finances_rectificative' THEN 'Loi de finances rectificative'
  WHEN 'loi_approbation_comptes' THEN 'Loi d''approbation des comptes (ex-loi de règlement)'
  WHEN 'loi_financement_secu' THEN 'Loi de financement de la sécurité sociale'
  WHEN 'loi_financement_secu_rectificative' THEN 'Loi de financement rectificative de la sécurité sociale'
  WHEN 'ratification_traite' THEN 'Ratification d''un traité ou d''une convention'
  WHEN 'loi_referendum_art11' THEN 'Proposition de loi référendaire (article 11)'
  WHEN 'resolution' THEN 'Résolution'
  WHEN 'resolution_34_1' THEN 'Résolution (article 34-1)'
  WHEN 'resolution_europeenne' THEN 'Résolution européenne'
  WHEN 'resolution_reglement' THEN 'Modification du règlement'
  WHEN 'commission_enquete' THEN 'Commission d''enquête'
  WHEN 'prerogatives_commission_enquete' THEN 'Attribution des prérogatives d''une commission d''enquête'
  WHEN 'mission_information' THEN 'Mission d''information'
  WHEN 'rapport_information' THEN 'Rapport d''information sans mission'
  WHEN 'motion_referendaire' THEN 'Motion référendaire'
  WHEN 'engagement_responsabilite' THEN 'Engagement de la responsabilité du Gouvernement'
  WHEN 'declaration_gouvernement' THEN 'Déclaration du Gouvernement'
  WHEN 'message_president_republique' THEN 'Message du président de la République'
  WHEN 'allocution_president_assemblee' THEN 'Allocution du président de l''Assemblée nationale'
  WHEN 'responsabilite_penale_president' THEN 'Responsabilité pénale du président de la République'
  WHEN 'immunite' THEN 'Immunité parlementaire'
  WHEN 'petition' THEN 'Pétition'
END;

-- Coordonnée au format de son type (CASE exhaustif). Réseaux : identifiant
-- ('@mariedupont', 'mariedupont') ou URL, sans espace.
CREATE MACRO coordonnee_valide(type, v) AS CASE
  WHEN type = 'email' THEN regexp_full_match(v, '[^@\s]+@[^@\s]+\.[^@\s]+')
  WHEN type IN ('telephone', 'telecopie') THEN regexp_full_match(v, '\+?[0-9][0-9 .()-]{5,}')
  WHEN type IN ('site', 'blog', 'page_institutionnelle', 'mediapart', 'huffpost') THEN regexp_full_match(v, 'https?://\S+')
  WHEN type IN ('x', 'facebook', 'instagram', 'linkedin', 'bluesky', 'threads', 'tiktok', 'youtube', 'tumblr')
    THEN regexp_full_match(v, '\S+')
  ELSE false END;

-- URL d'une coordonnée : la valeur si c'est déjà une URL, sinon le modèle
-- du réseau. NULL = pas de modèle connu.
CREATE MACRO url_coordonnee(type, v) AS CASE
  WHEN regexp_matches(v, '^https?://') THEN v
  WHEN type = 'email' THEN 'mailto:' || v
  WHEN type IN ('telephone', 'telecopie') THEN 'tel:' || replace(v, ' ', '')
  WHEN type = 'x' THEN 'https://x.com/' || ltrim(v, '@')
  WHEN type = 'facebook' THEN 'https://www.facebook.com/' || ltrim(v, '@')
  WHEN type = 'instagram' THEN 'https://www.instagram.com/' || ltrim(v, '@')
  WHEN type = 'linkedin' THEN 'https://www.linkedin.com/in/' || ltrim(v, '@')
  WHEN type = 'bluesky' THEN 'https://bsky.app/profile/' || ltrim(v, '@')
  WHEN type = 'threads' THEN 'https://www.threads.net/@' || ltrim(v, '@')
  WHEN type = 'tiktok' THEN 'https://www.tiktok.com/@' || ltrim(v, '@')
  WHEN type = 'youtube' THEN 'https://www.youtube.com/@' || ltrim(v, '@')
END;


-- =====================================================================
-- SOURCES ET TRAÇABILITÉ DES IMPORTS
-- =====================================================================

-- Rôle : sources de données : origine d'un lot d'import, d'un identifiant
-- ou d'une coordonnée de personne. Table plutôt qu'ENUM : chaque source
-- porte sa licence, la mention d'attribution exigée et le format de ses
-- identifiants. Référentiel rempli ici même (la base est recréée à chaque
-- passage) : une nouvelle source = une ligne ci-dessous. Pas de import_id :
-- imports référence cette table.
CREATE TABLE sources (
  code               VARCHAR PRIMARY KEY CHECK (regexp_full_match(code, '[a-z][a-z0-9_]*')),  -- ex. 'assemblee', 'hatvp'
  libelle            VARCHAR NOT NULL CHECK (non_vide(libelle)),       -- ex. 'Assemblée nationale (open data)'
  url                VARCHAR CHECK (est_url(url)),                     -- ex. 'https://data.assemblee-nationale.fr'
  licence            VARCHAR NOT NULL CHECK (non_vide(licence)),       -- ex. 'Licence Ouverte 2.0 (Etalab)'
  attribution        VARCHAR CHECK (non_vide(attribution)),            -- mention à afficher, ex. 'Source : Assemblée nationale'
  format_identifiant VARCHAR CHECK (non_vide(format_identifiant)),     -- expression régulière d'un identifiant de personne, ex. 'PA[0-9]+' ; NULL = la source n'en fournit pas
  created_at         TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  CHECK (updated_at >= created_at)
  -- Identifiant au format de sa source : macro identifiants_hors_format().
);
COMMENT ON TABLE sources IS 'Sources de données : licence, attribution, format des identifiants.';

INSERT INTO sources (code, libelle, url, licence, attribution, format_identifiant) VALUES
  ('assemblee', 'Assemblée nationale (open data)', 'https://data.assemblee-nationale.fr',
   'Licence Ouverte 2.0 (Etalab)', 'Source : Assemblée nationale', 'PA[0-9]+'),
  ('senat', 'Sénat (open data)', 'https://data.senat.fr',
   'Licence Ouverte 2.0 (Etalab)', 'Source : Sénat', '[0-9]+[A-Z]'),
  -- Identifiant : nom de la page nominative, ex. 'loisier-anne-catherine',
  -- 'beaudouin-hubiere-sophie-12855', 'martin-(gironde)-alexandra-26044',
  -- 'echaniz-iñaki-24343' (minuscules accentuées possibles : \p{Ll}).
  ('hatvp', 'Haute Autorité pour la transparence de la vie publique', 'https://www.hatvp.fr/open-data/',
   'Licence Ouverte 2.0 (Etalab)', 'Source : HATVP', '[\p{Ll}0-9()]+(-[\p{Ll}0-9()]+)*'),
  ('wikidata', 'Wikidata', 'https://www.wikidata.org',
   'CC0 1.0', NULL, 'Q[0-9]+');

CREATE SEQUENCE imports_id_seq START 1;

-- Rôle : un lot d'import (un passage du chargeur sur un jeu de données).
-- Chaque ligne du modèle garde dans import_id le dernier lot qui l'a
-- réellement modifiée : on sait d'où vient une valeur et quand elle a changé.
CREATE TABLE imports (
  id                  INTEGER PRIMARY KEY DEFAULT nextval('imports_id_seq'),
  source              VARCHAR NOT NULL REFERENCES sources (code),  -- ex. 'assemblee', 'hatvp'
  jeu_de_donnees      VARCHAR NOT NULL CHECK (non_vide(jeu_de_donnees)),  -- ex. 'amendements', 'scrutins'
  statut              statut_import NOT NULL,       -- valeurs : en_cours | termine | echoue
  debut               TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  fin                 TIMESTAMPTZ,                  -- NULL tant que le lot tourne
  nb_lignes_ecrites   INTEGER CHECK (nb_lignes_ecrites >= 0),  -- lignes insérées ou réellement modifiées, ex. 12408
  version_chargeur    VARCHAR CHECK (non_vide(version_chargeur)),  -- version du code d'import, ex. un hash git
  created_at          TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  -- Impact : un lot terminé ou échoué a une date de fin, postérieure au début.
  CHECK ((statut = 'en_cours') = (fin IS NULL)),
  CHECK (fin >= debut),
  CHECK (updated_at >= created_at)
);
COMMENT ON TABLE imports IS 'Lot d''import : un passage du chargeur sur un jeu de données.';


-- =====================================================================
-- RÉFÉRENTIEL DES PÉRIODES
-- =====================================================================

-- Rôle : unité de numérotation de chaque chambre. Une ligne par législature
-- de l'Assemblée ou par session du Sénat (le Sénat n'a pas de législature).
-- Seuls textes et scrutins portent une période, car leur numéro recommence
-- à chaque période ; ailleurs, la période se déduit par jointure.
CREATE TABLE periodes_legislatives (
  id         SMALLINT PRIMARY KEY,
  chambre    chambre NOT NULL,           -- valeurs : assemblee | senat | parlement_europeen
  type       type_periode NOT NULL,      -- valeurs : legislature | session_senat | legislature_europeenne
  numero     SMALLINT NOT NULL,          -- ex. 17 (AN) ; 2025 pour la session 2025-2026 (Sénat) ; 10 (PE)
  libelle    VARCHAR NOT NULL CHECK (non_vide(libelle)),  -- ex. 'XVIIe législature', 'Session 2025-2026'
  date_debut DATE NOT NULL,
  date_fin   DATE,                       -- NULL = période en cours
  created_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id  INTEGER REFERENCES imports (id),  -- NULL = saisie manuelle
  -- Impact : chaque chambre a son type de période (l'Assemblée des
  -- législatures, le Sénat des sessions, le PE des législatures européennes) ;
  -- numéro plausible (Ve République ; années de session ; PE depuis 1979).
  CHECK (CASE chambre
           WHEN 'assemblee'          THEN type = 'legislature' AND numero BETWEEN 1 AND 99
           WHEN 'senat'              THEN type = 'session_senat' AND numero BETWEEN 1958 AND 2200
           WHEN 'parlement_europeen' THEN type = 'legislature_europeenne' AND numero BETWEEN 1 AND 99
           ELSE false END),
  CHECK (date_fin >= date_debut),
  CHECK (updated_at >= created_at),
  UNIQUE (chambre, numero),
  -- Cible des clés composites (periode_legislative_id, chambre) : garantit
  -- qu'un texte ou un scrutin porte une période de sa propre chambre.
  UNIQUE (id, chambre)
  -- Pas deux périodes d'une même chambre qui se chevauchent : macro
  -- periodes_qui_se_chevauchent().
);
COMMENT ON TABLE periodes_legislatives IS 'Législature (AN) ou session (Sénat) : unité de numérotation des textes et scrutins.';


-- =====================================================================
-- ORGANES
-- =====================================================================

-- Rôle : tout organe, quel que soit son type (groupes, commissions, CMP,
-- groupes d'amitié, partis, alliances, Gouvernement...). Une seule table
-- cible pour les mandats, les réunions et les auteurs d'amendements.
-- Un même groupe a un organe par chambre et par législature (AN : nouveau
-- PO à chaque législature) ; ils sont reliés par organe_liens.
CREATE TABLE organes (
  id                  INTEGER PRIMARY KEY,
  uid                 VARCHAR NOT NULL UNIQUE CHECK (non_vide(uid)),  -- ex. 'PO845401', 'SENAT-COMEUR-AFEU'
  type                type_organe NOT NULL,        -- valeurs : voir le type type_organe, ex. 'GP', 'COMPER', 'COMSENAT'
  chambre             chambre,                     -- valeurs : assemblee | senat | parlement_europeen ; NULL pour le Gouvernement ou un organe extérieur
  parent_id           INTEGER REFERENCES organes (id),  -- ex. une sous-commission vers sa commission
  nom                 VARCHAR NOT NULL CHECK (non_vide(nom)),  -- ex. 'Commission des finances, de l''économie générale et du contrôle budgétaire'
  nom_court           VARCHAR CHECK (non_vide(nom_court)),     -- ex. 'Commission des finances'
  nom_precedent       VARCHAR CHECK (non_vide(nom_precedent)), -- nom avant le dernier changement de nom
  nom_court_precedent VARCHAR CHECK (non_vide(nom_court_precedent)),
  date_debut          DATE,
  date_fin            DATE,                        -- NULL = organe actif
  created_at          TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id           INTEGER REFERENCES imports (id),
  source_hash         VARCHAR CHECK (est_md5(source_hash)),  -- empreinte du document source : ligne inchangée = pas de réécriture
  CHECK (parent_id <> id),
  -- Impact : un type propre à une chambre (SENAT, COMSENAT, GROUPESENAT,
  -- ASSEMBLEE...) porte cette chambre.
  CHECK (chambre_du_type(type) IS NULL OR chambre IS NOT DISTINCT FROM chambre_du_type(type)),
  CHECK (date_fin >= date_debut),
  CHECK (updated_at >= created_at),
  -- Cible de la clé composite des sous-types et des mandats : garantit le type de l'organe.
  UNIQUE (id, type)
);
COMMENT ON TABLE organes IS 'Tout organe : groupe, parti, alliance, commission, CMP, délégation, Gouvernement...';

-- Rôle : liens datés entre organes : appartenance d'un groupe à une alliance,
-- succession d'un groupe d'une législature à l'autre, affiliation d'un
-- groupe à un parti ou à un groupe du Parlement européen. Les personnes ne
-- sont pas membres des alliances : leur appartenance se déduit de leur
-- mandat de groupe.
CREATE TABLE organe_liens (
  organe_id       INTEGER NOT NULL REFERENCES organes (id),  -- ex. le groupe LFI-NUPES
  organe_cible_id INTEGER NOT NULL REFERENCES organes (id),  -- ex. l'alliance NUPES
  type            type_lien_organe NOT NULL,        -- valeurs : membre_de | succede_a | affilie_a
  date_debut      DATE NOT NULL,
  date_fin        DATE,                             -- NULL = lien en cours
  created_at      TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id       INTEGER REFERENCES imports (id),  -- NULL = saisie manuelle
  CHECK (organe_cible_id <> organe_id),
  CHECK (date_fin >= date_debut),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (organe_id, organe_cible_id, type, date_debut)
  -- Cible d'un lien membre_de de type ALLIANCE ou PARPOL : macro liens_cible_incoherente().
);
COMMENT ON TABLE organe_liens IS 'Liens datés entre organes : alliance, succession, affiliation.';

-- Rôle : sous-type des organes de type 'GP' (groupe de l'AN, ou du PE plus
-- tard) ou 'GROUPESENAT' (groupe du Sénat), avec les colonnes propres aux
-- groupes. Toute colonne qui doit désigner un groupe politique référence
-- cette table, jamais organes directement.
CREATE TABLE groupes_politiques (
  organe_id          INTEGER PRIMARY KEY,
  type               type_organe NOT NULL CHECK (type IN ('GP', 'GROUPESENAT')),  -- valeurs : GP | GROUPESENAT
  couleur            VARCHAR CHECK (regexp_full_match(couleur, '#[0-9A-Fa-f]{6}')),  -- ex. '#77AA79'
  logo_url           VARCHAR CHECK (est_url(logo_url)),
  position_politique VARCHAR CHECK (position_politique IN ('extreme_gauche', 'gauche', 'centre_gauche', 'centre',
                                                           'centre_droit', 'droite', 'extreme_droite')),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id          INTEGER REFERENCES imports (id),
  CHECK (updated_at >= created_at),
  -- Impact : impossible de déclarer comme groupe un organe d'un autre type.
  FOREIGN KEY (organe_id, type) REFERENCES organes (id, type)
);
COMMENT ON TABLE groupes_politiques IS 'Sous-type des organes de type GP ou GROUPESENAT.';


-- =====================================================================
-- PERSONNES
-- =====================================================================

-- Rôle : identité d'une personne. Une même personne peut être députée,
-- puis sénatrice, puis ministre : les fonctions vivent dans mandats.
CREATE TABLE personnes (
  id             INTEGER PRIMARY KEY,
  slug           VARCHAR NOT NULL UNIQUE CHECK (regexp_full_match(slug, '[a-z0-9]+(-[a-z0-9]+)*')),  -- ex. 'marie-dupont'
  nom                  VARCHAR NOT NULL CHECK (non_vide(nom)),     -- nom d'usage, ex. 'Dupont'
  nom_naissance        VARCHAR CHECK (non_vide(nom_naissance)),    -- si différent du nom d'usage, ex. 'Martin' (rapprochement HATVP, Wikidata)
  prenom               VARCHAR NOT NULL CHECK (non_vide(prenom)),  -- ex. 'Marie'
  civilite             civilite,                   -- valeurs : m | mme ; telle que publiée par la source
  genre                genre,                      -- valeurs : femme | homme | non_binaire ; déclaré par la personne, jamais déduit
  date_naissance       DATE CHECK (date_naissance >= DATE '1850-01-01'),
  lieu_naissance       VARCHAR CHECK (non_vide(lieu_naissance)),   -- ex. 'Lyon (Rhône)'
  code_insee_naissance VARCHAR CHECK (regexp_full_match(code_insee_naissance, '[0-9][0-9AB][0-9]{3}')),  -- commune de naissance, ex. '69123', '2A004'
  date_deces           DATE,
  profession           VARCHAR CHECK (non_vide(profession)),       -- ex. 'Avocate' ; l'historique est dans personne_activites
  photo_url            VARCHAR CHECK (est_url(photo_url)),
  created_at           TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id            INTEGER REFERENCES imports (id),
  source_hash          VARCHAR CHECK (est_md5(source_hash)),
  CHECK (nom_naissance <> nom),
  CHECK (date_deces >= date_naissance),
  CHECK (updated_at >= created_at)
);
COMMENT ON TABLE personnes IS 'Identité d''une personne ; ses fonctions sont dans mandats.';

-- Rôle : formations d'une personne (diplômes, établissements). Plusieurs
-- lignes par personne ; l'établissement le plus récent est celui de la
-- formation à la plus grande annee_fin.
CREATE TABLE personne_formations (
  personne_id   INTEGER NOT NULL REFERENCES personnes (id),
  rang          SMALLINT NOT NULL CHECK (rang >= 1),  -- ordre des formations de la personne, 1 = la plus ancienne
  etablissement VARCHAR CHECK (non_vide(etablissement)),  -- ex. 'Sciences Po Paris', 'Université de Lyon'
  diplome       VARCHAR CHECK (non_vide(diplome)),        -- ex. 'Master de droit public'
  niveau        niveau_formation,                   -- valeurs : sans_diplome | secondaire | bac | bac_2 | licence | master | doctorat | grande_ecole
  annee_debut   SMALLINT CHECK (annee_debut BETWEEN 1850 AND 2200),
  annee_fin     SMALLINT CHECK (annee_fin BETWEEN 1850 AND 2200),  -- année d'obtention ou de sortie
  source        VARCHAR REFERENCES sources (code),  -- ex. 'hatvp', 'wikidata'
  created_at    TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id     INTEGER REFERENCES imports (id),
  -- Impact : une formation dit au moins où, quoi ou à quel niveau.
  CHECK (etablissement IS NOT NULL OR diplome IS NOT NULL OR niveau IS NOT NULL),
  CHECK (annee_fin >= annee_debut),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (personne_id, rang)
);
COMMENT ON TABLE personne_formations IS 'Formations d''une personne : établissement, diplôme, niveau.';

-- Rôle : activités professionnelles d'une personne (avant, pendant ou après
-- ses mandats). Avant / après se déduit des dates, comparées à mandats.
-- Les employeurs ne sont pas des organes : SIREN pour les rapprocher plus
-- tard du répertoire des représentants d'intérêts (HATVP).
CREATE TABLE personne_activites (
  personne_id     INTEGER NOT NULL REFERENCES personnes (id),
  rang            SMALLINT NOT NULL CHECK (rang >= 1),  -- ordre des activités de la personne
  employeur       VARCHAR CHECK (non_vide(employeur)),  -- ex. 'Cabinet Dupont & associés'
  employeur_siren VARCHAR CHECK (regexp_full_match(employeur_siren, '[0-9]{9}')),
  poste           VARCHAR CHECK (non_vide(poste)),      -- ex. 'Avocate associée'
  date_debut      DATE,
  date_fin        DATE,                             -- NULL = en cours ou inconnue
  source          VARCHAR REFERENCES sources (code),  -- ex. 'hatvp'
  created_at      TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id       INTEGER REFERENCES imports (id),
  CHECK (employeur IS NOT NULL OR poste IS NOT NULL),
  CHECK (date_fin >= date_debut),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (personne_id, rang)
);
COMMENT ON TABLE personne_activites IS 'Activités professionnelles d''une personne, datées.';

-- Rôle : identifiants de la personne dans chaque source.
CREATE TABLE personne_identifiants (
  personne_id INTEGER NOT NULL REFERENCES personnes (id),
  source      VARCHAR NOT NULL REFERENCES sources (code),  -- ex. 'assemblee', 'senat', 'hatvp', 'wikidata'
  valeur      VARCHAR NOT NULL CHECK (non_vide(valeur)),  -- ex. 'PA793246' (AN), '11069T' (Sénat), 'loisier-anne-catherine' (HATVP), 'Q3292150' (Wikidata)
  created_at  TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id   INTEGER REFERENCES imports (id),
  CHECK (updated_at >= created_at),
  -- Impact : un identifiant source désigne une seule personne.
  PRIMARY KEY (source, valeur)
  -- Format de l'identifiant = sources.format_identifiant (un CHECK ne lit
  -- pas une autre table) : macro identifiants_hors_format().
);
COMMENT ON TABLE personne_identifiants IS 'Identifiants d''une personne dans chaque source (AN, Sénat, HATVP, Wikidata).';

-- Rôle : coordonnées publiques d'une personne (courriel, téléphone, site,
-- réseaux), avec leur période de validité. Un nouveau réseau = une valeur
-- de type_coordonnee et une règle dans coordonnee_valide().
CREATE TABLE personne_coordonnees (
  personne_id INTEGER NOT NULL REFERENCES personnes (id),
  type        type_coordonnee NOT NULL,             -- valeurs : voir le type type_coordonnee, ex. 'email', 'x', 'bluesky'
  valeur      VARCHAR NOT NULL CHECK (non_vide(valeur)),  -- ex. 'marie.dupont@assemblee-nationale.fr', '@mariedupont'
  source      VARCHAR REFERENCES sources (code),    -- ex. 'assemblee'
  date_debut  DATE,
  date_fin    DATE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id   INTEGER REFERENCES imports (id),
  -- Impact : chaque valeur a la forme de son type (courriel, téléphone, URL...) ;
  -- un type sans règle dans coordonnee_valide() est refusé.
  CHECK (coordonnee_valide(type, valeur)),
  CHECK (date_fin >= date_debut),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (personne_id, type, valeur)
);
COMMENT ON TABLE personne_coordonnees IS 'Coordonnées publiques d''une personne, avec période de validité.';

-- Rôle : circonscriptions électorales, rattachées aux mandats parlementaires.
CREATE TABLE circonscriptions (
  id          INTEGER PRIMARY KEY,
  code        VARCHAR NOT NULL UNIQUE CHECK (non_vide(code)),  -- ex. '75-01' (législative), '21' (sénatoriale)
  departement VARCHAR NOT NULL CHECK (non_vide(departement)),  -- ex. '75', '2A', '971'
  numero      SMALLINT CHECK (numero >= 0),         -- ex. 1 ; 0 pour une circonscription sénatoriale (le département)
  libelle     VARCHAR NOT NULL CHECK (non_vide(libelle)),      -- ex. '1re circonscription de Paris'
  created_at  TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id   INTEGER REFERENCES imports (id),
  CHECK (updated_at >= created_at)
);
COMMENT ON TABLE circonscriptions IS 'Circonscriptions électorales (législatives et sénatoriales).';

-- Rôle : appartenance d'une personne à un organe sur une période, avec une
-- qualité. Remplace mandats, mandats_parlementaires et les colonnes
-- « situation actuelle » de parlementaires (groupe, circonscription, actif).
-- Une personne peut cumuler (ministre, membre d'un groupe dont le groupe est
-- dans une alliance) ; deux mandats dans le même organe (membre et
-- vice-président), ou deux groupes politiques en même temps, sont signalés
-- par des contrôles d'information, pas refusés.
-- Une qualité double de la source (« Président et rapporteur ») donne la
-- qualité principale et le reste dans qualite_precision : deux mandats
-- dans le même organe sur la même période seraient refusés.
CREATE TABLE mandats (
  id                 INTEGER PRIMARY KEY,
  uid                VARCHAR UNIQUE CHECK (non_vide(uid)),  -- identifiant du mandat dans la source, ex. 'PM843173'
  personne_id        INTEGER NOT NULL REFERENCES personnes (id),
  organe_id          INTEGER NOT NULL,
  organe_type        type_organe NOT NULL,          -- copie de organes.type, ex. 'GP', 'COMPER' (contrôle de circonscription_id, filtres sans jointure)
  qualite            qualite_mandat NOT NULL,       -- valeurs : voir le type qualite_mandat, ex. 'membre', 'vice_president' ; libellé : libelle_qualite()
  rang               SMALLINT CHECK (rang >= 1),    -- ex. 1 pour « Premier vice-président »
  qualite_precision  VARCHAR CHECK (non_vide(qualite_precision)),  -- libellé source quand il dit plus que qualite, ex. 'Rapporteur spécial au nom de la commission des finances : Sécurité'
  circonscription_id INTEGER REFERENCES circonscriptions (id),
  date_debut         DATE NOT NULL,
  date_fin           DATE,                          -- NULL = mandat en cours
  created_at         TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id          INTEGER REFERENCES imports (id),
  source_hash        VARCHAR CHECK (est_md5(source_hash)),
  -- Impact : seul un mandat parlementaire porte une circonscription.
  CHECK (circonscription_id IS NULL OR organe_type IN ('ASSEMBLEE', 'SENAT')),
  CHECK (date_fin >= date_debut),
  CHECK (updated_at >= created_at),
  -- Impact : organe_type ne peut pas diverger du type réel de l'organe.
  FOREIGN KEY (organe_id, organe_type) REFERENCES organes (id, type)
  -- Chevauchements signalés (non bloquants) : macros mandats_qui_se_chevauchent(),
  -- groupes_qui_se_chevauchent() ; répartition : chevauchements_par_type().
);
COMMENT ON TABLE mandats IS 'Appartenance d''une personne à un organe sur une période, avec une qualité.';


-- =====================================================================
-- TRAVAIL LÉGISLATIF : DOSSIERS, TEXTES, ARTICLES
-- =====================================================================

-- Rôle : un dossier législatif, qui regroupe tous les textes d'une navette.
CREATE TABLE dossiers (
  id                         INTEGER PRIMARY KEY,
  uid                        VARCHAR NOT NULL UNIQUE CHECK (regexp_full_match(uid, 'DLR5L[0-9]+N[0-9]+|SENAT-\S+')),  -- ex. 'DLR5L17N52725', 'SENAT-ppl24-123'
  procedure                  procedure_parlementaire,  -- valeurs : voir le type procedure_parlementaire, ex. 'loi_ordinaire' ; NULL = code source inconnu
  titre                      VARCHAR NOT NULL CHECK (non_vide(titre)),  -- ex. 'Projet de loi de finances pour 2026'
  titre_court                VARCHAR CHECK (non_vide(titre_court)),     -- ex. 'PLF 2026'
  statut                     statut_dossier NOT NULL,  -- valeurs : en_cours | clos
  denouement                 denouement_dossier,    -- valeurs : promulgue | adopte | rejete | caduc | fusionne | retire ; NULL tant que statut = 'en_cours'
  date_depot                 DATE,
  date_denouement            DATE,
  loi_numero                 VARCHAR CHECK (regexp_full_match(loi_numero, '[0-9]{2,4}-[0-9]+')),  -- ex. '2008-1076'
  loi_titre                  VARCHAR CHECK (non_vide(loi_titre)),
  loi_date_jo                DATE,
  url_legifrance             VARCHAR CHECK (est_url(url_legifrance)),
  created_at                 TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at                 TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id                  INTEGER REFERENCES imports (id),
  source_hash                VARCHAR CHECK (est_md5(source_hash)),
  -- Impact : un dossier clos a toujours un dénouement ; un dossier en cours n'en a pas.
  CHECK ((statut = 'clos') = (denouement IS NOT NULL)),
  -- Impact : seule une loi promulguée a un numéro, un titre de loi, une date au JO, un lien Légifrance.
  CHECK (denouement = 'promulgue'
         OR (loi_numero IS NULL AND loi_titre IS NULL AND loi_date_jo IS NULL AND url_legifrance IS NULL)),
  CHECK (date_denouement >= date_depot),
  CHECK (loi_date_jo >= date_depot),
  CHECK (updated_at >= created_at)
);
COMMENT ON TABLE dossiers IS 'Dossier législatif : regroupe les textes d''une navette.';

-- Rôle : un document de la navette (projet, proposition, texte de commission,
-- texte adopté). Existe sans articles : 1 064 des textes visés par des
-- amendements n'ont pas d'articles dans les données actuelles.
CREATE TABLE textes (
  id                     INTEGER PRIMARY KEY,
  uid                    VARCHAR NOT NULL UNIQUE,   -- ex. 'PRJLANR5L17B3058', 'SENAT-TXT-107168'
  dossier_id             INTEGER NOT NULL REFERENCES dossiers (id),
  periode_legislative_id SMALLINT NOT NULL,
  chambre                chambre NOT NULL,          -- valeurs : assemblee | senat
  nature                 nature_texte NOT NULL,     -- valeurs : projet | proposition | texte_commission | texte_adopte
  numero                 SMALLINT CHECK (numero > 0),  -- numéro officiel sans « n° », ex. 3058 ; NULL tant qu'inconnu (Sénat)
  ordre_dossier          SMALLINT NOT NULL CHECK (ordre_dossier >= 1),  -- rang dans le dossier : 1 = premier texte, puis chaque étape
  titre                  VARCHAR CHECK (non_vide(titre)),
  texte_source_id        INTEGER,                   -- ex. BTC3058 vers B3058
  date_depot             DATE,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id              INTEGER REFERENCES imports (id),
  source_hash            VARCHAR CHECK (est_md5(source_hash)),
  -- Impact : uid au format de sa chambre ; pour l'AN, nature et numéro sont
  -- ceux que porte l'uid (B = dépôt, BTC = commission, BTA = adopté).
  -- Chambre sans règle (PE) : refusée.
  CHECK (CASE chambre
           WHEN 'senat' THEN regexp_full_match(uid, 'SENAT-TXT-[0-9]+')
           WHEN 'assemblee' THEN regexp_full_match(uid, '[A-Z]{4}ANR5L[0-9]+B(TC|TA)?[0-9]+')
                AND numero = CAST(regexp_extract(uid, '[0-9]+$') AS INTEGER)
                AND nature = CASE WHEN contains(uid, 'BTC') THEN 'texte_commission'
                                  WHEN contains(uid, 'BTA') THEN 'texte_adopte'
                                  WHEN starts_with(uid, 'PRJL') THEN 'projet'
                                  ELSE 'proposition' END
           ELSE false
         END),
  CHECK (texte_source_id <> id),
  -- Impact : un texte de commission ou adopté dérive d'un texte, pas un dépôt.
  CHECK (texte_source_id IS NULL OR nature IN ('texte_commission', 'texte_adopte')),
  CHECK (updated_at >= created_at),
  -- Impact : la période appartient à la chambre du texte.
  FOREIGN KEY (periode_legislative_id, chambre) REFERENCES periodes_legislatives (id, chambre),
  -- Impact : le texte source appartient au même dossier.
  FOREIGN KEY (texte_source_id, dossier_id) REFERENCES textes (id, dossier_id),
  -- Impact : un numéro par période et par nature (B3058 et BTC3058 partagent 3058).
  UNIQUE (periode_legislative_id, nature, numero),
  UNIQUE (dossier_id, ordre_dossier),
  -- Cible des clés de contexte (texte_id, dossier_id) des amendements, scrutins et du texte source.
  UNIQUE (id, dossier_id)
);
COMMENT ON TABLE textes IS 'Document de la navette : projet, proposition, texte de commission, texte adopté.';

-- Rôle : emplacements d'un texte, ceux qu'un amendement peut viser :
-- l'intitulé, les articles réels (avec leur contenu), et les emplacements
-- entre deux articles (« APRÈS ART. 2 » et « AVANT ART. 3 » désignent la
-- même ligne). Les emplacements (est_emplacement) sont créés à l'import, à
-- la demande, quand un amendement les vise.
-- Règle de ordre_place, appliquée par l'import :
--   0 = titre ; 5 = avant le premier article ; 10k = article de rang k ;
--   10k + 5 = emplacement après l'article k (ordre_ref = k). Plafond :
--   3 276 articles (SMALLINT) ; le texte le plus long de clair en compte 328.
CREATE TABLE articles (
  id                  INTEGER PRIMARY KEY,
  texte_id            INTEGER NOT NULL REFERENCES textes (id),
  ordre               SMALLINT CHECK (ordre >= 1),  -- rang parmi les articles réels (1, 2...) ; NULL pour un emplacement
  ordre_ref           SMALLINT CHECK (ordre_ref >= 1),  -- emplacement après l'article de rang k : k ; NULL sinon
  ordre_place         SMALLINT NOT NULL CHECK (ordre_place >= 0),  -- rang dans le document, voir la règle ci-dessus
  est_emplacement     BOOLEAN NOT NULL,             -- emplacement (titre ou intervalle, pas un article réel) ; = numero IS NULL
  est_supprime        BOOLEAN NOT NULL DEFAULT false,  -- article réel marqué « (Supprimé) » : garde son numéro, sans contenu propre
  -- Forme normalisée (majuscules, sans espace en bord), celle des libellés
  -- visés par les amendements ; groupes et annexes existent ('ARTICLES 3 ET 4', 'RAPPORT ANNEXÉ').
  numero              VARCHAR CHECK (non_vide(numero) AND numero = upper(trim(numero))),  -- ex. 'PREMIER', '3 BIS', '20 A', 'LIMINAIRE' ; NULL = emplacement
  libelle             VARCHAR NOT NULL CHECK (non_vide(libelle)),  -- ex. 'Article 3 bis (nouveau)', 'Après l''article 2', 'Titre'
  contenu             VARCHAR CHECK (non_vide(contenu)),  -- articles réels : ex. 'I. – L''article 224 du code général des impôts...'
  created_at          TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id           INTEGER REFERENCES imports (id),
  CHECK (est_emplacement = (numero IS NULL)),
  -- Impact : un article réel a un rang et pas de référence ; un emplacement n'a
  -- ni rang, ni mention « supprimé », ni contenu.
  CHECK (CASE WHEN numero IS NOT NULL THEN ordre IS NOT NULL AND ordre_ref IS NULL
              ELSE ordre IS NULL AND NOT est_supprime AND contenu IS NULL END),
  -- Impact : la règle de ordre_place est vérifiée : 10k pour un article réel,
  -- 10k + 5 après l'article k, 0 (titre) ou 5 (avant le premier article) sinon.
  CHECK (CASE WHEN numero IS NOT NULL    THEN ordre_place = 10 * ordre
              WHEN ordre_ref IS NOT NULL THEN ordre_place = 10 * ordre_ref + 5
              ELSE ordre_place IN (0, 5) END),
  CHECK (updated_at >= created_at),
  -- Impact : l'emplacement suit un article réel du même texte (un
  -- emplacement a ordre NULL : il ne peut pas être visé ; ordre_ref NULL :
  -- pas de contrôle).
  FOREIGN KEY (texte_id, ordre_ref) REFERENCES articles (texte_id, ordre),
  UNIQUE (texte_id, numero),
  UNIQUE (texte_id, ordre),
  -- Impact : un seul titre, un seul « avant le premier article », un seul
  -- emplacement après chaque article.
  UNIQUE (texte_id, ordre_place),
  UNIQUE (id, texte_id)                             -- cible de (article_id, texte_id) des amendements, scrutins, interventions
);
COMMENT ON TABLE articles IS 'Emplacements d''un texte : titre, articles réels avec contenu, intervalles entre articles.';

-- Rôle : filiation d'un article d'un texte à l'autre de la navette
-- (B3058 -> BTC3058 -> BTA0749 -> texte transmis au Sénat). La source peut
-- être un emplacement : l'article 2 bis (nouveau) du texte de commission
-- vient de l'emplacement « après l'article 2 » du texte déposé. Plusieurs
-- sources (fusion) ou plusieurs descendants (scission) sont possibles.
-- Table séparée plutôt qu'une colonne de articles : remplie après tous les
-- articles, sans ordre d'insertion à respecter ni UPDATE (refusé par DuckDB
-- sur une ligne référencée).
CREATE TABLE article_filiations (
  article_id        INTEGER NOT NULL REFERENCES articles (id),  -- l'article du texte suivant
  article_source_id INTEGER NOT NULL REFERENCES articles (id),  -- article ou emplacement du texte précédent
  created_at        TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id         INTEGER REFERENCES imports (id),
  CHECK (article_source_id <> article_id),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (article_id, article_source_id)
  -- Source dans le même dossier, dans un texte antérieur : macro filiations_hors_navette().
);
COMMENT ON TABLE article_filiations IS 'Filiation d''un article d''un texte à l''autre de la navette.';


-- =====================================================================
-- AMENDEMENTS
-- =====================================================================

-- La correspondance des libellés sources de clair (« Rejeté », « rejete »,
-- « R », « Cavalier (45) »...) vers statut, catégorie et motif sert seulement
-- au chargement (couche d'import), hors modèle. Contenu : ../DENOUEMENTS.md.

-- Rôle : un amendement : métadonnées, texte (dispositif, exposé) et groupes
-- de discussion. Les cosignataires et la réunion de discussion sont dans
-- leurs propres tables.
-- Groupes de discussion, tels que l'AN les forme :
--   - discussion identique : amendements au dispositif identique ;
--   - discussion commune : amendements qui portent sur le même sujet.
CREATE TABLE amendements (
  id                      INTEGER PRIMARY KEY,
  uid                     VARCHAR NOT NULL UNIQUE,   -- ex. 'AMANR5L17PO419610B3058P0D1N000083', 'SENAT-AMD-1316454'
  texte_id                INTEGER NOT NULL,
  dossier_id              INTEGER NOT NULL,          -- contexte : copie de textes.dossier_id
  article_id              INTEGER,                   -- emplacement visé (article réel, intervalle ou titre)
  parent_id               INTEGER,                   -- sous-amendement : l'amendement visé
  organe_examen_id        INTEGER REFERENCES organes (id),  -- organe saisi (commission ou séance), PO de l'uid AN ; NULL au Sénat
  deliberation            SMALLINT CHECK (deliberation >= 1),  -- 1 = délibération normale, 2 = seconde délibération (D de l'uid AN)
  auteur_id               INTEGER REFERENCES personnes (id),  -- auteur parlementaire
  auteur_organe_id        INTEGER REFERENCES organes (id),    -- auteur institutionnel : Gouvernement, commission
  groupe_id               INTEGER REFERENCES groupes_politiques (organe_id),  -- groupe de l'auteur au dépôt (instantané)
  numero                  VARCHAR NOT NULL CHECK (non_vide(numero)),  -- numéro affiché, ex. 'CE83', 'I-164', '374', '21 (Rect)'
  numero_ordre            INTEGER CHECK (numero_ordre > 0),  -- ex. 83
  article_vise            VARCHAR CHECK (non_vide(article_vise)),  -- libellé brut, ex. 'APRÈS ART. 2' ; conservé si article_id non résolu
  alinea_numero           SMALLINT CHECK (alinea_numero >= 0),  -- alinéa visé dans l'article, ex. 4 (source AN)
  statut                  statut_amendement NOT NULL,  -- valeurs : en_recevabilite | a_discuter | en_traitement | traite
  denouement              categorie_denouement,      -- valeurs : adopte | rejete | retire | tombe | non_soutenu | irrecevable | autre ; NULL tant que statut <> 'traite'
  motif_denouement        motif_denouement,          -- valeurs : voir le type motif_denouement, ex. 'cavalier_45' ; NULL = pas de détail
  date_depot              DATE,
  date_denouement         TIMESTAMPTZ,
  est_racine              BOOLEAN NOT NULL,          -- = parent_id IS NULL (cible de la clé parent)
  parent_doit_etre_racine BOOLEAN,                   -- true si parent_id est renseigné, NULL sinon
  dispositif              VARCHAR,                   -- ex. 'Supprimer cet article.'
  expose_sommaire         VARCHAR,                   -- ex. 'Cet amendement vise à...'
  discussion_commune_id   INTEGER CHECK (discussion_commune_id > 0),    -- groupe de discussion commune dans la source, ex. 37569
  discussion_identique_id INTEGER CHECK (discussion_identique_id > 0),  -- groupe d'amendements identiques, ex. 59933
  position_commune        position_discussion,       -- valeurs : premier | milieu | dernier
  position_identique      position_discussion,       -- valeurs : premier | milieu | dernier
  created_at              TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id               INTEGER REFERENCES imports (id),
  source_hash             VARCHAR CHECK (est_md5(source_hash)),
  -- Impact : uid au format de sa source ; pour l'AN, la délibération est celle de l'uid.
  CHECK (CASE WHEN starts_with(uid, 'SENAT-') THEN regexp_full_match(uid, 'SENAT-AMD-\S+') AND deliberation IS NULL
              ELSE regexp_full_match(uid, 'AMANR5L[0-9]+PO[0-9]+B(TC|TA)?[0-9]+P[0-9]+D[0-9]+N[0-9]+')
                   AND deliberation = CAST(regexp_extract(uid, 'D([0-9]+)N', 1) AS INTEGER) END),
  -- Impact : les colonnes de cible de clé suivent leur définition (ex-colonnes générées).
  CHECK (est_racine = (parent_id IS NULL)),
  CHECK (parent_doit_etre_racine IS NOT DISTINCT FROM CASE WHEN parent_id IS NOT NULL THEN true END),
  CHECK (parent_id <> id),
  -- Impact : un seul auteur, parlementaire ou institutionnel.
  CHECK (auteur_id IS NULL OR auteur_organe_id IS NULL),
  -- Impact : un amendement traité a toujours un dénouement, et inversement.
  CHECK ((statut = 'traite') = (denouement IS NOT NULL)),
  -- Impact : le motif appartient à la catégorie du dénouement (ex. 'cavalier_45' => 'irrecevable').
  CHECK (motif_denouement IS NULL OR denouement IS NOT DISTINCT FROM categorie_du_motif(motif_denouement)),
  -- Impact : un groupe de discussion a toujours une position, et inversement.
  CHECK ((discussion_commune_id IS NULL) = (position_commune IS NULL)),
  CHECK ((discussion_identique_id IS NULL) = (position_identique IS NULL)),
  CHECK (updated_at >= created_at),
  -- Impact : dossier_id suit le texte.
  FOREIGN KEY (texte_id, dossier_id) REFERENCES textes (id, dossier_id),
  -- Impact : l'emplacement visé appartient au même texte.
  FOREIGN KEY (article_id, texte_id) REFERENCES articles (id, texte_id),
  -- Impact : le parent est un amendement racine du même texte (pas de sous-sous-amendement).
  FOREIGN KEY (parent_id, texte_id, parent_doit_etre_racine) REFERENCES amendements (id, texte_id, est_racine),
  UNIQUE (id, texte_id, est_racine),                -- cible de la clé parent
  UNIQUE (id, dossier_id),                          -- cible des clés de contexte des tables filles
  -- Impact : un numéro par texte, organe d'examen et délibération (AN).
  -- Au Sénat, organe et délibération sont NULL : pas de contrôle (NULL non comparés).
  UNIQUE (texte_id, organe_examen_id, deliberation, numero)
  -- Organe de l'uid AN = organe_examen_id : macro amendements_organe_incoherent().
);
COMMENT ON TABLE amendements IS 'Amendement : métadonnées, dispositif, exposé sommaire, groupes de discussion.';
-- uid_canonique de clair = replace(uid, 'BTC', 'B') pour 100 % des lignes :
-- index sur l'expression plutôt qu'une colonne stockée.
-- Requête : WHERE replace(uid, 'BTC', 'B') = 'AMANR5L15PO717460B0857P0D1N000374'.
CREATE UNIQUE INDEX amendements_uid_canonique ON amendements ((replace(uid, 'BTC', 'B')));

-- Rôle : cosignataires d'un amendement (l'auteur est dans amendements.auteur_id).
CREATE TABLE amendement_cosignataires (
  amendement_id INTEGER NOT NULL,
  personne_id   INTEGER NOT NULL REFERENCES personnes (id),
  dossier_id    INTEGER NOT NULL,                   -- contexte : copie de amendements.dossier_id
  rang          SMALLINT CHECK (rang >= 1),         -- ordre de signature dans la source, ex. 1, 2, 3
  created_at    TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id     INTEGER REFERENCES imports (id),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (amendement_id, personne_id),
  -- Impact : dossier_id suit l'amendement.
  FOREIGN KEY (amendement_id, dossier_id) REFERENCES amendements (id, dossier_id)
);
COMMENT ON TABLE amendement_cosignataires IS 'Cosignataires d''un amendement (hors auteur).';


-- #####################################################################
-- #####################################################################
-- PARTIE À VALIDER
-- Tables pas encore discutées : réunions, scrutins, votes, interventions.
-- Leur structure peut changer ; elles sont regroupées ici pour être
-- validées ensemble. amendement_discussions est ici car elle référence
-- reunions (DuckDB n'ajoute pas de clé étrangère après coup).
-- #####################################################################
-- #####################################################################

-- Nature d'une réunion.
CREATE TYPE type_reunion AS ENUM ('seance', 'commission', 'initiative_parlementaire');

-- Avancement d'une réunion.
CREATE TYPE statut_reunion AS ENUM ('confirme', 'annule');

-- Nature d'une prise de parole.
-- ex. interruption = « Très bien ! », reponse_gouvernement = réponse d'un ministre en séance de questions.
CREATE TYPE type_intervention AS ENUM ('intervention', 'interruption', 'question', 'reponse_gouvernement', 'explication_vote');

-- Mode de scrutin public.
CREATE TYPE type_vote AS ENUM ('ordinaire', 'solennel', 'motion_censure');

-- Objet soumis au vote.
-- ex. ensemble = vote sur l'ensemble du texte ; credits = vote d'une mission budgétaire.
CREATE TYPE objet_vote AS ENUM ('amendement', 'article', 'ensemble', 'motion', 'credits', 'declaration', 'autre');

-- Dénouement d'un scrutin public.
CREATE TYPE denouement_scrutin AS ENUM ('adopte', 'rejete');

-- Position d'un votant, ou position majoritaire d'un groupe.
CREATE TYPE position_vote AS ENUM ('pour', 'contre', 'abstention', 'non_votant', 'absent');

-- Rôle : réunions, séances publiques comme réunions de commission.
CREATE TABLE reunions (
  id          INTEGER PRIMARY KEY,
  uid         VARCHAR NOT NULL UNIQUE CHECK (non_vide(uid)),  -- ex. 'RUANR5L17S2025IDS29396', 'CRSANR5L15S2018O1N123', 'SENAT-d20250429'
  organe_id   INTEGER NOT NULL REFERENCES organes (id),  -- l'assemblée pour une séance, la commission sinon
  type        type_reunion NOT NULL,                -- valeurs : seance | commission | initiative_parlementaire
  statut      statut_reunion NOT NULL,              -- valeurs : confirme | annule
  debut       TIMESTAMPTZ NOT NULL,
  fin         TIMESTAMPTZ,
  lieu        VARCHAR CHECK (non_vide(lieu)),       -- ex. 'Sénat', 'Salle 4223 – Commission des affaires étrangères, ...'
  created_at  TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id   INTEGER REFERENCES imports (id),
  source_hash VARCHAR CHECK (est_md5(source_hash)),
  CHECK (fin >= debut),
  CHECK (updated_at >= created_at)
  -- Organe d'une séance = l'assemblée ou le Sénat : macro seances_hors_hemicycle().
);
COMMENT ON TABLE reunions IS 'Réunion : séance publique ou réunion de commission.';

-- Rôle : la discussion d'un amendement en réunion (séance ou commission) :
-- où et dans quel ordre. Une ligne par amendement discuté.
CREATE TABLE amendement_discussions (
  amendement_id INTEGER PRIMARY KEY REFERENCES amendements (id),
  reunion_id    INTEGER REFERENCES reunions (id),   -- réunion où l'amendement est discuté
  cle_tri       VARCHAR CHECK (non_vide(cle_tri)),  -- ordre de discussion fourni par l'AN (triAmendement), ex. 'bgaaaa…aag'
  created_at    TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id     INTEGER REFERENCES imports (id),
  -- Impact : une ligne de discussion porte au moins une information.
  CHECK (reunion_id IS NOT NULL OR cle_tri IS NOT NULL),
  CHECK (updated_at >= created_at)
);
COMMENT ON TABLE amendement_discussions IS 'Discussion d''un amendement : réunion et ordre de passage.';

-- Rôle : un scrutin public, avec son décompte officiel.
CREATE TABLE scrutins (
  id                     INTEGER PRIMARY KEY,
  uid                    VARCHAR NOT NULL UNIQUE,   -- ex. 'VTANR5L17V8745', 'SENAT-SCR-2025-123'
  periode_legislative_id SMALLINT NOT NULL,         -- conservée : le numéro recommence à chaque période
  chambre                chambre NOT NULL,          -- valeurs : assemblee | senat
  numero                 INTEGER NOT NULL CHECK (numero > 0),  -- par législature (AN) ou par session (Sénat), ex. 8745
  date_scrutin           DATE NOT NULL,
  reunion_id             INTEGER REFERENCES reunions (id),
  dossier_id             INTEGER REFERENCES dossiers (id),
  texte_id               INTEGER,
  article_id             INTEGER,
  type_vote              type_vote NOT NULL,        -- valeurs : ordinaire | solennel | motion_censure
  objet_vote             objet_vote NOT NULL,       -- valeurs : amendement | article | ensemble | motion | credits | declaration | autre
  titre                  VARCHAR NOT NULL CHECK (non_vide(titre)),  -- ex. 'l''amendement n° 83 de M. Dupont à l''article 2'
  demandeur              VARCHAR CHECK (non_vide(demandeur)),       -- ex. 'Présidente du groupe "Rassemblement National"'
  denouement             denouement_scrutin NOT NULL,  -- valeurs : adopte | rejete
  nb_votants             SMALLINT NOT NULL CHECK (nb_votants >= 0),  -- ex. 545
  nb_pour                SMALLINT NOT NULL CHECK (nb_pour >= 0),
  nb_contre              SMALLINT NOT NULL CHECK (nb_contre >= 0),
  nb_abstention          SMALLINT NOT NULL CHECK (nb_abstention >= 0),
  created_at             TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id              INTEGER REFERENCES imports (id),
  source_hash            VARCHAR CHECK (est_md5(source_hash)),
  -- Impact : uid au format de sa chambre ; pour l'AN, le numéro est celui de l'uid.
  CHECK (CASE chambre
           WHEN 'senat' THEN regexp_full_match(uid, 'SENAT-SCR-[0-9]{4}-[0-9]+')
           WHEN 'assemblee' THEN regexp_full_match(uid, 'VT(ANR|CGR)5L[0-9]+V[0-9]+')  -- CGR = Congrès
                AND numero = CAST(regexp_extract(uid, '[0-9]+$') AS INTEGER)
           ELSE false END),                                -- chambre sans règle (PE) : refusée
  -- Impact : votants = pour + contre + abstentions (100 % des scrutins de clair).
  CHECK (nb_pour + nb_contre + nb_abstention = nb_votants),
  -- Impact : une motion de censure est un vote sur une motion.
  CHECK (type_vote <> 'motion_censure' OR objet_vote = 'motion'),
  CHECK (updated_at >= created_at),
  FOREIGN KEY (periode_legislative_id, chambre) REFERENCES periodes_legislatives (id, chambre),
  -- Impact : si texte et dossier sont renseignés, le texte appartient au dossier.
  FOREIGN KEY (texte_id, dossier_id) REFERENCES textes (id, dossier_id),
  FOREIGN KEY (article_id, texte_id) REFERENCES articles (id, texte_id),
  UNIQUE (periode_legislative_id, numero)
  -- Date du scrutin dans sa période : macro scrutins_hors_periode().
);
COMMENT ON TABLE scrutins IS 'Scrutin public et son décompte officiel.';

-- Rôle : amendements soumis à un scrutin. Un scrutin peut porter sur
-- plusieurs amendements identiques.
CREATE TABLE scrutin_amendements (
  scrutin_id    INTEGER NOT NULL REFERENCES scrutins (id),
  amendement_id INTEGER NOT NULL REFERENCES amendements (id),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id     INTEGER REFERENCES imports (id),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (scrutin_id, amendement_id)
);
COMMENT ON TABLE scrutin_amendements IS 'Amendements soumis à un scrutin.';

-- Rôle : position majoritaire et décompte de chaque groupe, tels que publiés par l'AN.
CREATE TABLE scrutin_groupes (
  scrutin_id           INTEGER NOT NULL REFERENCES scrutins (id),
  groupe_id            INTEGER NOT NULL REFERENCES groupes_politiques (organe_id),
  position_majoritaire position_vote NOT NULL,      -- valeurs : pour | contre | abstention | non_votant | absent
  nb_pour              SMALLINT NOT NULL CHECK (nb_pour >= 0),
  nb_contre            SMALLINT NOT NULL CHECK (nb_contre >= 0),
  nb_abstention        SMALLINT NOT NULL CHECK (nb_abstention >= 0),
  nb_non_votants       SMALLINT NOT NULL CHECK (nb_non_votants >= 0),
  created_at           TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id            INTEGER REFERENCES imports (id),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (scrutin_id, groupe_id)
  -- Décomptes des groupes <= décompte du scrutin : macro scrutin_groupes_excedentaires().
);
COMMENT ON TABLE scrutin_groupes IS 'Position majoritaire et décompte de chaque groupe dans un scrutin.';

-- Rôle : vote nominatif d'une personne dans un scrutin.
CREATE TABLE votes (
  scrutin_id     INTEGER NOT NULL REFERENCES scrutins (id),
  personne_id    INTEGER NOT NULL REFERENCES personnes (id),
  groupe_id      INTEGER REFERENCES groupes_politiques (organe_id),  -- groupe du votant au moment du vote (calcul de loyauté)
  position       position_vote NOT NULL,            -- valeurs : pour | contre | abstention | non_votant | absent
  par_delegation BOOLEAN NOT NULL DEFAULT false,    -- vote exprimé par délégation
  created_at     TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id      INTEGER REFERENCES imports (id),
  -- Impact : une délégation porte un vote exprimé (pour, contre, abstention).
  CHECK (NOT par_delegation OR position IN ('pour', 'contre', 'abstention')),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (scrutin_id, personne_id)
);
COMMENT ON TABLE votes IS 'Vote nominatif d''une personne dans un scrutin.';

-- Rôle : une prise de parole dans une réunion, avec son texte.
CREATE TABLE interventions (
  id              INTEGER PRIMARY KEY,
  uid             VARCHAR NOT NULL UNIQUE CHECK (non_vide(uid)),
  reunion_id      INTEGER NOT NULL REFERENCES reunions (id),
  ordre           INTEGER NOT NULL CHECK (ordre >= 1),  -- rang dans la réunion, ex. 152
  personne_id     INTEGER REFERENCES personnes (id),    -- NULL si l'orateur n'est pas identifié
  dossier_id      INTEGER REFERENCES dossiers (id),
  texte_id        INTEGER REFERENCES textes (id),
  article_id      INTEGER,
  type            type_intervention NOT NULL,       -- valeurs : intervention | interruption | question | reponse_gouvernement | explication_vote
  est_presidence  BOOLEAN NOT NULL DEFAULT false,   -- parole du président de séance
  orateur_libelle VARCHAR NOT NULL CHECK (non_vide(orateur_libelle)),  -- nom tel qu'imprimé, ex. 'Mme Marie Dupont'
  qualite         VARCHAR CHECK (non_vide(qualite)),  -- ex. 'rapporteure', 'ministre de l''économie'
  contenu         VARCHAR NOT NULL CHECK (non_vide(contenu)),  -- ex. 'Monsieur le président, mes chers collègues...'
  created_at      TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id       INTEGER REFERENCES imports (id),
  source_hash     VARCHAR CHECK (est_md5(source_hash)),
  CHECK (updated_at >= created_at),
  -- Impact : l'article cité appartient au texte cité.
  FOREIGN KEY (article_id, texte_id) REFERENCES articles (id, texte_id),
  UNIQUE (reunion_id, ordre)
);
COMMENT ON TABLE interventions IS 'Prise de parole dans une réunion, avec son texte.';

-- Rôle : amendements cités dans une prise de parole (remplace le tableau
-- text[] amendements_vises de clair).
CREATE TABLE intervention_amendements (
  intervention_id INTEGER NOT NULL REFERENCES interventions (id),
  amendement_id   INTEGER NOT NULL REFERENCES amendements (id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id       INTEGER REFERENCES imports (id),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (intervention_id, amendement_id)
);
COMMENT ON TABLE intervention_amendements IS 'Amendements cités dans une prise de parole.';

-- Rôle : scrutins liés à une prise de parole (ex. explication de vote).
CREATE TABLE intervention_scrutins (
  intervention_id INTEGER NOT NULL REFERENCES interventions (id),
  scrutin_id      INTEGER NOT NULL REFERENCES scrutins (id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT current_timestamp,
  import_id       INTEGER REFERENCES imports (id),
  CHECK (updated_at >= created_at),
  PRIMARY KEY (intervention_id, scrutin_id)
);
COMMENT ON TABLE intervention_scrutins IS 'Scrutins liés à une prise de parole.';


-- =====================================================================
-- MACROS DE CONTRÔLE
-- Règles que DuckDB ne vérifie pas à l'insertion (portent sur plusieurs
-- lignes ou plusieurs tables). Chaque macro renvoie les lignes en anomalie ;
-- controles() les résume. Usage en étape 7 :
--   SELECT error('contrôle échoué : ' || controle || ' (' || nb || ')')
--   FROM controles() WHERE bloquant AND nb > 0;
-- =====================================================================

-- Ex-EXCLUDE : deux périodes d'une même chambre qui se chevauchent.
CREATE MACRO periodes_qui_se_chevauchent() AS TABLE
  SELECT a.id AS id_a, b.id AS id_b, a.chambre
  FROM periodes_legislatives a JOIN periodes_legislatives b
    ON a.chambre = b.chambre AND a.id < b.id
   AND se_chevauchent(a.date_debut, a.date_fin, b.date_debut, b.date_fin);

-- Information : deux mandats d'une personne dans le même organe qui se
-- chevauchent. Cas normal : l'AN publie un mandat par qualité (membre, puis
-- vice-président en parallèle) ; même qualité = doublon probable.
CREATE MACRO mandats_qui_se_chevauchent() AS TABLE
  SELECT a.id AS id_a, b.id AS id_b, a.personne_id, a.organe_id
  FROM mandats a JOIN mandats b
    ON a.personne_id = b.personne_id AND a.organe_id = b.organe_id AND a.id < b.id
   AND se_chevauchent(a.date_debut, a.date_fin, b.date_debut, b.date_fin);

-- Information : deux groupes politiques en même temps (AN ou Sénat). Cas
-- vus dans clair : bornes de deux législatures qui se recouvrent de quelques
-- jours. Une alliance (ALLIANCE) n'est pas un groupe : pas de conflit.
CREATE MACRO groupes_qui_se_chevauchent() AS TABLE
  SELECT a.id AS id_a, b.id AS id_b, a.personne_id
  FROM mandats a JOIN mandats b
    ON a.personne_id = b.personne_id AND a.id < b.id
   AND a.organe_type IN ('GP', 'GROUPESENAT') AND b.organe_type IN ('GP', 'GROUPESENAT')
   AND se_chevauchent(a.date_debut, a.date_fin, b.date_debut, b.date_fin);

-- Information : répartition des mandats chevauchant un autre mandat du même
-- organe, par type d'organe ; part = mandats concernés / mandats du type.
CREATE MACRO chevauchements_par_type() AS TABLE
  WITH ids AS (SELECT id_a AS id FROM mandats_qui_se_chevauchent()
               UNION SELECT id_b FROM mandats_qui_se_chevauchent())
  SELECT m.organe_type, famille_du_type(m.organe_type) AS famille, count(*) AS nb_mandats,
         count(i.id) AS nb_chevauchants, round(100.0 * count(i.id) / count(*), 1) AS part_pct
  FROM mandats m LEFT JOIN ids i ON i.id = m.id
  GROUP BY ALL ORDER BY nb_chevauchants DESC;

-- Identifiant hors du format de sa source (sources.format_identifiant) ;
-- une source sans format ne peut pas fournir d'identifiant.
CREATE MACRO identifiants_hors_format() AS TABLE
  SELECT i.personne_id, i.source, i.valeur
  FROM personne_identifiants i JOIN sources s ON s.code = i.source
  WHERE s.format_identifiant IS NULL OR NOT regexp_full_match(i.valeur, s.format_identifiant);

-- Lien d'organes incohérent : membre_de vise une alliance ou un parti ;
-- affilie_a part d'un groupe ; succede_a relie deux organes de même type.
CREATE MACRO liens_cible_incoherente() AS TABLE
  SELECT l.organe_id, l.organe_cible_id, l.type, o.type AS organe_type, c.type AS cible_type
  FROM organe_liens l
  JOIN organes o ON o.id = l.organe_id
  JOIN organes c ON c.id = l.organe_cible_id
  WHERE CASE l.type
          WHEN 'membre_de' THEN c.type NOT IN ('ALLIANCE', 'PARPOL')
          WHEN 'affilie_a' THEN o.type NOT IN ('GP', 'GROUPESENAT')
          WHEN 'succede_a' THEN o.type <> c.type
          ELSE true END;

-- Filiation d'article hors navette : la source est dans le même dossier,
-- dans un texte de rang antérieur.
CREATE MACRO filiations_hors_navette() AS TABLE
  SELECT f.article_id, f.article_source_id
  FROM article_filiations f
  JOIN articles a ON a.id = f.article_id         JOIN textes t ON t.id = a.texte_id
  JOIN articles s ON s.id = f.article_source_id  JOIN textes ts ON ts.id = s.texte_id
  WHERE ts.dossier_id <> t.dossier_id OR ts.ordre_dossier >= t.ordre_dossier;

-- Valeur d'ENUM sans règle dans sa macro (famille, libellé) : une valeur
-- ajoutée au type doit l'être aussi dans les macros qui la décrivent.
CREATE MACRO vocabulaires_incomplets() AS TABLE
            SELECT 'type_organe' AS vocabulaire, CAST(t AS VARCHAR) AS valeur
            FROM (SELECT unnest(enum_range(NULL::type_organe)) AS t)
            WHERE famille_du_type(t) IS NULL OR libelle_type_organe(t) IS NULL
  UNION ALL SELECT 'qualite_mandat', CAST(q AS VARCHAR)
            FROM (SELECT unnest(enum_range(NULL::qualite_mandat)) AS q)
            WHERE libelle_qualite(q, NULL) IS NULL OR libelle_qualite(q, 'mme') IS NULL
  UNION ALL SELECT 'procedure_parlementaire', CAST(p AS VARCHAR)
            FROM (SELECT unnest(enum_range(NULL::procedure_parlementaire)) AS p)
            WHERE libelle_procedure(p) IS NULL
  UNION ALL SELECT 'motif_denouement', CAST(m AS VARCHAR)
            FROM (SELECT unnest(enum_range(NULL::motif_denouement)) AS m)
            WHERE categorie_du_motif(m) IS NULL;

-- Texte AN : la législature de l'uid (L17) est celle de la période.
CREATE MACRO textes_hors_periode() AS TABLE
  SELECT t.id, t.uid, p.numero AS periode_numero
  FROM textes t JOIN periodes_legislatives p ON p.id = t.periode_legislative_id
  WHERE t.chambre = 'assemblee'
    AND CAST(regexp_extract(t.uid, 'L([0-9]+)B', 1) AS INTEGER) <> p.numero;

-- Scrutin : sa date tombe dans sa période ; pour l'AN, la législature de l'uid aussi.
CREATE MACRO scrutins_hors_periode() AS TABLE
  SELECT s.id, s.uid, s.date_scrutin, p.numero AS periode_numero
  FROM scrutins s JOIN periodes_legislatives p ON p.id = s.periode_legislative_id
  WHERE NOT en_cours_le(p.date_debut, p.date_fin, s.date_scrutin)
     OR (s.chambre = 'assemblee' AND CAST(regexp_extract(s.uid, 'L([0-9]+)V', 1) AS INTEGER) <> p.numero);

-- Amendement AN : l'organe de l'uid (PO...) est l'organe d'examen.
CREATE MACRO amendements_organe_incoherent() AS TABLE
  SELECT a.id, a.uid, o.uid AS organe_examen_uid
  FROM amendements a LEFT JOIN organes o ON o.id = a.organe_examen_id
  WHERE starts_with(a.uid, 'AMANR')
    AND o.uid IS DISTINCT FROM regexp_extract(a.uid, 'PO[0-9]+');

-- Séance publique : tenue par l'assemblée ou le Sénat (organe de type ASSEMBLEE ou SENAT).
CREATE MACRO seances_hors_hemicycle() AS TABLE
  SELECT r.id, r.uid, o.type AS organe_type
  FROM reunions r JOIN organes o ON o.id = r.organe_id
  WHERE r.type = 'seance' AND o.type NOT IN ('ASSEMBLEE', 'SENAT');

-- Décomptes de groupes : leur somme ne dépasse pas le décompte du scrutin.
CREATE MACRO scrutin_groupes_excedentaires() AS TABLE
  SELECT s.id, s.uid
  FROM scrutins s JOIN scrutin_groupes g ON g.scrutin_id = s.id
  GROUP BY s.id, s.uid, s.nb_pour, s.nb_contre, s.nb_abstention
  HAVING sum(g.nb_pour) > s.nb_pour OR sum(g.nb_contre) > s.nb_contre
      OR sum(g.nb_abstention) > s.nb_abstention;

-- Amendement soumis à un scrutin : même texte que le scrutin, quand il est connu.
CREATE MACRO scrutin_amendements_autre_texte() AS TABLE
  SELECT x.scrutin_id, x.amendement_id
  FROM scrutin_amendements x
  JOIN scrutins s ON s.id = x.scrutin_id
  JOIN amendements a ON a.id = x.amendement_id
  WHERE s.texte_id IS NOT NULL AND s.texte_id <> a.texte_id;

-- Alerte (non bloquante) : dénouement d'un amendement contraire au scrutin
-- qui le porte (97,5 % de concordance dans clair : amendements identiques).
CREATE MACRO denouements_contraires_au_scrutin() AS TABLE
  SELECT x.amendement_id, x.scrutin_id, a.denouement, s.denouement AS denouement_scrutin
  FROM scrutin_amendements x
  JOIN amendements a ON a.id = x.amendement_id
  JOIN scrutins s ON s.id = x.scrutin_id
  WHERE a.denouement IN ('adopte', 'rejete') AND CAST(a.denouement AS VARCHAR) <> CAST(s.denouement AS VARCHAR);

-- Alerte (non bloquante) : l'auteur figure aussi parmi les cosignataires.
CREATE MACRO auteurs_cosignataires() AS TABLE
  SELECT c.amendement_id, c.personne_id
  FROM amendement_cosignataires c JOIN amendements a ON a.id = c.amendement_id
  WHERE a.auteur_id = c.personne_id;

-- Alerte (non bloquante) : vote dont le groupe n'est pas celui du mandat GP
-- de la personne à la date du scrutin.
CREATE MACRO votes_groupe_incoherent() AS TABLE
  SELECT v.scrutin_id, v.personne_id, v.groupe_id
  FROM votes v JOIN scrutins s ON s.id = v.scrutin_id
  WHERE v.groupe_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM mandats m
                    WHERE m.personne_id = v.personne_id AND m.organe_id = v.groupe_id
                      AND en_cours_le(m.date_debut, m.date_fin, s.date_scrutin));

-- Synthèse : une ligne par contrôle, nb = nombre de lignes en anomalie.
CREATE MACRO controles() AS TABLE
            SELECT 'periodes_qui_se_chevauchent' AS controle, true AS bloquant, count(*) AS nb FROM periodes_qui_se_chevauchent()
  UNION ALL SELECT 'identifiants_hors_format', true, count(*) FROM identifiants_hors_format()
  UNION ALL SELECT 'liens_cible_incoherente', true, count(*) FROM liens_cible_incoherente()
  UNION ALL SELECT 'filiations_hors_navette', true, count(*) FROM filiations_hors_navette()
  UNION ALL SELECT 'vocabulaires_incomplets', true, count(*) FROM vocabulaires_incomplets()
  UNION ALL SELECT 'textes_hors_periode', true, count(*) FROM textes_hors_periode()
  UNION ALL SELECT 'scrutins_hors_periode', true, count(*) FROM scrutins_hors_periode()
  UNION ALL SELECT 'amendements_organe_incoherent', true, count(*) FROM amendements_organe_incoherent()
  UNION ALL SELECT 'seances_hors_hemicycle', true, count(*) FROM seances_hors_hemicycle()
  UNION ALL SELECT 'scrutin_groupes_excedentaires', true, count(*) FROM scrutin_groupes_excedentaires()
  UNION ALL SELECT 'scrutin_amendements_autre_texte', true, count(*) FROM scrutin_amendements_autre_texte()
  UNION ALL SELECT 'denouements_contraires_au_scrutin', false, count(*) FROM denouements_contraires_au_scrutin()
  UNION ALL SELECT 'auteurs_cosignataires', false, count(*) FROM auteurs_cosignataires()
  UNION ALL SELECT 'mandats_qui_se_chevauchent', false, count(*) FROM mandats_qui_se_chevauchent()
  UNION ALL SELECT 'groupes_qui_se_chevauchent', false, count(*) FROM groupes_qui_se_chevauchent()
  UNION ALL SELECT 'votes_groupe_incoherent', false, count(*) FROM votes_groupe_incoherent();
