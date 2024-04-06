#!/usr/bin/env bash
set -euxo pipefail

poetry run python src/weather_ingest.py
poetry run python src/generate_image.py