<#
.SYNOPSIS
    Setup script for PEQ Configurator (Windows PowerShell version)

.DESCRIPTION
    Creates virtual environment and installs dependencies using uv.
    Run this from the peq_configurator directory.

.EXAMPLE
    .\setup.ps1

.NOTES
    Requires uv to be installed: https://github.com/astral-sh/uv
#>

param(
    [switch]$ForceRecreate
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Setting up PEQ Configurator in: $ProjectRoot" -ForegroundColor Cyan

# Check if uv is available
try {
    uv --version | Out-Null
    Write-Host "uv found: $(uv --version)" -ForegroundColor Green
} catch {
    Write-Error "ERROR: uv is not installed or not in PATH"
    Write-Host "Please install uv first: https://github.com/astral-sh/uv" -ForegroundColor Red
    exit 1
}

$VenvDir = Join-Path $ProjectRoot ".venv"

# Create virtual environment
if ($ForceRecreate -or -not (Test-Path $VenvDir)) {
    if (Test-Path $VenvDir) {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VenvDir
    }
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    uv venv $VenvDir
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
}

# Determine python and pip executables
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python executable not found at $PythonExe"
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
& $PythonExe -m pip install --upgrade pip

# Install dependencies
$Requirements = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $Requirements) {
    Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
    & $PipExe install -r $Requirements
} else {
    Write-Host "requirements.txt not found, installing kivy directly..." -ForegroundColor Yellow
    & $PipExe install kivy==2.3.0
}

# Install test dependencies
Write-Host "Installing test dependencies..." -ForegroundColor Cyan
& $PipExe install pytest pytest-cov

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "To activate the environment:" -ForegroundColor Cyan
Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "`nTo run tests:" -ForegroundColor Cyan
Write-Host "  python run_tests.py" -ForegroundColor Gray
Write-Host "`nTo run the app:" -ForegroundColor Cyan
Write-Host "  python main.py" -ForegroundColor Gray