source /Volumes/repos/DFG/democracy-watch/.env
# À exécuter depuis la racine du dépôt, sans afficher les identifiants de connexion.
uv run --active sqlacodegen --generator declarative "$DATABASE_URL" --outfile backend/schemas/database_mapping.py
echo "database_mapping OK"
uv run --active sqlacodegen --generator dataclasses $DATABASE_URL >> dataclasses.py
echo "dataclasses OK"
uv run --active sqlacodegen --generator sqlmodels   $DATABASE_URL >> sqlmodels.py
echo "sqlmodels OK"
uv run --active sqlacodegen --generator tables      $DATABASE_URL >> tables.py
echo "tables OK"

uv run --active sqlacodegen $DATABASE_URL >> models.py
