#!/usr/bin/env bash
# Publish forge-next to PyPI. Requires: pip install build twine
# Auth: TWINE_USERNAME=__token__ TWINE_PASSWORD=<pypi_api_token>
set -euo pipefail
cd "$(dirname "$0")/../.."
rm -rf dist
python -m build
python -m twine check dist/*
python -m twine upload dist/*
