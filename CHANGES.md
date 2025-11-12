# Fleet MCP Changelog

All notable changes to Fleet MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2025-10-22

### Added
- **Script Content Retrieval**: The `fleet_get_script` tool now returns the full script content in addition to metadata, making it easier to review and verify scripts before execution.
- **Version Reporting in Health Check**: The server health check endpoint now includes the Fleet MCP version number, improving diagnostics and version tracking.

### Changed
- **Enhanced Script Tool Response**: Updated `fleet_get_script` to include `script_content` field in the response data, providing complete script information in a single tool call.
- **Improved Health Check Information**: The `fleet_health_check` tool now reports both Fleet server version and Fleet MCP server version for better system visibility.

### Documentation
- **Usage Guide Update**: Significantly expanded and reorganized the `docs/USAGE.md` file with:
  - Detailed examples for all 100+ MCP tools across 17 categories
  - Step-by-step workflows for common Fleet management tasks
  - Enhanced troubleshooting section
  - Better organization and navigation
  - Removed outdated tool reference and example files

### Testing
- Added integration tests for script content retrieval
- Enhanced unit tests for script tools to verify content inclusion
- Updated health check tests to verify version reporting

## [1.0.1] - 2025-10-21

### Changed
- Updated package version from 0.1.1 to 1.0.1 to reflect production readiness
- Applied black code formatting across entire codebase for consistency
- Resolved all ruff linting errors
- Fixed import sort order issues

### Added
- Test suite with 100% passing tests
- GitHub Actions CI/CD workflows for automated testing
- Branch protection and security rulesets

## [1.0.0] - 2025-10-21

### Major Release
First production-ready release of Fleet MCP.

### Features
- **100+ MCP Tools** across 17 categories:
  - Host Management (17 tools)
  - Query Execution (8 tools)
  - Policy Management (7 tools)
  - Software Management (8 tools)
  - Team Management (6 tools)
  - User Management (4 tools)
  - Label Management (5 tools)
  - Script Management (11 tools)
  - MDM Management (6 tools)
  - Pack Management (3 tools)
  - Carve Management (2 tools)
  - Secret Variables (1 tool)
  - Activity Monitoring (1 tool)
  - Device Management (3 tools)
  - Configuration (3 tools)
  - Osquery Tables (2 tools)
  - VPP Management (2 tools)

### Core Capabilities
- **Live Query Execution**: Run osquery queries across your fleet
- **Policy Management**: Create, update, and monitor security policies
- **Team & User Management**: Manage Fleet users and team-based access
- **Software Management**: Track and manage software across devices
- **Script Execution**: Run and manage scripts on hosts
- **MDM Integration**: Apple MDM commands and profile management
- **Osquery Table Discovery**: Dynamic table schema discovery with caching
- **Read-Only Mode**: Safe exploration mode for production environments
- **Activity Monitoring**: Track Fleet activities and changes
- **Error Handling**: Detailed error messages and recovery guidance

### Technical Features
- **Schema Override System**: Download and cache osquery table schemas from Fleet's GitHub
- **Intelligent Caching**: Local caching of table schemas with automatic updates
- **Type Safety**: Full type hints and mypy compliance
- **Async Support**: Built on httpx for efficient async operations
- **Flexible Configuration**: TOML config files or environment variables
- **Extensive Testing**: Unit and integration tests with pytest
- **CI/CD**: Automated testing and publishing workflows

### Documentation
- Updated README with installation and setup instructions for fleet-mcp itself
- Detailed USAGE guide with examples for all tools
- Configuration templates and examples

## [0.1.1] - 2025-10-11

### Changed
- Migrated to `uv` for dependency management
- Updated type hints to use `|` operator instead of `Optional[]`
- Updated README with uv installation instructions

### Added
- Development workflow documentation for uv
- Lock file (uv.lock) for reproducible builds

## [0.1.0] - 2025-10-11

### Initial Release
- Basic Fleet MCP server implementation
- Core host and query management tools
- Configuration management
- Initial documentation

---

## Version History Summary

- **1.0.2** (2025-10-22): Script content retrieval, version reporting, documentation improvements
- **1.0.1** (2025-10-21): Code formatting, linting fixes, production release
- **1.0.0** (2025-10-21): Prep for first production release with 100+ tools
- **0.1.1** (2025-10-11): Migration to uv package manager
- **0.1.0** (2025-10-11): Initial release

## Links

- [GitHub Repository](https://github.com/SimplyMinimal/fleet-mcp)
- [Issue Tracker](https://github.com/SimplyMinimal/fleet-mcp/issues)
- [Documentation](https://github.com/SimplyMinimal/fleet-mcp#readme)
