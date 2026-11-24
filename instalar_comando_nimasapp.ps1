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
$LegacyProfile = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'WindowsPowerShell\profile.ps1'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LegacyProfile) | Out-Null
if (-not (Test-Path -LiteralPath $LegacyProfile)) { New-Item -ItemType File -Force -Path $LegacyProfile | Out-Null }
$legacyContent = Get-Content -Raw -LiteralPath $LegacyProfile
if ($legacyContent -notmatch [regex]::Escape($line)) { Add-Content -LiteralPath $LegacyProfile -Value "`n# NIMAS Agent launcher`n$line" }
$ModernProfile = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'PowerShell\profile.ps1'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ModernProfile) | Out-Null
if (-not (Test-Path -LiteralPath $ModernProfile)) { New-Item -ItemType File -Force -Path $ModernProfile | Out-Null }
$modernContent = Get-Content -Raw -LiteralPath $ModernProfile
if ($modernContent -notmatch [regex]::Escape($line)) { Add-Content -LiteralPath $ModernProfile -Value "`n# NIMAS Agent launcher`n$line" }
Write-Host 'Comando instalado. Cierra y vuelve a abrir la terminal; luego escribe: NIMASAPP' -ForegroundColor Green
