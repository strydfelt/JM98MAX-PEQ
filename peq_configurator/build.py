#!/usr/bin/env python3
"""
Build script for PEQ Configurator - Cross-platform builds.
Supports Android APK/AAB and Windows executable.
"""
import argparse
import subprocess
import sys
import os
import shutil
from pathlib import Path


def run_cmd(cmd, cwd=None, check=True, env=None):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), 
                           capture_output=True, text=True, env=env)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


def build_android(project_root: Path, build_type: str = "debug", output_dir: Path = None):
    """Build Android APK or AAB using buildozer."""
    print(f"\n{'='*60}")
    print(f"Building Android ({build_type})")
    print(f"{'='*60}")
    
    if output_dir is None:
        output_dir = project_root / "build_artifacts" / "android"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if buildozer is available
    try:
        run_cmd(["buildozer", "version"], check=False)
    except FileNotFoundError:
        print("Installing buildozer...")
        run_cmd(["uv", "pip", "install", "buildozer"])
    
    # Build command
    if build_type == "debug":
        cmd = ["buildozer", "-v", "android", "debug"]
    elif build_type == "release":
        cmd = ["buildozer", "-v", "android", "release"]
    else:
        raise ValueError(f"Unknown build type: {build_type}")
    
    # Set environment for buildozer
    env = os.environ.copy()
    env["BUILDOZER_WARN_ON_ROOT"] = "1"
    
    try:
        run_cmd(cmd, cwd=project_root, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code {e.returncode}")
        return False
    
    # Find and copy artifacts
    bin_dir = project_root / "bin"
    if bin_dir.exists():
        for artifact in bin_dir.glob("*.apk"):
            dest = output_dir / artifact.name
            shutil.copy2(artifact, dest)
            print(f"Copied APK: {dest}")
        for artifact in bin_dir.glob("*.aab"):
            dest = output_dir / artifact.name
            shutil.copy2(artifact, dest)
            print(f"Copied AAB: {dest}")
    
    print(f"\nAndroid build complete! Artifacts in: {output_dir}")
    return True


def build_windows(project_root: Path, output_dir: Path = None):
    """Build Windows executable using PyInstaller."""
    print(f"\n{'='*60}")
    print(f"Building Windows executable")
    print(f"{'='*60}")
    
    if output_dir is None:
        output_dir = project_root / "build_artifacts" / "windows"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if PyInstaller is available
    try:
        run_cmd(["pyinstaller", "--version"], check=False)
    except FileNotFoundError:
        print("Installing PyInstaller...")
        run_cmd(["uv", "pip", "install", "pyinstaller"])
    
    # PyInstaller spec
    main_py = project_root / "main.py"
    icon_png = project_root / "assets" / "icon.png"  # Optional
    src_dir = project_root / "src"
    assets_dir = project_root / "assets"
    
    # ANGLE binaries (required by kivy_deps.angle)
    angle_bin_dir = project_root / ".venv" / "share" / "angle" / "bin"
    
    cmd = [
        "pyinstaller",
        "--name=PEQConfigurator",
        "--onefile",
        "--windowed",
        "--clean",
        f"--distpath={output_dir}",
        f"--workpath={project_root / 'build' / 'pyinstaller'}",
        f"--specpath={project_root / 'build' / 'pyinstaller'}",
        f"--add-data={src_dir};src",
        f"--add-data={assets_dir};assets",
        f"--add-data={angle_bin_dir};share/angle/bin",
        f"--runtime-hook={project_root / 'runtime_hook_kivy_deps.py'}",
        "--hidden-import=kivy_deps.sdl2",
        "--hidden-import=kivy_deps.glew",
        "--hidden-import=kivy_deps.angle",
        "--hidden-import=android",
        "--hidden-import=jnius",
        "--hidden-import=win32timezone",
        str(main_py),
    ]
    
    # Add icon if exists
    if icon_png.exists():
        cmd.insert(-1, f"--icon={icon_png}")
    
    try:
        run_cmd(cmd, cwd=project_root)
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code {e.returncode}")
        return False
    
    exe_path = output_dir / "PEQConfigurator.exe"
    if exe_path.exists():
        print(f"\nWindows build complete! Executable: {exe_path}")
        return True
    else:
        print("Executable not found after build")
        return False


def build_all(project_root: Path, output_base: Path = None):
    """Build for all platforms."""
    if output_base is None:
        output_base = project_root / "build_artifacts"
    
    results = {}
    
    # Windows build (always available)
    print("\n" + "="*60)
    print("BUILDING ALL PLATFORMS")
    print("="*60)
    results["windows"] = build_windows(project_root, output_base / "windows")
    
    # Android build (requires Linux/WSL or buildozer setup)
    try:
        results["android_debug"] = build_android(project_root, "debug", output_base / "android")
        results["android_release"] = build_android(project_root, "release", output_base / "android")
    except Exception as e:
        print(f"Android build skipped: {e}")
        results["android"] = False
    
    # Summary
    print("\n" + "="*60)
    print("BUILD SUMMARY")
    print("="*60)
    for platform, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {platform}: {status}")
    
    all_success = all(results.values())
    print(f"\nOverall: {'ALL BUILDS SUCCESSFUL' if all_success else 'SOME BUILDS FAILED'}")
    return all_success


def main():
    parser = argparse.ArgumentParser(description="Build PEQ Configurator for multiple platforms")
    parser.add_argument("--platform", choices=["android", "windows", "all"], default="all",
                       help="Target platform to build")
    parser.add_argument("--type", choices=["debug", "release"], default="debug",
                       help="Build type (android only)")
    parser.add_argument("--output", type=Path, default=None,
                       help="Output directory for artifacts")
    parser.add_argument("--project-root", type=Path, default=None,
                       help="Project root directory (default: script directory)")
    
    args = parser.parse_args()
    
    if args.project_root is None:
        project_root = Path(__file__).parent.absolute()
    else:
        project_root = args.project_root.absolute()
    
    print(f"Project root: {project_root}")
    
    if args.platform == "android":
        success = build_android(project_root, args.type, args.output)
    elif args.platform == "windows":
        success = build_windows(project_root, args.output)
    else:
        success = build_all(project_root, args.output)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()