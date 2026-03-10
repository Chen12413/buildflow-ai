param(
    [switch]$ApiOnly,
    [switch]$WebOnly,
    [switch]$InstallDeps
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $repoRoot "api"
$webDir = Join-Path $repoRoot "web"
$apiVenvPython = Join-Path $apiDir ".venv\Scripts\python.exe"
$webNodeModules = Join-Path $webDir "node_modules"

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

function Ensure-ApiEnvironment {
    $venvExists = Test-Path $apiVenvPython
    if (-not $venvExists) {
        $bootstrap = Get-PythonBootstrapCommand
        Write-Host "[api] Creating virtual environment..." -ForegroundColor Cyan
        & $bootstrap.Exe @($bootstrap.Args) -m venv "$apiDir/.venv"
    }

    if (-not (Test-Path (Join-Path $apiDir ".env")) -and (Test-Path (Join-Path $apiDir ".env.example"))) {
        Copy-Item (Join-Path $apiDir ".env.example") (Join-Path $apiDir ".env")
        Write-Host "[api] Copied .env from .env.example" -ForegroundColor DarkGray
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
}

function Ensure-WebEnvironment {
    if (-not (Test-Path (Join-Path $webDir ".env.local")) -and (Test-Path (Join-Path $webDir ".env.local.example"))) {
        Copy-Item (Join-Path $webDir ".env.local.example") (Join-Path $webDir ".env.local")
        Write-Host "[web] Copied .env.local from .env.local.example" -ForegroundColor DarkGray
    }

    if ($InstallDeps -or -not (Test-Path $webNodeModules)) {
        Write-Host "[web] Installing Node.js dependencies..." -ForegroundColor Cyan
        Push-Location $webDir
        try {
            npm install
        } finally {
            Pop-Location
        }
    }
}

function Start-TerminalProcess($title, $workingDirectory, $command) {
    $escapedTitle = $title.Replace("'", "''")
    $fullCommand = "`$host.UI.RawUI.WindowTitle = '$escapedTitle'; $command"
    Start-Process -FilePath "powershell.exe" -WorkingDirectory $workingDirectory -ArgumentList @("-NoExit", "-Command", $fullCommand) | Out-Null
}

if (-not $WebOnly) {
    Ensure-ApiEnvironment
}

if (-not $ApiOnly) {
    Ensure-WebEnvironment
}

if (-not $WebOnly) {
    Write-Host "[api] Starting FastAPI dev server..." -ForegroundColor Green
    Start-TerminalProcess "BuildFlow API" $apiDir ".\.venv\Scripts\python.exe -m uvicorn app.main:app --reload"
}

if (-not $ApiOnly) {
    Write-Host "[web] Starting Next.js dev server..." -ForegroundColor Green
    Start-TerminalProcess "BuildFlow Web" $webDir "npm run dev"
}

Write-Host "Done. API: http://localhost:8000  Web: http://localhost:3000" -ForegroundColor Yellow