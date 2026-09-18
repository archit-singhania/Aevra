#!/usr/bin/env sh
set -eu
backup_file="${1:?Usage: restore-postgres.sh BACKUP_FILE RESTORE_DATABASE_URL}"
restore_database_url="${2:?Usage: restore-postgres.sh BACKUP_FILE RESTORE_DATABASE_URL}"
test -f "$backup_file"
pg_restore --exit-on-error --single-transaction --no-owner --dbname="$restore_database_url" "$backup_file"
printf 'Restore completed. Run API smoke checks against the restore database before promoting it.\n'
