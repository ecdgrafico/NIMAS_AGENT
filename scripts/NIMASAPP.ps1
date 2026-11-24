[CmdletBinding()]
param(
    [string]$ProjectRoot = '',
    [int]$Port = 8000,
    [switch]$NoBrowser,
    [switch]$Watch,
    [switch]$DetailedLogs
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
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

if ($ProjectRoot) {
    if (-not (Test-NimasProject $ProjectRoot)) {
        throw 'La ruta indicada no contiene un proyecto NIMAS preparado. No se inició la auditoría.'
    }
    $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
} else {
    # No se carga PHE27 ni una ruta usada anteriormente. Sin un proyecto
    # explícito, la app abre su landing vacía para importar uno nuevo.
    $ProjectRoot = $RepoRoot
}

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
$env:NIMAS_VERBOSE = if ($DetailedLogs) { '1' } else { '0' }
$Url = "http://127.0.0.1:$Port/auditoria-lecciones/"
Write-Host ''
Write-Host "NIMASAPP iniciará en $Url" -ForegroundColor Green
if ($ProjectRoot -eq $RepoRoot) {
    Write-Host 'No hay proyecto editorial cargado. Usa la landing para importar un ZIP nuevo.' -ForegroundColor DarkYellow
} else {
    Write-Host "Proyecto editorial explícito: $ProjectRoot" -ForegroundColor DarkGreen
}
Write-Host 'Para detenerlo, presiona Ctrl+C en esta terminal.' -ForegroundColor DarkGray
if (-not $NoBrowser) { Start-Process $Url }

$ServerScript = Join-Path $RepoRoot 'nimas-agent\servidor_auditoria.py'
if (-not $Watch) {
    & $VenvPython $ServerScript
    exit $LASTEXITCODE
}

Write-Host 'Modo Watch activo: los cambios de código reiniciarán el servidor automáticamente.' -ForegroundColor DarkCyan
$watchExtensions = @('.py', '.js', '.html', '.css', '.ps1')
while ($true) {
    $files = Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $watchExtensions -contains $_.Extension -and $_.FullName -notmatch '\\.venv\\|\\.git\\|\\work\\|\\nimas-library\\' }
    $stamp = ($files | Sort-Object FullName | ForEach-Object { "$($_.FullName)|$($_.LastWriteTimeUtc.Ticks)|$($_.Length)" }) -join "`n"
    $process = Start-Process -FilePath $VenvPython -ArgumentList @($ServerScript) -PassThru -NoNewWindow
    while (-not $process.HasExited) {
        Start-Sleep -Milliseconds 700
        $currentFiles = Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $watchExtensions -contains $_.Extension -and $_.FullName -notmatch '\\.venv\\|\\.git\\|\\work\\|\\nimas-library\\' }
        $currentStamp = ($currentFiles | Sort-Object FullName | ForEach-Object { "$($_.FullName)|$($_.LastWriteTimeUtc.Ticks)|$($_.Length)" }) -join "`n"
        if ($currentStamp -ne $stamp) {
            Write-Host 'Cambio detectado; reiniciando servidor…' -ForegroundColor Yellow
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            break
        }
    }
    if ($process.HasExited) { exit $process.ExitCode }
}
