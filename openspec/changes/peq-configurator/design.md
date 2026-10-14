# Design

## Context

See proposal.md - Why for motivation. The current state involves a webdriver-based implementation for PEQ configuration on the Jcally JM98 Max DAC/AMP that is not user-friendly for audiophiles and music listeners. Constraints include targeting Android as the initial platform, using Kivy for the UI framework, and ensuring compatibility with existing PEQ configuration logic and data structures.

## Goals / Non-Goals

**Goals:**
- Create an intuitive Kivy-based Android application for PEQ configuration management
- Implement all core PEQ configuration lifecycle functions: definition, trial, persistence, export, and import
- Maintain compatibility with existing PEQ configuration data structures
- Provide a responsive UI suitable for consumer use on Android devices

**Non-Goals:**
- Support for iOS or other platforms in this initial implementation
- Integration with legacy webdriver interfaces
- Advanced analytics or reporting features
- Cloud synchronization capabilities (focused on local device operation)

## Decisions

**UI Framework Selection: Kivy**
- **Why**: Kivy provides cross-platform capabilities with strong Android support, allowing us to target Android initially while keeping iOS portability as a future option. It offers touch-friendly widgets suitable for consumer audio enthusiast use.
- **Alternatives Considered**: 
  - React Native: Rejected due to larger bundle size and steeper learning curve for the team
  - Native Android (Java/Kotlin): Rejected to maintain code sharing potential and faster development cycle
  - Flutter: Rejected due to team unfamiliarity and Dart language learning curve

**Data Persistence Approach: File-based with Flash Backup**
- **Why**: PEQ configurations need to persist across device reboots and power cycles. Using file-based storage with explicit flash persistence commands gives users control over when configurations are made permanent.
- **Alternatives Considered**:
  - Automatic persistence on every change: Rejected to prevent accidental wear on flash memory
  - Database storage (SQLite): Rejected for simplicity; PEQ configurations are relatively simple structured data

**Export/Import Format: JSON**
- **Why**: JSON provides human-readable, structured data that's easy to parse and generate. It supports the complex nested structure that PEQ configurations may have.
- **Alternatives Considered**:
  - CSV: Rejected due to limitations with hierarchical data
  - Proprietary binary format: Rejected for lack of human readability and debugging difficulty
  - XML: Rejected due to verbosity compared to JSON

**Trial Implementation: Temporary Application**
- **Why**: To allow users to test PEQ settings without affecting the current persistent configuration, we'll apply trial settings in a temporary layer that can be easily discarded.
- **Alternatives Considered**:
  - Direct application with undo: Rejected due to complexity of tracking all changes for rollback
  - Shadow configuration: Selected approach - maintain separate trial configuration that can be applied or discarded

## Risks / Trade-offs

[Flash memory wear from frequent persistence operations] → Implement persistence as explicit user action rather than automatic, and provide warnings about excessive persistence
[Learning curve for audio enthusiasts] → Design intuitive interface with clear labels and minimal steps for common operations
[Device compatibility issues with Kivy] → Test on representative Android devices early in development and maintain fallback options for critical UI components

## Open Questions

None - all key technical decisions have been resolved based on requirements and constraints.