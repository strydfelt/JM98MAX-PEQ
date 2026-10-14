<#
.SYNOPSIS
    Build script for PEQ Configurator - Windows build using PyInstaller

.DESCRIPTION
    Creates a standalone Windows executable (.exe) from the Python application.
    Uses PyInstaller with appropriate hooks for Kivy.

.PARAMETER Configuration
    Build configuration: Debug or Release (default: Release)

.PARAMETER OutputDir
    Output directory for the built executable (default: build_artifacts\windows)

.PARAMETER Clean
    Clean build artifacts before building

.EXAMPLE
    .\build_windows.ps1
    .\build_windows.ps1 -Configuration Debug
    .\build_windows.ps1 -Clean

.NOTES
    Requires: uv, PyInstaller (will be installed automatically)
#>

param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",
    
    [string]$OutputDir = "build_artifacts\windows",
    
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = $ScriptDir
$OutputDir = Join-Path $ProjectRoot $OutputDir

Write-Host "Building PEQ Configurator for Windows ($Configuration)" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Output directory: $OutputDir" -ForegroundColor Gray

# Clean if requested
if ($Clean) {
    Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
    $BuildDirs = @(
        "$ProjectRoot\build",
        "$ProjectRoot\dist",
        "$ProjectRoot\build_artifacts\windows"
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
    Write-Error "uv is not installed or not in PATH. Please install from https://github.com/astral-sh/uv"
    exit 1
}

# Install PyInstaller if needed
Write-Host "Ensuring PyInstaller is installed..." -ForegroundColor Cyan
& uv pip install pyinstaller

# Main Python script
$MainPy = Join-Path $ProjectRoot "main.py"
if (-not (Test-Path $MainPy)) {
    Write-Error "main.py not found at $MainPy"
    exit 1
}

# Optional icon
$IconPng = Join-Path $ProjectRoot "assets\icon.png"
$IconIco = Join-Path $ProjectRoot "assets\icon.ico"
$Icon = if (Test-Path $IconIco) { $IconIco } elseif (Test-Path $IconPng) { $IconPng } else { $null }

# PyInstaller arguments
$PyInstallerArgs = @(
    "--name=PEQConfigurator",
    "--onefile",
    "--windowed",
    "--clean",
    "--distpath=$OutputDir",
    "--workpath=$(Join-Path $ProjectRoot 'build\pyinstaller')",
    "--specpath=$(Join-Path $ProjectRoot 'build\pyinstaller')",
    "--add-data=$(Join-Path $ProjectRoot 'src');src",
    "--add-data=$(Join-Path $ProjectRoot 'assets');assets",
    "--add-data=$(Join-Path (uv run python -c 'import sys; print(sys.prefix)') 'share');share",
    "--hidden-import=kivy_deps.sdl2",
    "--hidden-import=kivy_deps.glew",
    "--hidden-import=kivy_deps.angle",
    "--hidden-import=android",
    "--hidden-import=jnius"
)

if ($Icon) {
    $PyInstallerArgs += "--icon=$Icon"
    Write-Host "Using icon: $Icon" -ForegroundColor Green
}

$PyInstallerArgs += $MainPy

Write-Host "Running PyInstaller..." -ForegroundColor Cyan
Write-Host "Arguments: $($PyInstallerArgs -join ' ')" -ForegroundColor Gray

try {
    & uv run pyinstaller @PyInstallerArgs
    Write-Host "PyInstaller completed successfully!" -ForegroundColor Green
} catch {
    Write-Error "PyInstaller failed: $_"
    exit 1
}

# Verify output
$ExePath = Join-Path $OutputDir "PEQConfigurator.exe"
if (Test-Path $ExePath) {
    $FileSize = (Get-Item $ExePath).Length / 1MB
    Write-Host "`nBuild successful!" -ForegroundColor Green
    Write-Host "Executable: $ExePath" -ForegroundColor Cyan
    Write-Host "Size: $([math]::Round($FileSize, 2)) MB" -ForegroundColor Gray
    
    # Test run (optional - just verify it starts)
    # & $ExePath --help 2>$null
} else {
    Write-Error "Executable not found at expected location: $ExePath"
    exit 1
}

Write-Host "`nWindows build complete!" -ForegroundColor Green