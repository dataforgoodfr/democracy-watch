ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
COMPOSE ?= docker-compose
COMPOSE_CMD = $(COMPOSE) --env-file "$(ROOT_DIR)/.env" -f "$(ROOT_DIR)/backend/api/docker-compose.yml"
# Projet Compose par défaut : nom du dossier du fichier Compose.
COMPOSE_PROJECT ?= api
# Services démarrés par docker-up : l'API joint Meilisearch sur http://meilisearch:7700.
SERVICES = api meilisearch microcks
API_URL ?= http://127.0.0.1:8000
MICROCKS_URL ?= http://127.0.0.1:8081
UV = uv --directory "$(ROOT_DIR)"
# uv lit le .env (variables $PGUSER… résolues) et échoue s'il est absent.
UV_ENV = $(UV) run --env-file "$(ROOT_DIR)/.env"
SCRIPTS = $(ROOT_DIR)/backend/api/scripts
CHECK_PORTS = "$(SCRIPTS)/check_ports.sh"
OFFER_STOP = "$(SCRIPTS)/offer_stop.sh"
PREPARE_CONTRACT = "$(SCRIPTS)/prepare_contract.sh"

.DEFAULT_GOAL := help
.PHONY: help install check-connections dev health test lint check \
	docker-up docker-down docker-logs docker-check \
	microcks-up openapi microcks-samples microcks-import

# Aide générée depuis les commentaires « ## » des cibles et les titres « ##@ ».
help: ## Afficher cette aide
	@awk 'BEGIN { FS = ":.*## " } \
	  /^##@ / { printf "\n%s\n", substr($$0, 5) } \
	  /^[a-z-]+:.*## / { printf "  %-18s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@printf '\nDétails : LOCAL_DEV.md\n'

##@ Premiers pas
install: ## Installer Python, le venv et les dépendances (uv sync)
	$(UV) sync

check-connections: ## Vérifier l'accès à Postgres et Meilisearch du .env (lecture seule)
	$(UV_ENV) python -m backend.api.scripts.check_connections

##@ API en local (hors Docker)
dev: ## Démarrer l'API sur le port 8000 avec rechargement automatique
	@$(CHECK_PORTS) 8000
	$(OFFER_STOP) --run $(UV_ENV) uvicorn backend.api.app.main:app --reload

health: ## Vérifier que l'API répond (API_URL, 8000 par défaut)
	curl --fail --show-error --silent --max-time 5 '$(API_URL)/health'
	@printf '\n'

##@ Qualité
test: ## Lancer pytest (sans base ni Meilisearch)
	$(UV) run pytest

lint: ## Lancer les hooks pre-commit sur tout le dépôt (ruff, ty, secrets…)
	$(UV) run prek run --all-files

check: lint test ## Tout vérifier avant une PR : lint puis tests

##@ Docker (API + Meilisearch + Microcks)
docker-up: ## Construire et démarrer les conteneurs
	@$(CHECK_PORTS) --ignore-project $(COMPOSE_PROJECT) 8000 7700 8081
	$(COMPOSE_CMD) up --build -d --wait $(SERVICES)
	@$(OFFER_STOP) $(COMPOSE_CMD) stop $(SERVICES)

docker-down: ## Arrêter les conteneurs sans supprimer les volumes
	$(COMPOSE_CMD) down

docker-logs: ## Suivre les journaux des conteneurs
	$(COMPOSE_CMD) logs -f $(SERVICES)

docker-check: ## Valider la configuration Compose sans afficher les secrets
	$(COMPOSE_CMD) config --quiet

##@ Microcks (API simulée)
microcks-up: ## Démarrer Microcks seul, sans accès DB
	@$(CHECK_PORTS) --ignore-project $(COMPOSE_PROJECT) 8081
	$(COMPOSE_CMD) up -d --wait microcks
	@$(OFFER_STOP) $(COMPOSE_CMD) stop microcks

openapi: ## Générer build/openapi.json (exemples synthétiques)
	@mkdir -p "$(ROOT_DIR)/build"
	$(UV) run python -m backend.api.scripts.export_openapi > "$(ROOT_DIR)/build/openapi.json"

microcks-samples: ## Extraire de vrais exemples de la DB vers build/microcks (lecture seule)
	@mkdir -p "$(ROOT_DIR)/build"
	$(UV_ENV) python -m backend.api.scripts.export_microcks_samples "$(ROOT_DIR)/build/microcks"

microcks-import: ## Importer le contrat et les exemples choisis (demande avant de régénérer)
	@examples=$$($(PREPARE_CONTRACT) "$(ROOT_DIR)") && \
	  curl --fail --show-error --silent --retry 10 --retry-delay 2 --retry-connrefused \
	  --connect-timeout 3 --max-time 15 \
	  --form 'file=@$(ROOT_DIR)/build/openapi.json;type=application/json' \
	  '$(MICROCKS_URL)/api/artifact/upload?mainArtifact=true' && \
	  if [ "$$examples" = db ]; then \
	    for file in "$(ROOT_DIR)"/build/microcks/examples-*.yaml; do \
	      [ -e "$$file" ] || continue; \
	      printf '\n%s : ' "$$file"; \
	      curl --fail --show-error --silent --max-time 300 \
	        --form "file=@$$file;type=application/x-yaml" \
	        '$(MICROCKS_URL)/api/artifact/upload?mainArtifact=false' || exit 1; \
	    done; \
	  fi
	@printf '\nMicrocks : $(MICROCKS_URL)\n'
