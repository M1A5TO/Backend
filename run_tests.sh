#!/usr/bin/env bash
set -euo pipefail

docker compose up -d --build

pytest tests/test_api.py