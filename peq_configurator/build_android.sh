#!/bin/bash
# Build script for PEQ Configurator - Android build using buildozer
# Run this from WSL2 or Linux

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BUILD_TYPE="${1:-debug}"
OUTPUT_DIR="${2:-$PROJECT_ROOT/build_artifacts/android}"

echo "=========================================="
echo "Building PEQ Configurator for Android ($BUILD_TYPE)"
echo "Project root: $PROJECT_ROOT"
echo "Output directory: $OUTPUT_DIR"
echo "=========================================="

# Clean if requested
if [[ "$3" == "clean" ]]; then
    echo "Cleaning previous build artifacts..."
    rm -rf "$PROJECT_ROOT/bin"
    rm -rf "$PROJECT_ROOT/.buildozer"
    rm -rf "$OUTPUT_DIR"
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed. Please install from https://github.com/astral-sh/uv"
    exit 1
fi

# Install buildozer if needed
echo "Ensuring buildozer is installed..."
uv pip install buildozer

# Build command
echo "Running buildozer..."
export BUILDOZER_WARN_ON_ROOT=1

if ! buildozer -v android "$BUILD_TYPE"; then
    echo "ERROR: buildozer failed"
    exit 1
fi

# Copy artifacts
BIN_DIR="$PROJECT_ROOT/bin"
if [[ -d "$BIN_DIR" ]]; then
    echo "Copying artifacts to $OUTPUT_DIR..."
    find "$BIN_DIR" -name "*.apk" -o -name "*.aab" | while read -r artifact; do
        filename=$(basename "$artifact")
        cp "$artifact" "$OUTPUT_DIR/$filename"
        echo "Copied: $filename"
    done
else
    echo "WARNING: Bin directory not found: $BIN_DIR"
fi

echo ""
echo "=========================================="
echo "Android build complete!"
echo "Artifacts in: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"
echo "=========================================="