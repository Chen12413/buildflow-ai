function Get-WebWorkspaceContext {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,
        [switch]$UseStableWebCopy,
        [switch]$AutoUseStableWebCopy,
        [string]$StableWebDir = "C:/buildflow-web-fix"
    )

    $sourceWebDir = Join-Path $RepoRoot "web"
    $inOneDrive = $RepoRoot -like "*OneDrive*"
    $shouldUseStableCopy = $UseStableWebCopy -or ($AutoUseStableWebCopy -and $inOneDrive)
    $resolvedWebDir = if ($shouldUseStableCopy) { $StableWebDir } else { $sourceWebDir }

    return [pscustomobject]@{
        RepoRoot = $RepoRoot
        SourceWebDir = $sourceWebDir
        ResolvedWebDir = $resolvedWebDir
        StableWebDir = $StableWebDir
        UsingStableCopy = $shouldUseStableCopy
        InOneDrive = $inOneDrive
    }
}

function Sync-WebWorkspace {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceDir,
        [Parameter(Mandatory = $true)]
        [string]$TargetDir
    )

    if (-not (Test-Path $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir | Out-Null
    }

    $robocopyArgs = @(
        $SourceDir,
        $TargetDir,
        "/E",
        "/R:1",
        "/W:1",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS",
        "/NP",
        "/XD", "node_modules", ".next", "playwright-report", "test-results"
    )

    & robocopy @robocopyArgs | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "Failed to sync web workspace to stable copy. robocopy exit code: $LASTEXITCODE"
    }
}

function Ensure-WebWorkspace {
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Workspace,
        [switch]$InstallDeps
    )

    if ($Workspace.UsingStableCopy) {
        Write-Host "[web] Syncing repository web workspace to stable copy..." -ForegroundColor Cyan
        Sync-WebWorkspace -SourceDir $Workspace.SourceWebDir -TargetDir $Workspace.ResolvedWebDir
    } elseif ($Workspace.InOneDrive) {
        Write-Host "[web] Detected OneDrive workspace. If Next.js becomes unstable, rerun with -UseStableWebCopy." -ForegroundColor Yellow
    }

    $envFile = Join-Path $Workspace.ResolvedWebDir ".env.local"
    $envExampleFile = Join-Path $Workspace.ResolvedWebDir ".env.local.example"
    if (-not (Test-Path $envFile) -and (Test-Path $envExampleFile)) {
        Copy-Item $envExampleFile $envFile
        Write-Host "[web] Copied .env.local from .env.local.example" -ForegroundColor DarkGray
    }

    $nodeModulesDir = Join-Path $Workspace.ResolvedWebDir "node_modules"
    if ($InstallDeps -or -not (Test-Path $nodeModulesDir)) {
        Write-Host "[web] Installing Node.js dependencies..." -ForegroundColor Cyan
        Push-Location $Workspace.ResolvedWebDir
        try {
            npm install
        } finally {
            Pop-Location
        }
    }
}
