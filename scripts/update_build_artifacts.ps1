<#
Build with PyInstaller and print the produced executable path.

This script does NOT add build artifacts to git. It runs PyInstaller
using the specified spec file (default: translate-local-py.spec) and
then reports the path to the produced exe under dist/. The intent is
to let you run the local exe directly without committing artifacts.

Usage:
  ./scripts/update_build_artifacts.ps1
  ./scripts/update_build_artifacts.ps1 -SpecFile my.spec
#>

param(
    [string]$SpecFile = 'translate-local-py.spec'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[info] $msg" -ForegroundColor Cyan }
function Write-Err($msg) { Write-Host "[error] $msg" -ForegroundColor Red }

try {
    # Move to repository root (script located in ./scripts)
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Push-Location (Resolve-Path (Join-Path $scriptDir '..')) | Out-Null

    Write-Info "Spec file: $SpecFile"

    Write-Info 'Running PyInstaller...'
    & python -m PyInstaller -y $SpecFile

    # Locate the produced exe if present
    $exePath = Join-Path (Join-Path (Get-Location) 'dist') 'translate-local-py\translate-local-py.exe'
    if (Test-Path -Path $exePath) {
        Write-Info "Executable: $exePath"
    } else {
        # Try find any exe in dist
        $found = Get-ChildItem -Path (Join-Path (Get-Location) 'dist') -Recurse -Filter '*.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            Write-Info "Found executable: $($found.FullName)"
        } else {
            Write-Info 'No executable found in dist/. Check PyInstaller output for errors.'
        }
    }

    Write-Info 'Note: dist/ and build/ are NOT added to git by this script.'
    Pop-Location | Out-Null
    exit 0
} catch {
    Write-Err "$_"
    if (Get-Location) { Pop-Location | Out-Null }
    exit 1
}
