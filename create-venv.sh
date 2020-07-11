#!/usr/bin/env bash

################################################################
#
# creates virtual env for python, requires python 3 in the path
#
################################################################

set -eu -o pipefail

errx() {
    echo "ERROR: ${1:-"No info"}"
    exit ${2:-32}
}

which python3 || errx "No python found in PATH!"

venv_path="./venv"

if [[ -d "${venv_path}" ]] ; then
    echo "Existing vnev folder found - cleaning up..."
    rm -rf "${venv_path}"
    echo "Done."
fi  

python3 -m venv "${venv_path}"

echo "Activating the venv"
. ./venv/bin/activate

