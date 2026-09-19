#!/usr/bin/env sh
set -eu
: "${AEVRA_DATABASE_URL:?Set AEVRA_DATABASE_URL before running a backup}"
output_dir="${1:-./backups}"
mkdir -p "$output_dir"
stamp="$(date -u +%Y%m%d-%H%M%S)"
target="$output_dir/aevra-$stamp.dump"
database_url="$(printf '%s' "$AEVRA_DATABASE_URL" | sed 's#^postgresql+psycopg://#postgresql://#')"
if ! pg_dump --format=custom --no-owner --file="$target" "$database_url"; then
  rm -f "$target"
  printf 'pg_dump failed. No usable backup was created.\n' >&2
  exit 1
fi
printf 'Backup written to %s\n' "$target"
