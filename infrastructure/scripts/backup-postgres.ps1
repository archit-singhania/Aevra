param(
  [string]$OutputDirectory = "./backups"
)

$ErrorActionPreference = "Stop"
if (-not $env:AEVRA_DATABASE_URL) {
  throw "Set AEVRA_DATABASE_URL to the production PostgreSQL URL before running a backup."
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$target = Join-Path $OutputDirectory "aevra-$stamp.dump"
pg_dump --format=custom --no-owner --file=$target $env:AEVRA_DATABASE_URL
Write-Output "Backup written to $target"
