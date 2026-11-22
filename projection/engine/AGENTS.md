# AGENTS.md - `projection/engine`

Complète le `AGENTS.md` racine. Le moteur projette les amendements sur le texte qu'ils modifient.

## Architecture : hexagonale légère

Un cœur pur au centre, des adaptateurs aux bords, et une seule règle : **les dépendances vont
vers le cœur**. Pas de ports formels (`Protocol`/ABC) : les types du `domain` jouent ce rôle.

| Couche      | Rôle                                                                                  | Peut importer                  |
| ----------- | ------------------------------------------------------------------------------------- | ------------------------------ |
| `domain/`   | Types et règles métier (`Patch`, `Operation`, `Target`, `Amendment`…). Pur, sans I/O. | stdlib                         |
| `actions/`  | Opérations enfichables : chacune se traduit en `Patch` (`Operation.plan`).            | `domain`                       |
| `reading/`  | Texte d'un dispositif → opérations (grammaires Lark). Seul `read` est public.         | `domain`, `actions`, `lark`    |
| `usecases/` | Orchestration pure : `project` (un amendement), `consolidate` (une étape).            | `domain`, `actions`, `reading` |
| `adapters/` | Bords : source de données → types du moteur, rendu (graphe).                          | tout le moteur                 |

Interdits (vérifiés par `tests/test_architecture.py`) :

- `domain`, `actions` : ni `lark`, ni `datasources`, ni `usecases`/`reading` (selon la couche).
- `reading`, `usecases` : ni `datasources`, ni `adapters` ; `usecases` : pas `lark`.
- Personne en dehors de `adapters/` ne connaît une source (Tricoteuses…) ni ses champs.

## Règles

- **Cœur pur** : mêmes entrées, même sortie, aucun I/O (réseau, base, fichier, horloge).
- **Entrées** : un adaptateur construit les types de `domain/documents.py` ; le moteur ne lit
  jamais les champs bruts d'une source. Les imports de `datasources` restent sous
  `TYPE_CHECKING`.
- **Nouvelle opération** : une classe dans `actions/` + la règle de grammaire dans `reading/`.
- **Un patch n'a de sens que contre sa base** : pour changer de base, on réévalue l'opération,
  on ne décale jamais des positions.
- **Exact ou absent** : une instruction refusée ou en conflit refuse tout l'amendement
  (`Refusal`/`Reason`), jamais de résultat approximatif.
- **Statut** : `Status` se déduit de `Reason` (`status_of`), ou est imposé par `consolidate`
  (`Projection.forced`) ; il ne remplace jamais `Reason`.
- **Nouvelle couche ou nouvel import interdit** : mettre à jour `FORBIDDEN` dans
  `tests/test_architecture.py` dans le même diff.
- Tests dans `tests/`, un fichier par module ; le test d'architecture doit toujours passer.
