---
title: Prompt de conception
description: Brief complet de conception de l'interface, rédigé à partir des wireframes Figma. Référence pour le design et le découpage des composants.
---

:::note
Document de travail : il décrit la cible complète. Les règles visuelles du [design system](/02-design-system) priment en cas d'écart.
:::

Je reprends désormais uniquement la page [Wireframes (En cours)](https://www.figma.com/design/3RA5EVvHh7cOdm7TrpaJG0/Data-for-Good-x-Democracy-Watch?node-id=125-11108), en utilisant le [style guide fourni](https://www.figma.com/design/3RA5EVvHh7cOdm7TrpaJG0/Data-for-Good-x-Democracy-Watch?node-id=218-709).

Les écrans à retenir sont : landing publique, connexion/inscription, accueil, recherche, ajout de textes à l’étude, Mes textes de loi, fiche texte/article, Mes amendements suivis, vue d’avancement et fiche amendement.

Voici le prompt complet réutilisable.

Conçois et implémente l’interface complète de Democracy Watch à partir de la page Figma « Wireframes (En cours) » et de son design system.

Ne pas utiliser les pages Figma « Idéation » ou « benchmark & user journey » comme sources visuelles finales. Elles peuvent expliquer certains besoins, mais les écrans à produire doivent suivre exclusivement les Wireframes actuels et le style guide.

## 1. Positionnement du produit

Democracy Watch est un outil professionnel de veille législative destiné principalement aux associations, ONG et équipes de plaidoyer.

Il permet de :

- rechercher des textes de loi, articles, amendements, députés ou groupes parlementaires ;
- sélectionner les textes et les articles à suivre ;
- surveiller les évolutions du parcours législatif ;
- identifier les nouveaux amendements ;
- comprendre rapidement l’effet concret d’un amendement ;
- retrouver ses auteurs et cosignataires ;
- identifier des amendements identiques, proches ou redéposés ;
- suivre leur passage entre commission pour avis, commission au fond et séance publique ;
- mesurer les risques et opportunités au regard des causes suivies par une organisation.

Le produit doit donner l’impression d’un outil institutionnel fiable, précis et méthodique, sans devenir froid ou administratif. Il doit ressembler à un poste de pilotage éditorial et législatif : dense en information, mais très hiérarchisé.

## 2. Principes fonctionnels

Respecter les principes suivants dans toutes les pages :

1. Montrer d’abord l’information utile à la décision.
2. Permettre d’accéder ensuite au détail juridique exact.
3. Toujours distinguer :
   - une donnée officielle ;
   - une reformulation en langage clair ;
   - une information calculée ;
   - une correspondance probable ;
   - une interprétation personnalisée.
4. Toujours conserver le lien entre :
   - texte de loi ;
   - article ;
   - alinéa ;
   - amendement ;
   - auteur et cosignataires ;
   - commission ;
   - étape législative.
5. Concevoir une interface simple au premier regard, mais permettant une lecture experte à la demande.
6. Mettre en avant les changements depuis la dernière visite.
7. Utiliser les alertes avec parcimonie : une couleur d’alerte signale une information réellement actionnable.
8. Toujours indiquer la source officielle, la date de mise à jour et, lorsque nécessaire, le niveau de confiance.

## 3. Fondations visuelles

### Typographie

Utiliser Archivo pour l’interface, les titres, les boutons, les champs, les tableaux et les métadonnées.

Utiliser Spectral pour les contenus juridiques longs : alinéas, citations, dispositifs, extraits de loi et comparaisons avant/après.

Le logotype Democracy Watch utilise Archivo ExtraBold Italic 800. Ne pas reproduire approximativement le logo avec une autre graisse.

Hiérarchie typographique recommandée :

- Titre de page : Archivo Bold, 32 à 40 px, interligne resserré.
- Titre de section : Archivo Bold, 24 à 28 px.
- Sous-titre : Archivo Bold, 18 à 20 px.
- Corps MD : Archivo Regular, environ 16/24 px.
- Corps MD gras : Archivo Bold, environ 16/24 px.
- Corps SM : Archivo Regular, environ 14/24 px.
- Corps SM gras : Archivo Bold, environ 14/24 px.
- Métadonnée XS : Archivo Regular, environ 12/20 px.
- Badge : Archivo Bold, 12/20 px, souvent en capitales.
- Alinéa juridique : Spectral Regular, environ 18/28 px.
- Citation juridique : Spectral Italic, environ 18/30 px.
- Logo : Archivo ExtraBold Italic, environ 28/28 px.

La lecture doit rester confortable. Éviter les textes fonctionnels de moins de 12 px.

### Couleurs

Utiliser des tokens sémantiques. Ne pas appliquer directement les couleurs sans préciser leur fonction.

Palette principale observée :

- Vert encre — `#17322E` :
  actions principales, liens importants, onglet actif, cases cochées, logo et titres de marque.
- Jaune accent — `#EDF58A` :
  nouveautés, surlignages, petits accents de marque.
- Jaune pâle — `#F7FBDD` :
  fonds alternatifs, bandeaux de marque, zones de connexion et encarts légers.
- Sarcelle — `#2E9F92` :
  décoration et visualisation de données uniquement ; ne pas l’utiliser pour du texte courant.
- Sarcelle texte — `#1F6F66` :
  texte ou liens secondaires lorsque le contraste est suffisant.
- Texte principal sombre — environ `#3A3A3A`.
- Texte secondaire et métadonnées — `#666666`.
- Bordures et séparateurs — `#DDDDDD`.
- Erreur, fond — `#FFE9E9`.
- Avertissement, fond — `#FFE9E6`.
- Succès — `#18753C`.
- Information — `#0063CB`.
- Focus clavier — `#0A76F6`.

Prévoir des fonds sémantiques très clairs associés aux couleurs succès, erreur, avertissement et information.

Ne jamais dépendre uniquement de la couleur : ajouter un libellé, une icône ou une forme de statut.

### Espacements

Utiliser une échelle fondée sur une unité de 4 px.

Valeurs structurantes :

- 24 px : padding intérieur des cartes ;
- 32 px : espacement entre blocs ;
- 40 px : séparation entre sections courtes ;
- 48 px : séparation entre grandes sections ;
- 64 à 80 px : respiration verticale des pages marketing.

Utiliser des espacements plus réduits — 4, 8, 12 et 16 px — pour les icônes, badges, lignes de métadonnées et groupes de contrôles.

### Rayons et formes

- Champs DSFR et éléments strictement institutionnels : angles droits ou très faiblement arrondis.
- Petits contrôles et badges : rayon de 4 à 8 px.
- Cartes et panneaux : rayon de 16 px.
- Bandeaux de marque, panneaux principaux et éléments très expressifs : rayon de 28 px.
- Éviter l’accumulation de cartes excessivement arrondies.

### Bordures, ombres et focus

- Utiliser principalement des bordures fines de 1 px.
- Réserver les ombres aux panneaux flottants, modales et éléments superposés.
- Les cartes cliquables peuvent utiliser un accent inférieur de 4 px, inspiré du motif `fr-card` du DSFR.
- Tout élément focusable doit afficher un contour clavier de 2 px en `#0A76F6`, avec un décalage de 2 px.
- Le focus clavier ne doit jamais être supprimé.

## 4. Structure responsive commune

Créer un composant `AppShell` comprenant :

- un en-tête principal ;
- le logo Democracy Watch ;
- une recherche globale ;
- la navigation principale ;
- les actions liées au compte ;
- une zone de contenu ;
- éventuellement un fil d’Ariane ;
- une zone de notifications ;
- un pied de page institutionnel.

Desktop :

- largeur de référence : 1440 px ;
- contenu principal limité à environ 1280–1360 px ;
- colonnes latérales entre 260 et 320 px ;
- gouttières de 24 à 32 px.

Tablette :

- transformer les filtres latéraux en panneau escamotable ;
- conserver les onglets et les principales actions ;
- permettre le défilement horizontal contrôlé des tableaux.

Mobile :

- navigation compacte ;
- recherche globale accessible depuis une action dédiée ;
- filtres dans une drawer ;
- cartes empilées ;
- tableaux transformés en listes structurées ;
- actions principales conservées dans une barre inférieure si nécessaire.

## 5. Bibliothèque de composants

### Identité et navigation

Créer :

- `LogoDemocracyWatch` :
  variantes horizontale, compacte et pictogramme seul.
- `HeaderPublic` :
  logo, navigation marketing, connexion et création de compte.
- `HeaderAuthenticated` :
  logo, recherche globale, navigation, notifications et menu du compte.
- `GlobalSearch` :
  vide, rempli, focus, chargement, résultats suggérés, erreur.
- `PrimaryNavigation` :
  Accueil, Mes textes de loi, Mes amendements suivis.
- `MobileNavigation`.
- `Breadcrumb`.
- `PageHeader`.
- `SectionHeader`.
- `FooterInstitutional`.
- `AccountMenu`.
- `NotificationButton`.

La navigation doit indiquer clairement l’onglet actif avec la couleur d’action et un soulignement visible.

### Boutons et actions

Créer :

- bouton primaire ;
- bouton secondaire ;
- bouton tertiaire ;
- bouton texte ;
- bouton avec icône ;
- bouton icône seul ;
- bouton de suppression ou action dangereuse ;
- bouton de retour ;
- bouton de téléchargement/export ;
- bouton à largeur complète ;
- groupe de boutons ;
- barre d’actions collante.

États obligatoires :

- défaut ;
- survol ;
- focus clavier ;
- actif ;
- chargement ;
- désactivé ;
- succès temporaire ;
- erreur.

Tailles :

- petite ;
- moyenne ;
- grande.

### Formulaires

Créer :

- champ texte ;
- champ e-mail ;
- champ mot de passe ;
- bouton afficher/masquer le mot de passe ;
- zone de texte ;
- champ de recherche ;
- recherche avec suggestions ;
- case à cocher ;
- groupe de cases à cocher ;
- bouton radio ;
- interrupteur ;
- select ;
- multiselect ;
- autocomplétion ;
- sélecteur de période ;
- champ de mots-clés ;
- filtre par numéro de texte ;
- filtre par auteur ou rapporteur ;
- filtre par commission ;
- filtre par groupe parlementaire ;
- message d’aide ;
- message d’erreur ;
- message de succès ;
- indicateur de champ obligatoire.

Tous les champs doivent posséder un label visible. Ne pas utiliser le placeholder comme unique libellé.

### Badges, tags et statuts

Créer des composants distincts pour :

- type de texte : PJL, PPL, PLF ;
- commission au fond ;
- commission pour avis ;
- groupe parlementaire ;
- nombre de cosignataires ;
- transpartisan ;
- étape législative ;
- adopté ;
- rejeté ;
- tombé ;
- retiré ;
- en attente ;
- irrecevable ;
- redéposé ;
- identique ;
- similaire ;
- nouveau ;
- menacé ;
- à l’étude ;
- source officielle ;
- niveau de confiance.

Prévoir les tailles petite et moyenne, avec icône facultative.

### Conteneurs et retours d’état

Créer :

- carte simple ;
- carte cliquable ;
- panneau latéral ;
- callout ;
- alerte ;
- bannière ;
- encart informatif ;
- toast ;
- tooltip ;
- popover ;
- modal ;
- drawer ;
- accordéon ;
- skeleton de chargement ;
- état vide ;
- état d’erreur ;
- état sans résultat ;
- état de source indisponible ;
- état de synchronisation en cours.

### Navigation locale et filtres

Créer :

- onglets ;
- segmented control ;
- filtres latéraux ;
- filtre mobile en drawer ;
- chips de filtres actifs ;
- bouton « Réinitialiser les filtres » ;
- compteur de résultats ;
- tri ;
- pagination ;
- bouton afficher plus ;
- toggle « Regrouper les similaires » ;
- sélecteur de vue :
  - liste ;
  - avancement ;
  - groupe parlementaire.

### Composants législatifs

Créer :

- `LegislativeTextCard` ;
- `LegislativeTextRow` ;
- `ArticleRow` ;
- `AmendmentCard` ;
- `AmendmentCompactRow` ;
- `AuthorIdentity` ;
- `CosignatoriesList` ;
- `ParliamentaryGroupBadge` ;
- `LegislativeStageRail` ;
- `LegislativeTimeline` ;
- `ArticleSummaryNavigation` ;
- `LegalExcerpt` ;
- `LegalParagraph` ;
- `BeforeAfterComparison` ;
- `AmendmentEffectPreview` ;
- `ConfidenceIndicator` ;
- `OfficialSourceLink` ;
- `SimilarAmendmentsGroup` ;
- `AmendmentJourney` ;
- `CauseAssessmentCard` ;
- `DeadlineIndicator` ;
- `NewActivityIndicator`.

Chaque carte de texte de loi doit pouvoir afficher :

- type de texte ;
- commission ;
- numéro ;
- titre ;
- résumé ;
- étape actuelle ;
- prochaines échéances ;
- nombre d’articles ;
- nombre d’amendements ;
- articles suivis ;
- nouveaux amendements ;
- risques détectés ;
- actions disponibles.

Chaque amendement doit pouvoir afficher :

- numéro ;
- article et alinéa ciblés ;
- auteur ;
- groupe ;
- cosignataires ;
- résumé en langage clair ;
- statut ;
- étape ;
- nature de l’amendement ;
- correspondances identiques ou similaires ;
- niveau de confiance ;
- lien vers la source officielle.

## 6. Pages publiques et authentification

### Landing publique

Créer une vraie landing page accessible sans connexion.

Sections :

1. Header public.
2. Hero avec :
   - titre clair ;
   - proposition de valeur ;
   - recherche de démonstration ;
   - bouton « Découvrir Democracy Watch » ;
   - bouton « Se connecter ».
3. Bloc « Gardez un œil sur vos amendements ».
4. Trois bénéfices :
   - suivre les amendements d’un texte par article ;
   - filtrer ceux qui correspondent à un sujet ;
   - repérer les intérêts et acteurs derrière les propositions.
5. Démonstration visuelle de la fiche amendement.
6. Démonstration du suivi des textes.
7. Explication des sources :
   - Assemblée nationale ;
   - Légifrance ;
   - données ouvertes ;
   - périmètre Sénat lorsqu’il sera disponible.
8. Bloc de confiance :
   - données sourcées ;
   - distinction entre fait et analyse ;
   - actualisation ;
   - open data.
9. Cas d’usage pour :
   - association ;
   - ONG ;
   - chargé de plaidoyer ;
   - journaliste ;
   - chercheur.
10. Appel à l’action final.
11. Footer institutionnel.

Le hero doit être très lisible, avec fond jaune pâle, vert encre et illustrations ou captures sobres. Ne pas utiliser de visuels décoratifs génériques.

### Connexion

Créer une page en deux colonnes.

Colonne gauche :

- fond jaune clair ;
- logo ;
- pictogramme de marque ;
- titre « Gardez un œil sur vos amendements » ;
- trois bénéfices courts accompagnés d’icônes.

Colonne droite :

- titre « Connexion » ;
- sous-titre destiné aux associations ;
- e-mail ;
- mot de passe ;
- affichage du mot de passe ;
- mot de passe oublié ;
- rester connecté ;
- bouton « Se connecter » ;
- séparation « ou » ;
- bouton de lien magique par e-mail ;
- lien vers la création de compte.

Prévoir les états : saisie, focus, erreur, identifiants incorrects, chargement, succès et lien magique envoyé.

### Inscription

Ajouter une page complète d’inscription, cohérente avec la connexion.

Étapes possibles :

1. Informations du compte.
2. Organisation.
3. Profil utilisateur.
4. Thématiques suivies.
5. Commissions et mots-clés.
6. Invitation éventuelle de collaborateurs.
7. Confirmation.

Le formulaire peut identifier le persona :

- chargé de plaidoyer ;
- responsable affaires publiques ;
- analyste ;
- journaliste ;
- chercheur ;
- autre.

Prévoir une option permettant de découvrir certaines fonctions sans compte, tout en expliquant ce qui nécessite une connexion.

Ajouter :

- validation d’e-mail ;
- acceptation des conditions ;
- politique de confidentialité ;
- succès de création ;
- compte déjà existant ;
- invitation à rejoindre une organisation existante.

### Mot de passe oublié et lien magique

Créer :

- demande de réinitialisation ;
- confirmation d’envoi ;
- nouveau mot de passe ;
- lien expiré ;
- connexion par lien magique ;
- erreur ou lien déjà utilisé.

## 7. Accueil connecté

L’accueil ne doit pas être une page vide contenant uniquement une recherche.

Ajouter :

- recherche globale ;
- résumé de l’activité depuis la dernière visite ;
- alertes prioritaires ;
- échéances à venir ;
- nouveaux amendements ;
- articles menacés ;
- redépôts détectés ;
- textes récemment suivis ;
- suggestions de textes pouvant correspondre aux thèmes de l’organisation ;
- raccourcis :
  - ajouter un texte ;
  - rechercher un amendement ;
  - consulter mes alertes ;
  - régler mes sujets ;
  - exporter un bilan.

Prévoir un état de première visite avec un onboarding explicatif.

## 8. Mes textes de loi

Construire un tableau de bord de veille.

En-tête :

- titre « Mes textes de loi » ;
- nombre total ;
- explication courte ;
- bouton « Ajouter des textes » ;
- recherche locale ;
- choix liste/cartes si pertinent.

Colonne de filtres :

- commission ;
- thématique ;
- étape ;
- type de texte ;
- échéance ;
- présence de nouveautés ;
- articles menacés ;
- texte suivi manuellement ;
- réinitialisation.

Zone principale :

- compteur ;
- tri ;
- cartes de textes ;
- pagination ou chargement progressif.

Chaque carte doit mettre en évidence :

- titre du texte ;
- type et numéro ;
- commission au fond ;
- commissions pour avis ;
- étapes déjà franchies ;
- étape en cours ;
- prochaine échéance ;
- temps restant ;
- articles suivis ;
- articles menacés ;
- nouveaux amendements ;
- bouton d’accès au texte.

Prévoir :

- aucun texte suivi ;
- aucun résultat filtré ;
- texte pas encore déposé ;
- source momentanément indisponible ;
- texte adopté ;
- texte transmis au Sénat ;
- donnée Sénat non couverte.

## 9. Recherche élargie

Créer une recherche globale couvrant :

- textes de loi ;
- articles ;
- amendements.

Éléments :

- requête visible ;
- nombre total de résultats ;
- onglets par type ;
- synonymes inclus ;
- tri par pertinence ou date ;
- filtres latéraux ;
- extraits surlignés ;
- source ;
- contexte ;
- statut ;
- action d’ouverture ;
- sélection d’un texte ;
- action « Ajouter à mon étude ».

Ajouter une barre d’action persistante lorsqu’un ou plusieurs textes sont sélectionnés.

## 10. Ajouter des textes à l’étude

Utiliser une disposition en deux colonnes :

- tableau principal des textes ;
- panneau « Ma sélection ».

Tableau :

- sélection ;
- titre ;
- type et numéro ;
- étape actuelle ;
- commission ;
- nombre d’articles ;
- nombre d’amendements ;
- source ;
- pagination.

Panneau de sélection :

- textes choisis ;
- suppression d’une sélection ;
- tous les articles ou sélection manuelle ;
- alertes souhaitées ;
- thématique de rangement ;
- bouton final d’ajout.

## 11. Fiche texte et articles

Créer :

- fil d’Ariane ;
- titre du texte ;
- type, numéro et commissions ;
- étape actuelle ;
- accès au dossier législatif ;
- sommaire des articles à gauche ;
- article sélectionné ;
- résumé en langage clair ;
- exposé des motifs ;
- amendements associés ;
- texte juridique par alinéa ;
- visualisation des effets possibles.

Le sommaire doit montrer :

- numéro d’article ;
- titre ;
- nombre d’amendements ;
- article suivi ;
- menaces ;
- modification en commission ;
- article additionnel ;
- report de date.

## 12. Mes amendements suivis

Créer un véritable poste de travail analytique :

- recherche plein texte ;
- recherche par numéro ou auteur ;
- vues liste, avancement et groupe ;
- regroupement des similaires ;
- filtres par texte, article, groupe, statut, étape et date ;
- chips des filtres actifs ;
- lignes compactes mais lisibles ;
- résumé en langage clair ;
- statut très visible ;
- accès à la fiche.

Prévoir un panneau de filtres dense mais organisé en accordéons.

## 13. Vue d’avancement

Présenter les amendements sous forme de tableau ou kanban législatif :

- déposés ;
- commission pour avis ;
- commission au fond ;
- séance publique ;
- éventuellement Sénat si les données deviennent disponibles.

Chaque colonne affiche :

- volume ;
- date ou échéance ;
- état vide ;
- cartes compactes ;
- amendements regroupés ;
- amendements redéposés ;
- statut ;
- auteur et groupe.

## 14. Fiche amendement

Organiser la page en contenu principal et rail contextuel.

Contenu principal :

- titre et numéro ;
- article et alinéa ;
- auteur et cosignataires ;
- groupe ;
- date ;
- statut ;
- commission ;
- résumé ;
- dispositif exact ;
- effet reconstitué ;
- exposé sommaire ;
- parcours législatif ;
- amendements parents et sous-amendements ;
- amendements identiques ou similaires ;
- sources.

Rail contextuel :

- évaluation au regard de la cause ;
- favorabilité ou défavorabilité ;
- repère utilisé ;
- comparaison avec la position de l’organisation ;
- signataires ;
- amendements liés ;
- actions de suivi.

Toujours afficher explicitement :

- « texte exact » ;
- « reconstitué automatiquement » ;
- « à vérifier » ;
- « lien certain » ;
- « lien probable ».

Ne jamais présenter une reconstruction automatique comme un fait officiel.

## 15. Accessibilité et qualité

Respecter WCAG AA au minimum.

Prévoir :

- navigation intégrale au clavier ;
- focus visible ;
- labels explicites ;
- zones cliquables suffisantes ;
- messages d’erreur compréhensibles ;
- contrastes vérifiés ;
- titres hiérarchisés ;
- tableaux accessibles ;
- alternatives textuelles ;
- support du zoom ;
- réduction des animations ;
- absence de dépendance exclusive à la couleur.

## 16. États à concevoir systématiquement

Pour chaque composant et chaque page, prévoir :

- chargement ;
- vide ;
- erreur ;
- succès ;
- désactivé ;
- données partielles ;
- source indisponible ;
- données anciennes ;
- accès non autorisé ;
- première visite ;
- grand volume de résultats ;
- textes très longs ;
- titres sur plusieurs lignes ;
- utilisateurs sans organisation ;
- utilisateurs avec plusieurs organisations.

## 17. Résultat attendu

Produire :

1. les fondations visuelles sous forme de tokens sémantiques ;
2. la bibliothèque complète de composants et variantes ;
3. les écrans desktop ;
4. les adaptations tablette et mobile ;
5. les états interactifs ;
6. les états vides, erreurs et chargements ;
7. les parcours publics et authentifiés ;
8. les règles de provenance et de niveau de confiance ;
9. une nomenclature cohérente des composants ;
10. une documentation courte indiquant quand utiliser chaque composant.

Favoriser les composants réutilisables, les layouts structurés, l’auto-layout, les propriétés de composants et les variants. Éviter les groupes de calques non nommés et les duplications manuelles.
