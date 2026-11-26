#!/usr/bin/env bash
# Prépare le contrat OpenAPI et choisit les exemples avant un import Microcks.
# Usage : prepare_contract.sh RACINE_DU_DEPOT
# Affiche l'âge de build/openapi.json et propose de le régénérer, puis demande s'il faut
# importer les exemples synthétiques seuls ou l'extrait de la DB (build/microcks).
# Écrit le choix sur la sortie standard : « synthetic » ou « db » ; le reste va sur stderr.
# Sans terminal interactif : contrat régénéré, extrait DB utilisé s'il existe déjà.
set -euo pipefail

root=${1:?Usage : prepare_contract.sh RACINE_DU_DEPOT}
contract="$root/build/openapi.json"
samples_dir="$root/build/microcks"

# Pose une question ; renvoie la réponse, ou la valeur par défaut hors terminal.
ask() {
    local answer=""
    if [[ -t 0 ]]; then
        read -r -p "$1 " answer >&2
    fi
    printf '%s' "${answer:-$2}"
}

# Âge lisible d'un fichier, d'après sa date de modification (stat GNU ou BSD).
age() {
    local mtime seconds
    mtime=$(stat -c %Y "$1" 2>/dev/null || stat -f %m "$1")
    seconds=$(($(date +%s) - mtime))
    if ((seconds < 3600)); then
        printf '%d min' $((seconds / 60))
    elif ((seconds < 86400)); then
        printf '%d h' $((seconds / 3600))
    else
        printf '%d j' $((seconds / 86400))
    fi
}

if [[ ! -e $contract ]]; then
    echo "Contrat absent : génération de $contract" >&2
    make -C "$root" openapi >&2
else
    notice=""
    if [[ -n $(find "$root/backend/api/app" -name '*.py' -newer "$contract" -print -quit) ]]; then
        notice=" ; code de l'API modifié depuis"
    fi
    echo "Contrat existant : $contract (généré il y a $(age "$contract")$notice)" >&2
    if [[ $(ask "Régénérer le contrat ? [O/n]" o) == [oOyY]* ]]; then
        make -C "$root" openapi >&2
    fi
fi

shopt -s nullglob
samples=("$samples_dir"/examples-*.yaml)
if ((${#samples[@]})); then
    echo "Extrait DB existant : ${#samples[@]} fichiers dans $samples_dir" \
        "(extrait il y a $(age "${samples[0]}"))" >&2
    choice=$(ask "Exemples : [s]ynthétiques seuls, [e]xtrait DB existant, [r]éextraire depuis la DB ? [s/E/r]" e)
else
    echo "Aucun extrait DB dans $samples_dir" >&2
    choice=$(ask "Exemples : [s]ynthétiques seuls, [r]extraire depuis la DB ? [S/r]" s)
fi

if [[ $choice == [rR]* ]]; then
    make -C "$root" microcks-samples >&2
    choice=e
fi

case $choice in
    [eE]*)
        echo "Import : contrat + extrait DB de $samples_dir" >&2
        echo db
        ;;
    *)
        echo "Import : contrat seul, exemples synthétiques" >&2
        echo synthetic
        ;;
esac
