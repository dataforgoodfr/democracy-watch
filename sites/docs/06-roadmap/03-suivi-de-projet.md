---
title: Suivi de projet
description: Relier la roadmap aux issues GitHub existantes (#1 → #26), organiser labels, jalons et GitHub Project, et ce qu'il reste à faire.
sidebar_label: "Suivi de projet"
sidebar_icon: clipboard-list
---

:::info{title="Proposition"}
Rien n'a encore été modifié sur GitHub. Cette page propose comment **rattacher la roadmap
(DW-01 → DW-66) aux issues déjà en place**, plutôt que de créer un second suivi en parallèle.
:::

## 1. État actuel (25 octobre 2026)

Le dépôt compte **26 issues**, organisées par trois issues chapeau :

| Chapeau | Sous-issues ouvertes | Sous-issues fermées |
| --- | --- | --- |
| **#1 Produit** | #3 Caler les interviews, #4 Synthèse des interviews, #18 Interview Oxfam, #19 Interview QuotaClimat | #7 FNE, #17 Emmaüs |
| **#8 Data / Back-End** | #21 Script PG → Meilisearch, #22 Extraction des vecteurs, #23 Comptes Vaultwarden | #9, #10, #11, #20, #24 |
| **#12 Front-End** | #13 Page accueil, #14 Section « Textes de loi », #15 Section « Articles », #16 Section « Amendements » | — |

Ce qui manque pour suivre le travail sereinement :

- **#26 API endpoints V0** n'est rattachée à aucun chapeau ;
- **#5 et #6 « Wireframe Democracy Watch »** sont en doublon (#6 est sous-issue de #5) ;
- **aucune issue n'a de label, de jalon ni de description** (sauf #26), presque aucune n'est assignée ;
- la branche `feature/setup-front` (socle front, doc, API) **n'a pas de pull request**.

## 2. Principe : réutiliser avant de créer

1. Si une issue existante couvre le sujet, **on la complète** (description, critères d'acceptation, label, jalon) — on ne crée pas de doublon.
2. Sinon, on crée l'issue DW-NN **comme sous-issue du bon chapeau**.
3. Une issue = une PR = une branche `type/NN-sujet` (ex. `feat/15-kanban-filtres`) ; la PR contient `Closes #NN`.

## 3. Structure cible

Les 10 épiques de la [roadmap](/roadmap) correspondent aux chapeaux GitHub :

```text
#1  Produit ............................ interviews, méthode (DW-02)
#5  Design (ex-Wireframe) .............. DW-03, DW-04, DW-05            ← #6 fermée en doublon
#8  Data / Back-End .................... #21, #22, #23, #26 (rattachée), DW-10 → DW-17, DW-25, DW-26
#12 Front-End
    ├── #13 Page accueil ............... DW-29, DW-38
    ├── #14 Section « Textes de loi » .. DW-20, DW-37
    ├── #15 Section « Articles » ....... DW-18, DW-19, DW-21
    └── #16 Section « Amendements » .... DW-22, DW-23, DW-24, DW-27, DW-28
NOUVEAU  Ops / Déploiement ............. DW-01, DW-06 → DW-09, DW-40, DW-41, DW-43
NOUVEAU  Comptes et alertes ............ DW-30 → DW-36
NOUVEAU  Analytics ..................... DW-50 → DW-56 (Rybbit)
NOUVEAU  Observabilité ................. DW-60 → DW-66 (OpenObserve)
NOUVEAU  Après V0 ...................... DW-39 (landing), DW-42 (Sénat)
```

## 4. Correspondance roadmap ↔ issues

| Roadmap | Issue existante | Action |
| --- | --- | --- |
| DW-01 Labels, jalons, Project | — | créer sous « Ops / Déploiement » |
| DW-02 RFC méthode de travail | #1 Produit | créer comme sous-issue de #1 |
| DW-03 Choix du logo | #5 | sous-issue de #5 |
| DW-04 Couleurs des groupes | #5 | sous-issue de #5 |
| DW-05 Nouvelle itération des maquettes | **#6** | **réutiliser #6** (renommer « Reporter la nouvelle itération des maquettes ») plutôt que la fermer, si l'équipe préfère |
| DW-06 Accès Coolify | #23 (Vaultwarden, secrets) | créer sous « Ops », dépend de #23 |
| DW-07 → DW-09 Déploiement, domaines, CI | — | créer sous « Ops » |
| DW-43 Hébergement du front | — | créer sous « Ops » |
| DW-10 Documenter les index Meilisearch | #21 | sous-issue de #8, dépend de #21 |
| DW-11 Docker de l'API | **#26** | sous-issue de #26 |
| DW-12 Meilisearch alimenté | **#21** | **réutiliser #21** (pas de nouvelle issue) |
| DW-13 → DW-15 Endpoints manquants | **#26** | sous-issues de #26 |
| DW-16 Préproduction en mode API | #26 | sous-issue de #26 |
| DW-17 Tests d'intégration API | #26 | sous-issue de #26 |
| DW-18, DW-19, DW-21 Kanban | **#15** | sous-issues de #15 |
| DW-20 Choisir les articles suivis | **#14** | sous-issue de #14 |
| DW-22 → DW-24, DW-27, DW-28 Comprendre un amendement | **#16** | sous-issues de #16 |
| DW-25 Similaires (≥ 85 %) | **#22** (vecteurs) | sous-issue de #8, dépend de #22 |
| DW-26 Redépôt commission → séance | #22 | sous-issue de #8, dépend de DW-25 |
| DW-29, DW-38 Nouveautés, accueil enrichi | **#13** | sous-issues de #13 |
| DW-30 → DW-36 Délais, alertes, comptes | — | créer sous « Comptes et alertes » |
| DW-37 Fiche texte enrichie | **#14** | sous-issue de #14 |
| DW-39 Landing, DW-42 Sénat | — | créer sous « Après V0 » |
| DW-40 Recette RGAA, DW-41 e2e en mode API | — | créer sous « Ops » |

### Ce que le socle déjà livré permet de fermer ou de mettre à jour

| Issue | Après fusion de `feature/setup-front` |
| --- | --- |
| #12 Front-End | rester ouverte (chapeau) ; cocher « socle » dans la description |
| #13 Page accueil | **première version livrée** ; garder ouverte pour DW-29, DW-38 |
| #14 Section « Textes de loi » | **sélection, suivi, mes textes, fiche texte livrés** ; reste DW-20, DW-37 |
| #15 Section « Articles » | **kanban livré** (données fictives) ; reste DW-18, DW-19, DW-21 |
| #16 Section « Amendements » | **liste et filtres livrés** ; reste la fiche amendement (DW-22 →) |
| #26 API endpoints V0 | **endpoints implémentés** ; fermer après DW-16 (préproduction branchée) |

## 5. Labels, jalons et GitHub Project

**Labels** (en plus de `bug`, `documentation`, `good first issue`, `help wanted` existants) :

| Famille | Labels |
| --- | --- |
| Type | `type:feat`, `type:fix`, `type:docs`, `type:chore` |
| Domaine | `domaine:front`, `domaine:api`, `domaine:data`, `domaine:design`, `domaine:ops`, `domaine:produit` |
| Taille | `taille:S` (≤ ½ j), `taille:M` (≈ 1 j), `taille:L` (2–3 j) |
| Priorité | `V0` (nécessaire le 7 novembre) |

**Jalons** : `V0 — 7 nov. 2026` et `Après V0`.

**GitHub Project** — champs :

| Champ | Valeurs |
| --- | --- |
| Statut | **Backlog · Not Started · To Implement · In Progress · In Testing · In Review · Done** (mêmes colonnes que les Kanban de la doc) |
| Épique | E1 Produit et design · E2 Suivre des textes · E3 Kanban des amendements · E4 Comprendre un amendement · E5 Être prévenu · E6 Comptes et ouverture · E7 Données et API · E8 Ops, qualité et déploiement · E9 Analytics · E10 Observabilité |
| Taille | S · M · L |
| Domaine | Front · API · Data · Design · Ops · Produit |

Vues : **deux tableaux Kanban**, identiques aux pages de la doc —
[« Produit et front »](/roadmap/produit-front) (filtre Épique E1 → E6) et
[« Données, API et ops »](/roadmap/donnees-api-ops) (filtre Épique E7 → E10) — plus une vue
**« V0 »** (filtre label `V0`) et une vue **« Bénévoles »** (filtre `good first issue`).

Statuts actuels : les issues GitHub fermées sont en *Done* ; ce qui est livré sur
`feature/setup-front` sans être fusionné (#13, #14, #15, #16, #26) est en *In Review* ; les issues
ouvertes et assignées (#6, #21, #22, #23) sont en *In Progress*.

**Prêt** (*Definition of Ready*) : description, critères d'acceptation, maquette liée si
interface, taille estimée. **Fait** (*Definition of Done*) : PR fusionnée, CI verte, doc mise à
jour, captures avant / après pour un changement visuel.

## 6. Commandes

Le token `gh` doit pouvoir lire et écrire les projets :

```bash
gh auth refresh -s read:project,project
```

### Labels et jalons

```bash
REPO=dataforgoodfr/democracy-watch
for l in type:feat type:fix type:docs type:chore domaine:front domaine:api domaine:data \
         domaine:design domaine:ops domaine:produit taille:S taille:M taille:L V0; do
  gh label create "$l" --repo $REPO --force
done
gh api repos/$REPO/milestones -f title="V0 — 7 nov. 2026" -f due_on="2026-11-07T00:00:00Z"
gh api repos/$REPO/milestones -f title="Après V0"
```

### Remettre de l'ordre dans l'existant

```bash
# #26 sous #8 (l'API de sous-issues attend l'identifiant interne, pas le numéro)
ID=$(gh api repos/$REPO/issues/26 --jq .id)
gh api repos/$REPO/issues/8/sub_issues -F sub_issue_id=$ID

# #5 devient le chapeau Design
gh issue edit 5 --repo $REPO --title "Design" --add-label domaine:design
```

### Créer une issue de la roadmap comme sous-issue

```bash
# Exemple : DW-18 sous #15 (Section « Articles »)
URL=$(gh issue create --repo $REPO \
  --title "DW-18 — Kanban : filtres Type, Groupe et Tri (maquette V0·5)" \
  --label type:feat --label domaine:front --label taille:M --label V0 \
  --milestone "V0 — 7 nov. 2026" \
  --body "Voir la roadmap (docs › Roadmap). Maquette : V0 · 5. Critères : filtres reflétés dans l'URL, testés (Vitest + e2e).")
ID=$(gh api "repos/$REPO/issues/${URL##*/}" --jq .id)
gh api repos/$REPO/issues/15/sub_issues -F sub_issue_id=$ID
```

### Ajouter les issues au Project

```bash
gh project item-add <numéro-du-projet> --owner dataforgoodfr --url "$URL"
```

## 7. Pull request du socle

Texte proposé pour `feature/setup-front` → `main` :

```markdown
## Ce qui change

Socle du front, de la documentation et de l'API :
- monorepo pnpm : packages theme, brand, data, api, state, ui, screens ; Next.js ne fait que du routage
- parcours V0 (données fictives) : connexion, sélection et suivi de textes, kanban d'un article
- API FastAPI selon la RFC (#26) : recherche Meilisearch, dossiers, articles, amendements, santé
- documentation Zudoku, roadmap « cycle de vie d'un amendement »

Refs #12 #13 #14 #15 #16 #26

## Comment tester

pnpm install && pnpm dev        # http://localhost:3000, n'importe quel e-mail pour se connecter
pnpm dev:docs                   # http://localhost:3002
pnpm test && pnpm build && pnpm test:e2e
cd server && uv sync && uv run pytest
```

## 8. Rythme proposé

Compatible avec la [RFC méthode de travail](/produit/methode-de-travail) (Shape Up) :

| Quand | Quoi | Qui |
| --- | --- | --- |
| Début de cycle | choisir les issues du cycle dans le Project (vue « V0 ») | produit + tech leads |
| Chaque semaine | 30 min : ce qui est en Revue, ce qui bloque, réaffectation | équipe |
| Fin de cycle | démo sur la préproduction, mise à jour de la roadmap | équipe |
