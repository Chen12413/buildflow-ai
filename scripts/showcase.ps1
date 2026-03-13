param(
    [switch]$InstallDeps,
    [switch]$UseStableWebCopy,
    [string]$StableWebDir = "C:/buildflow-web-showcase"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "lib/web-workspace.ps1")
$apiDir = Join-Path $repoRoot "api"
$webWorkspace = Get-WebWorkspaceContext -RepoRoot $repoRoot -UseStableWebCopy:$UseStableWebCopy -AutoUseStableWebCopy -StableWebDir $StableWebDir
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

Ensure-WebWorkspace -Workspace $webWorkspace -InstallDeps:$InstallDeps

Push-Location $webWorkspace.ResolvedWebDir
try {
    Write-Host "[web] Installing Playwright browser..." -ForegroundColor Cyan
    npx playwright install chromium

    Write-Host "[showcase] Capturing repository screenshots..." -ForegroundColor Green
    $env:BUILD_FLOW_REPO_ROOT = $repoRoot
    $env:BUILD_FLOW_WEB_WORKSPACE = $webWorkspace.ResolvedWebDir
    npm run capture:showcase
} finally {
    Remove-Item Env:BUILD_FLOW_REPO_ROOT -ErrorAction SilentlyContinue
    Remove-Item Env:BUILD_FLOW_WEB_WORKSPACE -ErrorAction SilentlyContinue
    Pop-Location
}
