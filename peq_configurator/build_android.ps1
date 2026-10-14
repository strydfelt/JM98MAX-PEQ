<#
.SYNOPSIS
    Build script for PEQ Configurator - Android build using buildozer

.DESCRIPTION
    Creates Android APK/AAB using buildozer. 
    Note: buildozer requires a Linux environment. On Windows, use WSL2 or GitHub Actions.

.PARAMETER BuildType
    Build type: debug or release (default: debug)

.PARAMETER OutputDir
    Output directory for artifacts (default: build_artifacts\android)

.PARAMETER Clean
    Clean build artifacts before building

.EXAMPLE
    .\build_android.ps1
    .\build_android.ps1 -BuildType release
    .\build_android.ps1 -Clean

.NOTES
    - Requires Linux environment (WSL2 on Windows)
    - buildozer will be installed automatically via uv
    - For WSL2: run this script from within WSL (bash build_android.sh)
#>

param(
    [ValidateSet("debug", "release")]
    [string]$BuildType = "debug",
    
    [string]$OutputDir = "build_artifacts\android",
    
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = $ScriptDir
$OutputDir = Join-Path $ProjectRoot $OutputDir

Write-Host "Building PEQ Configurator for Android ($BuildType)" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray

# Check if running in WSL/Linux
$IsWSL = $env:WSL_DISTRO_NAME -or $env:WSL_INTEROP
$IsLinux = ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform("Linux"))

if (-not ($IsWSL -or $IsLinux)) {
    Write-Warning "buildozer requires a Linux environment."
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  1. Run this script from WSL2: wsl bash build_android.sh" -ForegroundColor Gray
    Write-Host "  2. Use GitHub Actions for CI/CD builds" -ForegroundColor Gray
    Write-Host "  3. Use a Linux VM or Docker container" -ForegroundColor Gray
    Write-Host "" -ForegroundColor Gray
    Write-Host "For WSL2, ensure you have:" -ForegroundColor Cyan
    Write-Host "  - Ubuntu or Debian installed in WSL2" -ForegroundColor Gray
    Write-Host "  - build dependencies: buildozer dependencies for Ubuntu" -ForegroundColor Gray
    exit 1
}

# Clean if requested
if ($Clean) {
    Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
    $BuildDirs = @(
        Join-Path $ProjectRoot "bin",
        Join-Path $ProjectRoot ".buildozer",
        Join-Path $ProjectRoot "build_artifacts\android"
    )
    foreach ($dir in $BuildDirs) {
        if (Test-Path $dir) {
            Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
            Write-Host "  Removed: $dir" -ForegroundColor Gray
        }
    }
}

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}

# Check if uv is available
try {
    $uvVersion = uv --version
    Write-Host "uv found: $uvVersion" -ForegroundColor Green
} catch {
    Write-Error "uv is not installed or not in PATH"
    exit 1
}

# Install buildozer if needed
Write-Host "Ensuring buildozer is installed..." -ForegroundColor Cyan
& uv pip install buildozer

# Build command
$BuildozerArgs = @("buildozer", "-v", "android", $BuildType)
Write-Host "Running buildozer..." -ForegroundColor Cyan
Write-Host "Command: $($BuildozerArgs -join ' ')" -ForegroundColor Gray

$Env:BUILDOZER_WARN_ON_ROOT = "1"

try {
    & $BuildozerArgs
    Write-Host "buildozer completed successfully!" -ForegroundColor Green
} catch {
    Write-Error "buildozer failed: $_"
    exit 1
}

# Copy artifacts
$BinDir = Join-Path $ProjectRoot "bin"
if (Test-Path $BinDir) {
    $Artifacts = Get-ChildItem $BinDir -Filter "*.apk", "*.aab" -File
    if ($Artifacts.Count -gt 0) {
        foreach ($artifact in $Artifacts) {
            $Dest = Join-Path $OutputDir $artifact.Name
            Copy-Item $artifact.FullName -Destination $Dest -Force
            Write-Host "Copied: $($artifact.Name) -> $Dest" -ForegroundColor Green
        }
    } else {
        Write-Warning "No APK/AAB artifacts found in $BinDir"
    }
} else {
    Write-Warning "Bin directory not found: $BinDir"
}

Write-Host "`nAndroid build complete!" -ForegroundColor Green
Write-Host "Artifacts in: $OutputDir" -ForegroundColor Cyan