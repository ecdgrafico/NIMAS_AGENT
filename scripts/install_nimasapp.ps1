[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Bin = Join-Path $env:LOCALAPPDATA 'NIMASAPP-bin'
New-Item -ItemType Directory -Path $Bin -Force | Out-Null
$Shim = Join-Path $Bin 'NIMASAPP.cmd'
$content = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$RepoRoot\scripts\NIMASAPP.ps1`" %*`r`n"
[System.IO.File]::WriteAllText($Shim, $content, [System.Text.Encoding]::ASCII)
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$parts = @($userPath -split ';' | Where-Object { $_ -and $_.Trim() })
if ($parts -notcontains $Bin) {
    [Environment]::SetEnvironmentVariable('Path', (($parts + $Bin) -join ';'), 'User')
    Write-Host "NIMASAPP instalado en el PATH del usuario: $Bin"
} else {
    Write-Host "NIMASAPP ya estaba instalado: $Bin"
}
Write-Host 'Cierra y abre una nueva terminal; despues podras ejecutar: NIMASAPP'
