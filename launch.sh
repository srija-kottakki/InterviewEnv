#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec uvicorn server.app:app --host 0.0.0.0 --port "${PORT:-7860}"
