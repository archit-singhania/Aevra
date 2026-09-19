#!/bin/sh
set -eu

alembic upgrade head
python -m aevra_api.seed
exec uvicorn aevra_api.main:app --host 0.0.0.0 --port "${PORT:-10000}"
