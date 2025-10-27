#!/bin/bash

set -euo pipefail

BUILD_FLAG=""
if [[ "${1-}" == "--build" || "${1-}" == "-b" ]]; then
  BUILD_FLAG="--build"
  shift
fi

dotenvx run -- docker compose up ${BUILD_FLAG} -d "$@"