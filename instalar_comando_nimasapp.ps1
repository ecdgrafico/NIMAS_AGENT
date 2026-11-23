[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$Launcher = Join-Path $RepoRoot 'scripts\NIMASAPP.ps1'
$ProfileDir = Split-Path -Parent $PROFILE.CurrentUserAllHosts
New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null
if (-not (Test-Path -LiteralPath $PROFILE.CurrentUserAllHosts)) {
    New-Item -ItemType File -Force -Path $PROFILE.CurrentUserAllHosts | Out-Null
}

$escaped = $Launcher.Replace("'", "''")
$line = "function global:NIMASAPP { & '$escaped' @args }"
$content = Get-Content -Raw -LiteralPath $PROFILE.CurrentUserAllHosts
if ($content -notmatch [regex]::Escape($line)) {
    Add-Content -LiteralPath $PROFILE.CurrentUserAllHosts -Value "`n# NIMAS Agent launcher`n$line"
}
Write-Host 'Comando instalado. Cierra y vuelve a abrir la terminal; luego escribe: NIMASAPP' -ForegroundColor Green
