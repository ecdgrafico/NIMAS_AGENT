param([switch]$RequireClean)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Push-Location $repo
try {
    Write-Host '[1/4] Vue production build'
    Push-Location (Join-Path $repo 'frontend-vue')
    npm run build
    Pop-Location

    Write-Host '[2/4] Python test suite'
    & (Join-Path $repo '.venv\Scripts\python.exe') -m unittest discover -s tests

    Write-Host '[3/4] Python syntax check'
    & (Join-Path $repo '.venv\Scripts\python.exe') -m py_compile nimas-agent/servidor_auditoria.py

    Write-Host '[4/4] Git working tree'
    git diff --check
    if ($RequireClean -and (git status --porcelain)) { throw 'El árbol de trabajo contiene cambios no revisados.' }
    Write-Host 'SMOKE TEST PASSED'
} finally {
    Pop-Location -ErrorAction SilentlyContinue
}
