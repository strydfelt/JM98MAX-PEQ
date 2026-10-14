# Proposal

## Why
The existing webdriver implementation for PEQ configuration on the Jcally JM98 Max (a portable USB-C to 3.5mm DAC/AMP headphone adapter) is not user-friendly for audiophiles and music listeners. A mobile Kivy application will provide an intuitive interface for defining, trialing, persisting, exporting, and importing PEQ configurations directly on Android devices.

## What Changes
- Create a Kivy-based Android application for PEQ configuration management
- Implement screens for defining PEQ parameters
- Add functionality to trial PEQ settings on the device
- Implement persistence of PEQ configurations to flash memory
- Add export and import capabilities for PEQ configurations to/from files
- Ensure the application follows the existing webdriver implementation's logic and data structures

## Capabilities
### New Capabilities
- peq-configurator: Manages the full lifecycle of PEQ configuration including definition, trial, persistence, export, and import.

### Modified Capabilities
*None*

## Impact
- New Android application source code in the project
- Potential need for new dependencies (Kivy, etc.)
- Integration with existing PEQ configuration backend (if any) or creation of new backend logic
- Impact on flash memory management for persisting configurations
- Need for file storage access for export/import functionality