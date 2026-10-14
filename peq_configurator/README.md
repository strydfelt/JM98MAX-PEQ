# JM98 Max PEQ Configurator

A Kivy-based Android application for configuring the Parametric Equalizer (PEQ) on the Jcally JM98 Max USB-C to 3.5mm DAC/AMP headphone adapter.

## Features

- **Define PEQ Parameters** - Intuitive UI for editing 8 PEQ bands (frequency, gain, Q, type)
- **Trial PEQ Settings** - Test configurations temporarily before committing
- **Persist to Flash** - Save configurations permanently to device flash memory
- **Export/Import** - Save and load configurations in JSON or Equalizer APO Filter.txt format
- **Settings** - Global gain control, auto-connect, theme options

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) for dependency management
- Kivy 2.3.0

## Quick Start

### Windows (PowerShell)
```powershell
# Run the setup script
.\setup.ps1

# Activate environment
.\.venv\Scripts\Activate.ps1

# Run tests
uv run pytest tests/ -v

# Run the app
uv run python main.py
```

### Linux/macOS (Python script)
```bash
# Run the setup script
python setup.py

# Activate environment
source .venv/bin/activate

# Run tests
uv run pytest tests/ -v

# Run the app
uv run python main.py
```

### Manual Setup (any platform)
```bash
# Create virtual environment
uv venv .venv

# Activate
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
uv pip install pytest pytest-cov
```

## Building for Android

```bash
# Install buildozer
uv pip install buildozer

# Build debug APK
buildozer -v android debug

# Build release AAB
buildozer -v android release
```

## Project Structure

```
peq_configurator/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── buildozer.spec         # Android build configuration
├── setup.py               # Setup script (cross-platform)
├── setup.ps1              # Setup script (Windows PowerShell)
├── build.py               # Cross-platform build script
├── build_windows.ps1      # Windows build script (PowerShell)
├── build_android.sh       # Android build script (Linux/WSL)
├── build_android.ps1      # Android build script (PowerShell wrapper)
├── pyproject.toml         # Project config (pytest, etc.)
├── .github/workflows/     # GitHub Actions CI/CD
│   └── build.yml
├── src/
│   ├── peq_app.py         # Main application class
│   ├── models/
│   │   └── peq_config.py  # PEQBand, PEQConfiguration data models
│   ├── screens/
│   │   ├── main_screen.py         # Main overview screen
│   │   ├── peq_editor_screen.py   # PEQ parameter editor
│   │   ├── trial_screen.py        # Trial mode screen
│   │   ├── export_import_screen.py # Export/Import screen
│   │   └── settings_screen.py     # Settings screen
│   └── services/
│       ├── device_service.py      # USB HID device communication
│       └── storage_service.py     # Configuration persistence
└── tests/
    ├── test_models.py           # Data model tests (15 tests)
    ├── test_storage_service.py  # Storage service tests (18 tests)
    └── test_device_service.py   # Device service tests (13 tests)
```

## Building

### Windows Executable (PyInstaller)

```powershell
# Quick build
.\build_windows.ps1

# Debug build with clean
.\build_windows.ps1 -Configuration Debug -Clean

# Or use the cross-platform script
uv run python build.py --platform windows
```

Output: `build_artifacts/windows/PEQConfigurator.exe`

### Android APK/AAB (buildozer)

**Requires Linux/WSL2** (buildozer only runs on Linux):

```bash
# In WSL2 or Linux
chmod +x build_android.sh
./build_android.sh debug      # Debug APK
./build_android.sh release    # Release AAB
./build_android.sh debug clean # Clean build
```

Or from PowerShell (launches WSL):
```powershell
.\build_android.ps1 -BuildType debug
.\build_android.ps1 -BuildType release -Clean
```

Output: `build_artifacts/android/*.apk` and `*.aab`

### Cross-platform Build Script

```bash
# Build everything
uv run python build.py --platform all

# Build specific platform
uv run python build.py --platform windows
uv run python build.py --platform android --type release

# Custom output directory
uv run python build.py --platform all --output ./dist
```

### GitHub Actions CI/CD

Automated builds on push/PR:
- **Windows**: Creates `.exe` via PyInstaller
- **Android**: Creates `.apk` (debug) and `.aab` (release) via buildozer
- **Release**: On version tags (`v*`), creates GitHub Release with all artifacts

Trigger manual build with custom type:
```bash
gh workflow run build.yml -f build_type=release
```

## Data Models

The application uses data structures compatible with the existing webdriver implementation:

```python
PEQBand:
    index: int          # 0-7
    freq: float         # 20-20000 Hz
    gain: float         # -12 to +12 dB
    q: float            # 0.1-10
    type: str           # "PK", "LSQ", "HSQ"
    enabled: bool

PEQConfiguration:
    bands: List[PEQBand]  # Exactly 8 bands
```

## Export Formats

### JSON (Native)
```json
{
  "device": "JM98MAX",
  "timestamp": "2024-01-01T00:00:00",
  "globalGain": -3.0,
  "bands": [
    {"index": 0, "freq": 40, "gain": 2.0, "q": 1.0, "type": "PK", "enabled": true},
    ...
  ]
}
```

### Filter.txt (Equalizer APO / Peace / AutoEQ compatible)
```
Preamp: -5.4 dB
Filter 1: ON PK Fc 20 Hz Gain -0.9 dB Q 2.000
Filter 2: ON PK Fc 29 Hz Gain -2.5 dB Q 0.500
...
```

## Device Communication

The app communicates with the JM98 Max via USB HID using the same protocol as the webdriver:
- Vendor ID: 0x661 (JCally / Generic Savitech)
- Report ID: 75
- Packet Size: 63 bytes
- 8 PEQ bands with IIR filter coefficients in Q30 format

## Testing

Tests use **pytest** and are discoverable by VS Code's Test Explorer.

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test module
uv run pytest tests/test_models.py -v
uv run pytest tests/test_storage_service.py -v
uv run pytest tests/test_device_service.py -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# VS Code: Open Command Palette (Ctrl+Shift+P) → "Python: Configure Tests" → select "pytest"
```

### Test Coverage
- **46 tests total** across 3 modules
- `test_models.py` - 15 tests (PEQBand, PEQConfiguration)
- `test_storage_service.py` - 18 tests (JSON + Filter.txt export/import)
- `test_device_service.py` - 13 tests (MockDeviceService, constants, IIR filter)

## License

MIT License - See LICENSE file for details.