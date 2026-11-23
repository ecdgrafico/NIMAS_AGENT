[CmdletBinding()]
param(
    [string]$ProjectRoot = '',
    [int]$Port = 8000,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $RepoRoot 'config\project.local.json'
$Venv = Join-Path $RepoRoot '.venv'
$VenvPython = Join-Path $Venv 'Scripts\python.exe'

function Test-NimasProject([string]$Path) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Container)) { return $false }
    $markers = @('lecciones_originales', 'PDF', '9781669952961NIMAS', '9781669952961NIMAS_original')
    return (@($markers | Where-Object { -not (Test-Path -LiteralPath (Join-Path $Path $_)) }).Count -eq 0)
}

function Get-BasePython {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return @{ File = $py.Source; Args = @('-3') } }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return @{ File = $python.Source; Args = @() } }
    throw 'No se encontró Python 3. Instálalo desde https://www.python.org/downloads/windows/ y vuelve a ejecutar NIMASAPP.'
}

if (-not $ProjectRoot -and (Test-Path -LiteralPath $ConfigPath)) {
    try { $ProjectRoot = (Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json).projectRoot } catch {}
}
if (-not (Test-NimasProject $ProjectRoot)) {
    Write-Host ''
    Write-Host 'Indica la carpeta del proyecto editorial PHE27_NIMAS.' -ForegroundColor Yellow
    Write-Host 'Debe contener: PDF, lecciones_originales, 9781669952961NIMAS y 9781669952961NIMAS_original.' -ForegroundColor DarkYellow
    $ProjectRoot = Read-Host 'Ruta completa del proyecto'
}
if (-not (Test-NimasProject $ProjectRoot)) {
    throw 'La ruta no contiene un proyecto NIMAS preparado. No se inició la auditoría.'
}
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path

# Se guarda sólo una ruta local; config/project.local.json está ignorado por Git.
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ConfigPath) | Out-Null
@{ projectRoot = $ProjectRoot } | ConvertTo-Json | Set-Content -LiteralPath $ConfigPath -Encoding UTF8

if (-not (Test-Path -LiteralPath $VenvPython)) {
    $base = Get-BasePython
    Write-Host 'Creando entorno Python local…' -ForegroundColor Cyan
    & $base.File @($base.Args) -m venv $Venv
}

Write-Host 'Comprobando e instalando dependencias Python…' -ForegroundColor Cyan
& $VenvPython -m pip install --disable-pip-version-check -q -r (Join-Path $RepoRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias de Python.' }

if (-not (Get-Command pdftoppm -ErrorAction SilentlyContinue)) {
    Write-Warning 'No se encontró pdftoppm (Poppler). La app iniciará, pero para ver páginas PDF instala Poppler y reinicia NIMASAPP.'
    Write-Host 'Instalación sugerida: winget search poppler  (elige una distribución y añádela a PATH).' -ForegroundColor DarkYellow
}

$env:NIMAS_PROJECT_ROOT = $ProjectRoot
$Url = "http://127.0.0.1:$Port/auditoria-lecciones/"
Write-Host ''
Write-Host "NIMASAPP iniciará en $Url" -ForegroundColor Green
Write-Host "Proyecto editorial: $ProjectRoot" -ForegroundColor DarkGreen
Write-Host 'Para detenerlo, presiona Ctrl+C en esta terminal.' -ForegroundColor DarkGray
if (-not $NoBrowser) { Start-Process $Url }

& $VenvPython (Join-Path $RepoRoot 'nimas-agent\servidor_auditoria.py')
exit $LASTEXITCODE
