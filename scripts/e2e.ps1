param(
    [switch]$InstallDeps,
    [switch]$Headed,
    [switch]$UseStableWebCopy,
    [string]$StableWebDir = "C:/buildflow-web-e2e"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "lib/web-workspace.ps1")
$apiDir = Join-Path $repoRoot "api"
$webWorkspace = Get-WebWorkspaceContext -RepoRoot $repoRoot -UseStableWebCopy:$UseStableWebCopy -AutoUseStableWebCopy -StableWebDir $StableWebDir
$apiVenvPython = Join-Path $apiDir ".venv\Scripts\python.exe"

function Get-FreeTcpPort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    try {
        $listener.Start()
        return ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    } finally {
        $listener.Stop()
    }
}

$webPort = Get-FreeTcpPort
$apiPort = Get-FreeTcpPort
while ($apiPort -eq $webPort) {
    $apiPort = Get-FreeTcpPort
}

function Stop-ListeningProcessOnPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $listeners) {
        return
    }

    $processIds = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        if ($processId -le 0) {
            continue
        }

        Write-Host "[e2e] Releasing port $Port from PID $processId..." -ForegroundColor Yellow
        & taskkill /PID $processId /T /F | Out-Null
    }
}

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
Stop-ListeningProcessOnPort -Port $webPort
Stop-ListeningProcessOnPort -Port $apiPort

Push-Location $webWorkspace.ResolvedWebDir
try {
    $previousRepoRoot = $env:BUILD_FLOW_REPO_ROOT
    $previousWebWorkspace = $env:BUILD_FLOW_WEB_WORKSPACE
    $previousPythonBin = $env:E2E_PYTHON_BIN
    $previousBaseUrl = $env:E2E_BASE_URL
    $previousApiBaseUrl = $env:E2E_API_BASE_URL
    $env:BUILD_FLOW_REPO_ROOT = $repoRoot
    $env:BUILD_FLOW_WEB_WORKSPACE = $webWorkspace.ResolvedWebDir
    $env:E2E_PYTHON_BIN = $apiVenvPython
    $env:E2E_BASE_URL = "http://127.0.0.1:$webPort"
    $env:E2E_API_BASE_URL = "http://127.0.0.1:$apiPort"

    Write-Host "[e2e] Using web URL $($env:E2E_BASE_URL)" -ForegroundColor DarkGray
    Write-Host "[e2e] Using api URL $($env:E2E_API_BASE_URL)" -ForegroundColor DarkGray

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
    $env:BUILD_FLOW_REPO_ROOT = $previousRepoRoot
    $env:BUILD_FLOW_WEB_WORKSPACE = $previousWebWorkspace
    $env:E2E_PYTHON_BIN = $previousPythonBin
    $env:E2E_BASE_URL = $previousBaseUrl
    $env:E2E_API_BASE_URL = $previousApiBaseUrl
    Pop-Location
}
