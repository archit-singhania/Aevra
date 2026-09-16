#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/aevra
mkdir -p "$APP_DIR"
cd "$APP_DIR"

if [ ! -f .env.staging ]; then
  echo "Create $APP_DIR/.env.staging before starting the stack" >&2
  exit 1
fi

docker compose --env-file .env.staging -f infrastructure/gcp/staging-compose.yml up -d --build
