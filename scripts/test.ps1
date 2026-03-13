param(
    [switch]$SkipWeb,
    [switch]$InstallDeps,
    [switch]$IncludeE2E,
    [switch]$UseStableWebCopy,
    [string]$StableWebDir = "C:/buildflow-web-test"
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

    throw "No Python runtime found."
}

$venvExists = Test-Path $apiVenvPython
if (-not $venvExists) {
    $bootstrap = Get-PythonBootstrapCommand
    Write-Host "[api] Creating virtual environment..." -ForegroundColor Cyan
    & $bootstrap.Exe @($bootstrap.Args) -m venv "$apiDir/.venv"
}

Push-Location $apiDir
try {
    if ($InstallDeps -or -not $venvExists) {
        Write-Host "[api] Installing Python dependencies..." -ForegroundColor Cyan
        & $apiVenvPython -m pip install -e ".[dev]"
    }

    Write-Host "[api] Running pytest..." -ForegroundColor Green
    & $apiVenvPython -m pytest -q
} finally {
    Pop-Location
}

if (-not $SkipWeb) {
    Ensure-WebWorkspace -Workspace $webWorkspace -InstallDeps:$InstallDeps
    Push-Location $webWorkspace.ResolvedWebDir
    try {
        Write-Host "[web] Running next build..." -ForegroundColor Green
        npm run build
    } finally {
        Pop-Location
    }
}

if ($IncludeE2E) {
    Write-Host "[e2e] Running Playwright regression..." -ForegroundColor Green
    $e2eScript = Join-Path $repoRoot "scripts/e2e.ps1"
    if ($InstallDeps) {
        & $e2eScript -InstallDeps -UseStableWebCopy:$webWorkspace.UsingStableCopy -StableWebDir $webWorkspace.StableWebDir
    } else {
        & $e2eScript -UseStableWebCopy:$webWorkspace.UsingStableCopy -StableWebDir $webWorkspace.StableWebDir
    }
}
