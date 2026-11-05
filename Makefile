ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
COMPOSE ?= docker-compose
COMPOSE_CMD = $(COMPOSE) --env-file "$(ROOT_DIR)/.env" -f "$(ROOT_DIR)/backend/api/docker-compose.yml"
API_URL ?= http://127.0.0.1:8000
MICROCKS_URL ?= http://127.0.0.1:8081
CHECK_PORTS = "$(ROOT_DIR)/backend/api/scripts/check_ports.sh"
OFFER_STOP = "$(ROOT_DIR)/backend/api/scripts/offer_stop.sh"
# Projet Compose par défaut : nom du dossier du fichier Compose.
COMPOSE_PROJECT ?= api

.DEFAULT_GOAL := help
.PHONY: help install dev test docker-up docker-down docker-logs docker-check microcks-up openapi microcks-samples microcks-import health

help:
	@printf '%s\n' \
	  'install          Installer les dépendances avec uv' \
	  'dev              Démarrer FastAPI localement avec rechargement' \
	  'test             Lancer pytest sans services partagés' \
	  'docker-up        Construire et démarrer API + Microcks' \
	  'docker-down      Arrêter les conteneurs sans supprimer les volumes' \
	  'docker-logs      Suivre les journaux API + Microcks' \
	  'docker-check     Valider Compose sans afficher les secrets' \
	  'microcks-up      Démarrer uniquement Microcks, sans accès DB' \
	  'openapi          Exporter le contrat avec exemples synthétiques' \
	  'microcks-samples Extraire des exemples réels de la DB vers build/microcks (lecture seule)' \
	  'microcks-import  Importer ce contrat (et build/microcks s'"'"'il existe) dans Microcks' \
	  'health           Vérifier la vivacité de la vraie API'

install:
	uv --directory "$(ROOT_DIR)" sync

dev:
	@$(CHECK_PORTS) 8000
	$(OFFER_STOP) --run uv --directory "$(ROOT_DIR)" run uvicorn backend.api.app.main:app --reload

test:
	uv --directory "$(ROOT_DIR)" run pytest

docker-up:
	@$(CHECK_PORTS) --ignore-project $(COMPOSE_PROJECT) 8000 8081
	$(COMPOSE_CMD) up --build -d --wait api microcks
	@$(OFFER_STOP) $(COMPOSE_CMD) stop api microcks

docker-down:
	$(COMPOSE_CMD) down

docker-logs:
	$(COMPOSE_CMD) logs -f api microcks

docker-check:
	$(COMPOSE_CMD) config --quiet

microcks-up:
	@$(CHECK_PORTS) --ignore-project $(COMPOSE_PROJECT) 8081
	$(COMPOSE_CMD) up -d --wait microcks
	@$(OFFER_STOP) $(COMPOSE_CMD) stop microcks

openapi:
	@mkdir -p "$(ROOT_DIR)/build"
	uv --directory "$(ROOT_DIR)" run python -m backend.api.scripts.export_openapi > "$(ROOT_DIR)/build/openapi.json"

microcks-samples:
	@mkdir -p "$(ROOT_DIR)/build"
	set -a && . "$(ROOT_DIR)/.env" && set +a && \
	  uv --directory "$(ROOT_DIR)" run python -m backend.api.scripts.export_microcks_samples "$(ROOT_DIR)/build/microcks"

microcks-import: openapi
	curl --fail --show-error --silent --retry 10 --retry-delay 2 --retry-connrefused \
	  --connect-timeout 3 --max-time 15 \
	  --form 'file=@$(ROOT_DIR)/build/openapi.json;type=application/json' \
	  '$(MICROCKS_URL)/api/artifact/upload?mainArtifact=true'
	@for file in "$(ROOT_DIR)"/build/microcks/examples-*.yaml; do \
	  [ -e "$$file" ] || continue; \
	  printf '\n%s : ' "$$file"; \
	  curl --fail --show-error --silent --max-time 300 \
	    --form "file=@$$file;type=application/x-yaml" \
	    '$(MICROCKS_URL)/api/artifact/upload?mainArtifact=false' || exit 1; \
	done
	@printf '\nMicrocks : $(MICROCKS_URL)\n'

health:
	curl --fail --show-error --silent --max-time 5 '$(API_URL)/health'
	@printf '\n'
