[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$Book,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    throw "No se encontró el entorno Python en $Python. Ejecute: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}
$Runner = Join-Path $Root 'nimas-agent\run_book_batch.py'
if (-not (Test-Path -LiteralPath $Runner)) { throw "No se encontró el ejecutor: $Runner" }
& $Python $Runner --root $Root --book $Book $(if ($Force) { '--force' })
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
