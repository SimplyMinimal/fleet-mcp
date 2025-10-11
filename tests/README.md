# Fleet MCP Test Suite

This directory contains the test suite for Fleet MCP, organized into unit tests and integration tests.

## Test Organization

```
tests/
├── unit/                    # Unit tests (fast, isolated, no external dependencies)
│   ├── test_client.py      # Fleet API client tests
│   ├── test_config.py      # Configuration validation tests
│   └── test_readonly_mode.py  # Read-only mode configuration tests
│
├── integration/            # Integration tests (require Fleet server)
│   ├── test_readonly_mode_integration.py  # Read-only mode functionality tests
│   ├── test_dynamic_tables.py            # Dynamic table discovery tests
│   └── test_simple_discovery.py          # Basic connectivity tests
│
├── fixtures/               # Shared test fixtures
│   └── fleet_fixtures.py  # Common fixtures for all tests
│
└── conftest.py            # Pytest configuration and shared setup
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Only Unit Tests (Fast)

Unit tests are fast and don't require a Fleet server:

```bash
# Using marker
pytest -m unit

# Using path
pytest tests/unit/
```

### Run Only Integration Tests

Integration tests require a running Fleet server:

```bash
# Using marker
pytest -m integration

# Using path
pytest tests/integration/
```

### Run Specific Test File

```bash
pytest tests/unit/test_config.py
pytest tests/integration/test_dynamic_tables.py
```

### Run Specific Test

```bash
pytest tests/unit/test_config.py::TestFleetConfig::test_valid_config
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=fleet_mcp --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run with Verbose Output

```bash
pytest -v
pytest -vv  # Extra verbose
```

## Test Categories

### Unit Tests

**Purpose**: Fast, isolated tests that verify individual components work correctly.

**Characteristics**:
- No external dependencies (Fleet server, network, etc.)
- Use mocks and fixtures
- Run in milliseconds
- Should always pass regardless of environment

**Examples**:
- Configuration validation
- URL normalization
- Error handling
- Data parsing

**Location**: `tests/unit/`

### Integration Tests

**Purpose**: Verify that components work together correctly with real dependencies.

**Characteristics**:
- Require running Fleet server
- May require specific test data
- Slower execution
- May be skipped if dependencies unavailable

**Examples**:
- Live host queries
- Table discovery from real hosts
- API endpoint integration
- End-to-end workflows

**Location**: `tests/integration/`

## Configuration for Integration Tests

Integration tests require a Fleet server. Configure using environment variables:

```bash
export FLEET_SERVER_URL="http://your-fleet-server:1337"
export FLEET_API_TOKEN="your-api-token"
```

Or create a `fleet-mcp.toml` configuration file in the project root.

### Test Host Requirements

Some integration tests expect specific test hosts:
- Host ID 6: CentOS/RHEL host for Linux-specific tests
- Hosts 3-6: General test hosts

Adjust host IDs in test files if your environment differs.

## Writing Tests

### Unit Test Example

```python
import pytest
from fleet_mcp.config import FleetConfig

@pytest.mark.unit
class TestMyFeature:
    def test_something(self, test_fleet_config):
        """Test description."""
        # Arrange
        config = test_fleet_config
        
        # Act
        result = some_function(config)
        
        # Assert
        assert result == expected_value
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
class TestMyIntegration:
    async def test_live_operation(self, live_fleet_client):
        """Test description."""
        try:
            async with live_fleet_client:
                result = await live_fleet_client.get("/hosts")
                assert result.success
        except Exception as e:
            pytest.skip(f"Test skipped: {e}")
```

## Available Fixtures

Fixtures are defined in `tests/conftest.py` and `tests/fixtures/fleet_fixtures.py`:

### Unit Test Fixtures

- `test_fleet_config`: Mock Fleet configuration (readonly=True)
- `test_fleet_config_write_mode`: Mock Fleet configuration (readonly=False)
- `test_fleet_client`: Mock Fleet client
- `sample_host_data`: Sample host data for testing
- `sample_query_data`: Sample query data for testing
- `sample_policy_data`: Sample policy data for testing

### Integration Test Fixtures

- `live_fleet_config`: Real Fleet server configuration
- `live_fleet_client`: Real Fleet client connected to server
- `fleet_server_available`: Check if Fleet server is available

## Test Markers

Tests are automatically marked based on their location:

- `@pytest.mark.unit`: Unit tests (in `tests/unit/`)
- `@pytest.mark.integration`: Integration tests (in `tests/integration/`)
- `@pytest.mark.slow`: Slow running tests
- `@pytest.mark.asyncio`: Async tests (auto-applied)

## Continuous Integration

### GitHub Actions (Recommended)

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest -m unit --cov=fleet_mcp
      
  integration-tests:
    runs-on: ubuntu-latest
    # Only run if Fleet server is available
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest -m integration
        env:
          FLEET_SERVER_URL: ${{ secrets.FLEET_SERVER_URL }}
          FLEET_API_TOKEN: ${{ secrets.FLEET_API_TOKEN }}
```

## Troubleshooting

### Integration Tests Failing

**Problem**: Integration tests fail with connection errors.

**Solution**: 
1. Verify Fleet server is running: `curl http://your-fleet-server:1337/healthz`
2. Check environment variables are set correctly
3. Verify API token has correct permissions
4. Check test host IDs match your environment

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'fleet_mcp'`

**Solution**:
1. Install package in development mode: `pip install -e .`
2. Or ensure `conftest.py` is adding src to path

### Async Test Warnings

**Problem**: Warnings about async tests not being awaited.

**Solution**: Ensure `pytest-asyncio` is installed and `asyncio_mode = "auto"` is in `pyproject.toml`.

## Best Practices

1. **Keep unit tests fast**: Mock external dependencies
2. **Make integration tests resilient**: Use `pytest.skip()` when dependencies unavailable
3. **Use descriptive test names**: Test name should describe what is being tested
4. **One assertion per test**: Makes failures easier to diagnose
5. **Use fixtures**: Avoid code duplication
6. **Clean up after tests**: Use fixtures with cleanup or context managers
7. **Document test requirements**: Note any special setup needed

## Coverage Goals

- **Unit tests**: Aim for >90% coverage of core logic
- **Integration tests**: Cover critical user workflows
- **Overall**: Maintain >80% total coverage

Check current coverage:

```bash
pytest --cov=fleet_mcp --cov-report=term-missing
```

