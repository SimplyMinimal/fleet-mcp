# Fleet MCP Changelog

All notable changes to Fleet MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-11-20

### Added
- **Asynchronous Query Execution**: New async query pattern to work around the 60-second MCP client timeout limitation in TypeScript-based clients like LM Studio
  - `fleet_run_live_query_with_results` now supports async mode when `FLEET_USE_ASYNC_QUERY_MODE=true`
  - `fleet_get_query_results` tool to retrieve results from async queries by campaign ID
  - `fleet_list_async_queries` tool to list all running and completed async queries with status filtering
  - `fleet_cancel_query` tool to cancel running async queries
  - Disk-based storage for intermediate query results with configurable retention (default: 24 hours)
  - Future Redis support planned for distributed deployments

- **Schema Overrides Feature**: Enhanced osquery table documentation with Fleet's curated metadata
  - Automatic download of YAML schema files from Fleet's GitHub repository (`schema/tables/`)
  - Local caching of schema overrides in `~/.fleet-mcp/cache/schema_overrides.json`
  - Intelligent merging of override data with base osquery schemas
  - Prominent display of usage requirements and examples in `fleet_get_osquery_table_schema` responses
  - Multi-tier loading strategy: cache → download → stale cache fallback
  - 24-hour cache TTL with graceful degradation if downloads fail

- **Fuzzy Matching Host Lookup**: Intelligent host identifier resolution for flexible host targeting
  - New `host_identifier.py` utility module for smart host lookups
  - Support for matching hosts by hostname, UUID, serial number, or hardware model
  - Enhanced `fleet_run_live_query_with_results` to support fuzzy host matching
  - Automatic disambiguation when multiple hosts match

- **CVE Filtering Support**: Enhanced vulnerability tracking and reporting
  - New CVE filtering capabilities in `software_tools.py`
  - Filter software by specific CVE identifiers
  - Improved vulnerability tracking across the fleet
  - Enhanced documentation with CVE filtering examples

- **WebSocket-Based Live Query**: Complete rewrite of live query execution
  - Replaced `fleet_run_live_query` with WebSocket-based `fleet_run_live_query_with_results`
  - New `websocket_client.py` module for real-time result streaming
  - Improved reliability and performance for live queries

- **Docker Support**: Containerized deployment option
  - Added Dockerfile for easy deployment and distribution
  - Simplified setup for containerized environments

- **Development Tooling**:
  - Pre-commit hooks for automated code quality checks (Black, isort, mypy)
  - `.pre-commit-hooks-guide.md` documentation
  - Updated `CONTRIBUTING.md` with pre-commit setup instructions
  - Auto-updating pre-commit hook versions

- **Security Policy**: Added `SECURITY.md` file with security reporting directions.

### Changed
- **Query Tool Enhancement**: `fleet_run_live_query_with_results` now returns campaign_id and status immediately in async mode instead of blocking
- **Configuration Options**: Added three new configuration parameters:
  - `use_async_query_mode` (default: false) - Enable async query execution
  - `async_query_storage_dir` (default: `.fleet_mcp_async_queries`) - Directory for storing async query results
  - `async_query_retention_hours` (default: 24) - Hours to retain completed query results
- **Table Schema Cache**: Enhanced `TableSchemaCache` to support schema overrides with automatic download and caching
- **Health Check**: Now reports schema override cache status and source (cache/download/none)

### Fixed
- **Policy Creation**: Fixed issue with creating policies globally vs team-specific
- **WebSocket Connection**: Improved WebSocket connection handling for live queries
- **Import Organization**: Updated `known_first_party` in pyproject.toml for better import sorting

### Technical Improvements
- **AsyncQueryManager**: New disk-based query job manager with status tracking (pending/running/completed/failed/cancelled)
- **Background Task Management**: Async queries run in background tasks with proper lifecycle management
- **Code Refactoring**: Applied some DRY (Don't Repeat Yourself) principles across the codebase
  - Refactored all tools to use common response formatting functions
  - Created common utilities for pagination parameter building
  - Applied `@handle_fleet_api_errors` decorator across all tool functions
  - Consolidated error handling and response formatting
  - Refactored activity, device, user, config, team, VPP, and async query tools
- **Error Handling**: Improved error messages for async query operations with detailed status information
- **Testing**: Comprehensive test coverage with ~1,200+ new test lines
  - Added `test_config.py` with 33 new tests
  - Enhanced `test_websocket_client.py` with 37 additional tests
  - New integration tests for query host by identifier
- **Code Quality**: Temporarily disabled ruff formatter in favor of Black for more consistent formatting
- **Package Updates**: Updated uv packages and added WebSocket dependencies

### Documentation
- Updated usage documentation with async query pattern examples
- Added schema overrides feature documentation
- Enhanced configuration guide with new async query settings
- Added CVE filtering examples
- Added fuzzy host matching documentation
- Enhanced troubleshooting section

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

- **1.1.0** (2025-11-20): Async query execution, schema overrides, fuzzy host matching, CVE filtering, WebSocket-based queries, Docker support, major code refactoring
- **1.0.2** (2025-10-22): Script content retrieval, version reporting, documentation improvements
- **1.0.1** (2025-10-21): Code formatting, linting fixes, production release
- **1.0.0** (2025-10-21): Prep for first production release with 100+ tools
- **0.1.1** (2025-10-11): Migration to uv package manager
- **0.1.0** (2025-10-11): Initial release

## Links

- [GitHub Repository](https://github.com/SimplyMinimal/fleet-mcp)
- [Issue Tracker](https://github.com/SimplyMinimal/fleet-mcp/issues)
- [Documentation](https://github.com/SimplyMinimal/fleet-mcp#readme)
