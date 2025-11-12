# Contributing to Fleet MCP

Thank you for your interest in contributing to Fleet MCP! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/SimplyMinimal/fleet-mcp.git
   cd fleet-mcp
   ```

2. Install dependencies:
   ```bash
   uv sync --dev
   ```

3. Install pre-commit hooks (recommended):
   ```bash
   uv run pre-commit install
   ```

## Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to automatically run code quality checks before each commit. The hooks ensure code consistency and catch common issues early.

### What the Pre-commit Hooks Do

The pre-commit hooks automatically run the following checks:

1. **General File Checks**:
   - Remove trailing whitespace
   - Ensure files end with a newline
   - Validate YAML, JSON, and TOML syntax
   - Check for large files
   - Detect merge conflicts

2. **Code Formatting** (auto-fixes):
   - **Black**: Formats Python code to a consistent style
   - **isort**: Sorts and organizes import statements

3. **Type Checking**:
   - **mypy**: Checks type annotations in the `src/` directory

### Installing Pre-commit Hooks

After cloning the repository and installing dependencies, run:

```bash
uv run pre-commit install
```

This installs the git hook scripts that will run automatically before each commit.

### Running Pre-commit Hooks Manually

To run all hooks on all files (useful after initial setup or updating hooks):

```bash
uv run pre-commit run --all-files
```

To run hooks on specific files:

```bash
uv run pre-commit run --files src/fleet_mcp/client.py
```

To run a specific hook:

```bash
uv run pre-commit run black --all-files
uv run pre-commit run mypy --all-files
```

### Updating Pre-commit Hooks

To update the hooks to their latest versions:

```bash
uv run pre-commit autoupdate
```

### Skipping Pre-commit Hooks (Not Recommended)

If you need to commit without running the hooks (not recommended):

```bash
git commit --no-verify -m "Your commit message"
```

**Note**: Even if you skip pre-commit hooks locally, the CI pipeline will still run all checks. It's better to fix issues locally before pushing.

## Code Quality Standards

### Formatting

- **Black**: Line length of 88 characters, Python 3.10+ target
- **isort**: Black-compatible profile, groups imports by stdlib → third-party → first-party

Configuration is in `pyproject.toml`.

### Type Checking

- **mypy**: Strict type checking enabled for `src/` directory
- All functions in `src/` must have type annotations
- Tests in `tests/` have relaxed type checking requirements

### Testing

Run tests with:

```bash
# Run all tests
uv run pytest

# Run only unit tests
uv run pytest -m unit

# Run with coverage
uv run pytest --cov=fleet_mcp --cov-report=html
```

### Manual Code Quality Checks

You can run the same checks that CI runs:

```bash
# Format code
uv run black src tests

# Sort imports
uv run isort src tests

# Type check
uv run mypy src

# Run all checks (read-only)
uv run black --check src tests
uv run isort --check-only src tests
uv run mypy src
```

## Continuous Integration

The CI pipeline runs on every push and pull request. It includes:

1. **Unit Tests**: Python 3.10, 3.11, and 3.12
2. **Lint and Format**: Black and isort checks
3. **Type Check**: mypy validation

All checks must pass before a pull request can be merged.

## Commit Message Guidelines

- Use clear, descriptive commit messages
- Start with a verb in the imperative mood (e.g., "Add", "Fix", "Update")
- Keep the first line under 72 characters
- Add detailed description in the body if needed

Example:
```
Add support for async query cancellation

- Implement fleet_cancel_query tool
- Add tests for cancellation scenarios
- Update documentation
```

## Pull Request Process

1. Fork the repository and create a new branch
2. Make your changes and ensure all tests pass
3. Run pre-commit hooks: `uv run pre-commit run --all-files`
4. Commit your changes with clear messages
5. Push to your fork and create a pull request
6. Ensure CI checks pass
7. Wait for review and address any feedback

## Questions or Issues?

If you have questions or run into issues:

- Check existing [GitHub Issues](https://github.com/SimplyMinimal/fleet-mcp/issues)
- Create a new issue with a clear description
- Join the discussion in pull requests

Thank you for contributing! 🎉
