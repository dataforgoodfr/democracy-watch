-- Données synthétiques des tests, chargées après DATA_MODEL_V3_DUCKDB.sql dans une base
-- en mémoire. Aucune donnée réelle : noms, uid et contenus sont inventés.

INSERT INTO periodes_legislatives (id, chambre, type, numero, libelle, date_debut) VALUES
  (1, 'assemblee', 'legislature', 17, 'XVIIe législature', DATE '2024-07-18');

INSERT INTO organes (id, uid, type, chambre, nom, nom_court, date_debut) VALUES
  (1, 'PO1', 'ASSEMBLEE', 'assemblee', 'Assemblée nationale de la 17e législature', 'AN', DATE '2024-07-18'),
  (2, 'PO2', 'GP', 'assemblee', 'Groupe Alpha', 'ALPHA', NULL),
  (3, 'PO3', 'GP', 'assemblee', 'Groupe Bêta', 'BETA', NULL),
  (4, 'PO4', 'COMPER', 'assemblee', 'Commission des finances', 'CION_FIN', DATE '2024-07-18');
INSERT INTO organes (id, uid, type, chambre, parent_id, nom) VALUES
  (5, 'PO5', 'COMPER', 'assemblee', 4, 'Sous-commission du budget');

INSERT INTO groupes_politiques (organe_id, type, couleur, position_politique) VALUES
  (2, 'GP', '#112233', 'gauche'),
  (3, 'GP', '#445566', 'droite');

INSERT INTO personnes (id, slug, nom, prenom, civilite, profession) VALUES
  (1, 'marie-dupont', 'Dupont', 'Marie', 'mme', 'Avocate'),
  (2, 'jean-martin', 'Martin', 'Jean', 'm', NULL),
  (3, 'luc-ancien', 'Ancien', 'Luc', 'm', NULL);

-- Marie : AN + Alpha + présidente de la commission. Jean : AN, Alpha puis Bêta.
-- Luc : ancien membre de l'AN et d'Alpha (mandats clos).
INSERT INTO mandats (id, uid, personne_id, organe_id, organe_type, qualite, date_debut, date_fin) VALUES
  (1, 'PM1', 1, 1, 'ASSEMBLEE', 'membre', DATE '2024-07-18', NULL),
  (2, 'PM2', 1, 2, 'GP', 'membre', DATE '2024-07-18', NULL),
  (3, 'PM3', 1, 4, 'COMPER', 'president', DATE '2024-07-18', NULL),
  (4, 'PM4', 2, 1, 'ASSEMBLEE', 'membre', DATE '2024-07-18', NULL),
  (5, 'PM5', 2, 2, 'GP', 'membre', DATE '2024-07-18', DATE '2025-01-31'),
  (6, 'PM6', 2, 3, 'GP', 'membre', DATE '2025-02-01', NULL),
  (7, 'PM7', 3, 1, 'ASSEMBLEE', 'membre', DATE '2024-07-18', DATE '2024-12-31'),
  (8, 'PM8', 3, 2, 'GP', 'membre', DATE '2024-07-18', DATE '2024-12-31');

INSERT INTO dossiers (id, uid, procedure, titre, titre_court, statut, denouement, date_depot,
                      date_denouement, loi_numero, loi_titre, loi_date_jo, url_legifrance) VALUES
  (1, 'DLR5L17N1', 'loi_finances', 'Projet de loi de finances pour 2026', 'PLF 2026', 'en_cours',
   NULL, DATE '2025-10-14', NULL, NULL, NULL, NULL, NULL),
  (2, 'DLR5L17N2', 'loi_ordinaire', 'Proposition de loi sur les essais', NULL, 'clos',
   'promulgue', DATE '2024-09-01', DATE '2025-03-01', '2025-12', 'Loi relative aux essais',
   DATE '2025-03-05', 'https://www.legifrance.gouv.fr/jorf/id/TEST');

INSERT INTO textes (id, uid, dossier_id, periode_legislative_id, chambre, nature, numero,
                    ordre_dossier, titre, date_depot) VALUES
  (1, 'PRJLANR5L17B0001', 1, 1, 'assemblee', 'projet', 1, 1, 'Projet de loi de finances', DATE '2025-10-14'),
  (3, 'PIONANR5L17B0003', 2, 1, 'assemblee', 'proposition', 3, 1, NULL, DATE '2024-09-01');
INSERT INTO textes (id, uid, dossier_id, periode_legislative_id, chambre, nature, numero,
                    ordre_dossier, texte_source_id) VALUES
  (2, 'PRJLANR5L17BTC0002', 1, 1, 'assemblee', 'texte_commission', 2, 2, 1);

INSERT INTO articles (id, texte_id, ordre, ordre_place, est_emplacement, numero, libelle, contenu) VALUES
  (1, 1, 1, 10, false, 'PREMIER', 'Article premier', 'Contenu de l''article premier.'),
  (2, 1, 2, 20, false, '2', 'Article 2', 'Contenu de l''article 2.'),
  (4, 2, 1, 10, false, 'PREMIER', 'Article premier', 'Contenu modifié en commission.');
INSERT INTO articles (id, texte_id, ordre_ref, ordre_place, est_emplacement, libelle) VALUES
  (3, 1, 1, 15, true, 'Après l''article premier');

INSERT INTO amendements (id, uid, texte_id, dossier_id, article_id, organe_examen_id,
                         deliberation, auteur_id, groupe_id, numero, numero_ordre, article_vise,
                         statut, denouement, date_depot, est_racine, dispositif, expose_sommaire) VALUES
  (1, 'AMANR5L17PO1B0001P0D1N000001', 1, 1, 1, 1, 1, 1, 2, '1', 1, 'ART. PREMIER',
   'traite', 'rejete', DATE '2025-10-15', true, 'Supprimer cet article.', 'Exposé 1.'),
  (2, 'AMANR5L17PO1B0001P0D1N000002', 1, 1, 3, 1, 1, 2, 3, '2', 2, 'APRÈS ART. PREMIER',
   'a_discuter', NULL, DATE '2025-10-16', true, 'Insérer un article.', NULL),
  (4, 'AMANR5L17PO1BTC0002P0D1N000001', 2, 1, 4, 1, 1, 1, 2, '1', 1, 'ART. PREMIER',
   'a_discuter', NULL, DATE '2025-11-02', true, NULL, NULL);
-- Sous-amendement de l'amendement 1, sans article ni auteur résolus.
INSERT INTO amendements (id, uid, texte_id, dossier_id, parent_id, organe_examen_id,
                         deliberation, numero, numero_ordre, statut, est_racine,
                         parent_doit_etre_racine) VALUES
  (3, 'AMANR5L17PO1B0001P0D1N000003', 1, 1, 1, 1, 1, '3', 3, 'en_recevabilite', false, true);
