#!/usr/bin/env bash
# Propose d'arrêter un serveur une fois démarré.
# Usage : offer_stop.sh --run COMMANDE...  lance COMMANDE (serveur au premier plan) ;
#           réponse oui : l'arrête ; sinon : reste attaché jusqu'à Ctrl+C.
#         offer_stop.sh COMMANDE...        serveur déjà détaché ; réponse oui : lance COMMANDE.
# Sans terminal interactif, rien n'est demandé ni arrêté.
set -euo pipefail

# Pose une question oui/non ; refuse par défaut et hors terminal.
ask() {
    [[ -t 0 ]] || return 1
    local answer
    read -r -p "$1 [o/N] " answer
    [[ $answer == [oOyY]* ]]
}

if [[ ${1:-} == --run ]]; then
    shift
    [[ -t 0 ]] || exec "$@"
    # Hors contrôle de tâches, le serveur en arrière-plan lit /dev/null : la réponse reste ici.
    "$@" &
    pid=$!
    trap 'kill "$pid" 2>/dev/null || true' EXIT
    ask "Arrêter le serveur ?" && exit 0
    wait "$pid"
elif ask "Arrêter les conteneurs démarrés ?"; then
    "$@"
fi
