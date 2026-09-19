param(
  [Parameter(Mandatory = $true)][string]$BackupFile,
  [Parameter(Mandatory = $true)][string]$RestoreDatabaseUrl
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $BackupFile -PathType Leaf)) {
  throw "Backup file not found: $BackupFile"
}
Write-Output "Restoring $BackupFile into the explicitly supplied restore database."
$databaseUrl = $RestoreDatabaseUrl -replace '^postgresql\+psycopg://', 'postgresql://'
& pg_restore --exit-on-error --single-transaction --no-owner --dbname=$databaseUrl $BackupFile
if ($LASTEXITCODE -ne 0) {
  throw "pg_restore failed with exit code $LASTEXITCODE. The restore database must not be promoted."
}
Write-Output "Restore completed. Run the API smoke checks against the restore database before promoting it."
