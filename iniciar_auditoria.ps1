param(
  [string]$ProjectRoot = $PSScriptRoot,
  [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw 'Se requiere Python 3.10 o superior. Instálalo y vuelve a ejecutar este archivo.'
}
if (-not (Get-Command pdftoppm -ErrorAction SilentlyContinue)) {
  throw 'Se requiere Poppler (pdftoppm) para mostrar PDFs por página. Instálalo y añádelo a PATH.'
}

$env:NIMAS_PROJECT_ROOT = $ProjectRoot
python nimas-agent/servidor_auditoria.py
