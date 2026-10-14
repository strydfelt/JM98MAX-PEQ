#!/usr/bin/env python3
"""
Setup script for PEQ Configurator.
Creates virtual environment and installs dependencies using uv.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_cmd(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


def main():
    """Main setup function."""
    project_root = Path(__file__).parent.absolute()
    print(f"Setting up PEQ Configurator in: {project_root}")
    
    # Check if uv is available
    try:
        run_cmd(["uv", "--version"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: uv is not installed or not in PATH")
        print("Please install uv first: https://github.com/astral-sh/uv")
        sys.exit(1)
    
    venv_dir = project_root / ".venv"
    
    # Create virtual environment
    if not venv_dir.exists():
        print("Creating virtual environment...")
        run_cmd(["uv", "venv", str(venv_dir)], cwd=project_root)
    else:
        print("Virtual environment already exists")
    
    # Determine python executable
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    # Upgrade pip
    print("Upgrading pip...")
    run_cmd([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], cwd=project_root)
    
    # Install dependencies
    requirements = project_root / "requirements.txt"
    if requirements.exists():
        print("Installing dependencies from requirements.txt...")
        run_cmd([str(pip_exe), "install", "-r", str(requirements)], cwd=project_root)
    else:
        print("requirements.txt not found, installing kivy directly...")
        run_cmd([str(pip_exe), "install", "kivy==2.3.0"], cwd=project_root)
    
    # Install test dependencies
    print("Installing test dependencies...")
    run_cmd([str(pip_exe), "install", "pytest", "pytest-cov"], cwd=project_root)
    
    print("\nSetup complete!")
    print(f"To activate the environment:")
    if sys.platform == "win32":
        print(f"  .venv\\Scripts\\activate")
    else:
        print(f"  source .venv/bin/activate")
    print(f"\nTo run tests:")
    print(f"  python run_tests.py")
    print(f"\nTo run the app:")
    print(f"  python main.py")


if __name__ == "__main__":
    main()