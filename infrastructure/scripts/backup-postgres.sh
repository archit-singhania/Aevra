#!/usr/bin/env sh
set -eu
: "${AEVRA_DATABASE_URL:?Set AEVRA_DATABASE_URL before running a backup}"
output_dir="${1:-./backups}"
mkdir -p "$output_dir"
stamp="$(date -u +%Y%m%d-%H%M%S)"
target="$output_dir/aevra-$stamp.dump"
pg_dump --format=custom --no-owner --file="$target" "$AEVRA_DATABASE_URL"
printf 'Backup written to %s\n' "$target"
