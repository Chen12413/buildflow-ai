param(
    [switch]$InstallDeps,
    [switch]$UseStableWebCopy,
    [string]$StableWebDir = "C:/buildflow-web-preview",
    [int]$Port = 3026,
    [switch]$BuildOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "lib/web-workspace.ps1")
$webWorkspace = Get-WebWorkspaceContext -RepoRoot $repoRoot -UseStableWebCopy:$UseStableWebCopy -AutoUseStableWebCopy -StableWebDir $StableWebDir

function Start-TerminalProcess($title, $workingDirectory, $command) {
    $escapedTitle = $title.Replace("'", "''")
    $fullCommand = "`$host.UI.RawUI.WindowTitle = '$escapedTitle'; $command"
    Start-Process -FilePath "powershell.exe" -WorkingDirectory $workingDirectory -ArgumentList @("-NoExit", "-Command", $fullCommand) | Out-Null
}

Ensure-WebWorkspace -Workspace $webWorkspace -InstallDeps:$InstallDeps

Push-Location $webWorkspace.ResolvedWebDir
try {
    Write-Host "[web] Running production build..." -ForegroundColor Green
    npm run build
} finally {
    Pop-Location
}

if (-not $BuildOnly) {
    Write-Host "[web] Starting standalone preview..." -ForegroundColor Green
    Start-TerminalProcess "BuildFlow Web Preview" $webWorkspace.ResolvedWebDir "`$env:HOSTNAME='127.0.0.1'; `$env:PORT='$Port'; npm run start"
    Write-Host "Done. Web preview: http://127.0.0.1:$Port" -ForegroundColor Yellow
}
