#!/usr/bin/env bash

set -eu -o pipefail

. ./venv/bin/activate

[[ -d "./dist" ]] && rm -rf "./dist"

python3 -m pip install --upgrade setuptools wheel twine

python3 setup.py sdist bdist_wheel

python3 -m twine upload --repository testpypi dist/*
