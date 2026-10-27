# JM98 Repository Agent Guidance

## peq_configurator (Python/Kivy Android App)

**Dependency Management**: Uses `uv`, not pip or poetry
- Setup: `.\setup.ps1` (Windows) or `python setup.py` (cross-platform)
- Activate: `.\.venv\Scripts\Activate.ps1` (Windows) or `source .venv/bin/activate` (Unix)
- Install deps manually: `uv pip install -r requirements.txt`

**Running & Testing**:
- Run app: `uv run python main.py`
- Run tests: `uv run pytest tests/ -v`
- Run with coverage: `uv run pytest tests/ --cov=src --cov-report=term-missing`
- Test specific module: `uv run pytest tests/test_models.py -v`

**Building**:
- Windows executable: `.\build_windows.ps1` or `uv run python build.py --platform windows`
- Android APK/AAB: Requires Linux/WSL2
  - PowerShell (launches WSL): `.\build_android.ps1 -BuildType debug`
  - WSL/Linux direct: `chmod +x build_android.sh && ./build_android.sh debug`
- Cross-platform: `uv run python build.py --platform all`

**Important Notes**:
- Data models: PEQBand (index, freq, gain, q, type, enabled) and PEQConfiguration (8 bands)
- USB HID communication: Report ID 75, 63-byte packets (same as webdriver)
- Persistence: Explicit flash write operations (not automatic) to prevent wear
- Test suite: 46 tests across models (15), storage (18), device (13)

## webdriver (TypeScript/Vite Web App)

**Development**:
- Start dev server: `npm run dev` or `vite`
- Build for production: `npm run build` or `tsc && vite build`
- Format code: `npm run format` (uses @biomejs/biome)
- Preview build: `npm run preview`

**Technical Details**:
- WebHID API communication with Report ID 75
- Requires browser with WebHID support (Chrome, Edge, Opera)
- Calculates Biquad coefficients for 96kHz sample rate, Q2.30 fixed-point format
- I2C tunneling to Cirrus Logic CS43198 programmable filter registers

## openspec (OpenSpec Change Tracking)

**Existing Change**: `openspec/changes/peq-configurator/` contains a nearly-completed change
- All tasks checked except: "Test application on physical Android device connected to JM98 Max DAC/AMP"
- Artifacts: design.md, proposal.md, tasks.md, .openspec.yaml
- To continue: Would need to complete final testing and archive the change

**OpenSpec Workflow**: Repository uses OpenSpec for change tracking (commands prefixed with `opsx`):
- `opsx propose` - Start a new change
- `opsx ff` - Fast-track through artifact creation
- `opsx apply` - Implement change
- `opsx verify` - Check implementation matches specs
- `opsx archive` - Finalize completed change

## General Repository Structure

- **Monorepo-like**: Independent projects in separate directories
- **No unified build system**: Each project has its own build/test procedures
- **Shared concepts**: Both peq_configurator and webdriver communicate with JM98 MAX via USB HID using identical packet structure (Report ID 75)
- **Configuration**: Root `opencode.json` defines OpenCode permissions (bash access rules)

## Key Conventions

1. **Environment**: peq_configurator uses `uv` and virtual environments (`.venv`)
2. **Platform specifics**: Android builds require Linux/WSL2 (buildozer limitation)
3. **Persistence**: Flash writes are explicit user actions in peq_configurator (prevents wear)
4. **Testing**: peq_configurator uses pytest with configuration in pyproject.toml
5. **Web standards**: webdriver uses Vite, TypeScript, and Biome for formatting