param(
  [Parameter(Mandatory = $true)][string]$BackupFile,
  [Parameter(Mandatory = $true)][string]$RestoreDatabaseUrl
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $BackupFile -PathType Leaf)) {
  throw "Backup file not found: $BackupFile"
}
Write-Output "Restoring $BackupFile into the explicitly supplied restore database."
pg_restore --exit-on-error --single-transaction --no-owner --dbname=$RestoreDatabaseUrl $BackupFile
Write-Output "Restore completed. Run the API smoke checks against the restore database before promoting it."
