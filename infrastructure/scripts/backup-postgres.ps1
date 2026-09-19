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
$databaseUrl = $env:AEVRA_DATABASE_URL -replace '^postgresql\+psycopg://', 'postgresql://'
& pg_dump --format=custom --no-owner --file=$target $databaseUrl
if ($LASTEXITCODE -ne 0) {
  Remove-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue
  throw "pg_dump failed with exit code $LASTEXITCODE. No usable backup was created."
}
Write-Output "Backup written to $target"
