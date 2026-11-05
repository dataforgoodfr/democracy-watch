#!/usr/bin/env bash
# Vérifie que des ports TCP locaux sont libres avant de démarrer un service.
# Usage : check_ports.sh [--ignore-project NOM] PORT...
# Port occupé : propose d'arrêter le conteneur Docker ou le processus qui l'écoute.
# Les conteneurs du projet Compose ignoré sont laissés à `docker compose up`.
# Sans terminal interactif, rien n'est arrêté et le script échoue.
set -euo pipefail

DOCKER=${DOCKER:-docker}
ignored_project=""
if [[ ${1:-} == --ignore-project ]]; then
    ignored_project=$2
    shift 2
fi

# Pose une question oui/non ; refuse par défaut et hors terminal.
ask() {
    [[ -t 0 ]] || return 1
    local answer
    read -r -p "$1 [o/N] " answer
    [[ $answer == [oOyY]* ]]
}

listeners() {
    lsof -nP -t -iTCP:"$1" -sTCP:LISTEN 2>/dev/null | sort -u || true
}

# Attend jusqu'à 5 s que le port se libère.
wait_free() {
    for _ in {1..10}; do
        [[ -z $(listeners "$1") ]] && return 0
        sleep 0.5
    done
    return 1
}

command -v lsof >/dev/null || { echo "lsof absent : vérification des ports ignorée." >&2; exit 0; }

for port in "$@"; do
    pids=$(listeners "$port")
    [[ -z $pids ]] && continue

    container="" project=""
    if command -v "$DOCKER" >/dev/null; then
        read -r container project < <(
            "$DOCKER" ps --filter "publish=$port" \
                --format '{{.Names}} {{.Label "com.docker.compose.project"}}' 2>/dev/null | head -n 1
        ) || true
    fi

    if [[ -n $container ]]; then
        [[ -n $ignored_project && $project == "$ignored_project" ]] && continue
        echo "Port $port occupé par le conteneur Docker $container."
        if ask "Arrêter le conteneur $container ?"; then
            "$DOCKER" stop "$container" >/dev/null
            wait_free "$port" && continue
        fi
    else
        echo "Port $port occupé par :"
        ps -o pid=,command= -p "$(paste -sd, - <<<"$pids")" || true
        if ask "Arrêter ce(s) processus ?"; then
            # shellcheck disable=SC2086  # un PID par mot
            kill $pids
            wait_free "$port" && continue
        fi
    fi
    echo "Port $port toujours occupé : abandon." >&2
    exit 1
done
