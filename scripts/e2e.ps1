param(
    [switch]$InstallDeps,
    [switch]$Headed
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $repoRoot "api"
$webDir = Join-Path $repoRoot "web"
$apiVenvPython = Join-Path $apiDir ".venv\Scripts\python.exe"

function Get-PythonBootstrapCommand {
    $candidates = @(
        @{ Exe = (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"); Args = @() },
        @{ Exe = (Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"); Args = @() }
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate.Exe) {
            return $candidate
        }
    }

    try {
        $py = Get-Command py -ErrorAction Stop
        return @{ Exe = $py.Source; Args = @("-3.11") }
    } catch {}

    try {
        $python = Get-Command python -ErrorAction Stop
        return @{ Exe = $python.Source; Args = @() }
    } catch {}

    throw "No Python runtime found. Install Python 3.11+ or fix PATH first."
}

$venvExists = Test-Path $apiVenvPython
if (-not $venvExists) {
    $bootstrap = Get-PythonBootstrapCommand
    Write-Host "[api] Creating virtual environment..." -ForegroundColor Cyan
    & $bootstrap.Exe @($bootstrap.Args) -m venv "$apiDir/.venv"
}

if ($InstallDeps -or -not $venvExists) {
    Write-Host "[api] Installing Python dependencies..." -ForegroundColor Cyan
    Push-Location $apiDir
    try {
        & $apiVenvPython -m pip install -e ".[dev]"
    } finally {
        Pop-Location
    }
}

Push-Location $webDir
try {
    if ($InstallDeps -or -not (Test-Path (Join-Path $webDir "node_modules"))) {
        Write-Host "[web] Installing Node.js dependencies..." -ForegroundColor Cyan
        npm install
    }

    Write-Host "[web] Installing Playwright browser..." -ForegroundColor Cyan
    npx playwright install chromium

    if ($Headed) {
        Write-Host "[e2e] Running headed Playwright tests..." -ForegroundColor Green
        npm run test:e2e:headed
    } else {
        Write-Host "[e2e] Running Playwright tests..." -ForegroundColor Green
        npm run test:e2e
    }
} finally {
    Pop-Location
}
