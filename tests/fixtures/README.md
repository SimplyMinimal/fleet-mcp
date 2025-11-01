# Test Fixtures

This directory contains shared test fixtures and synthetic test data for Fleet MCP tests.

## Purpose

The fixtures in this directory provide:

1. **Synthetic test data** that is clearly fake and does not represent any real Fleet instance
2. **Consistent test data** across all unit tests
3. **Easy maintenance** - update test data in one place
4. **Security** - no sensitive infrastructure details exposed in the codebase

## Files

### `test_data.py`

Contains synthetic test data including:

- **TEST_HOSTS**: Dictionary of test host configurations
  - `laptop`: Standard laptop configuration (ID: 123)
  - `workstation`: Workstation configuration (ID: 456)
  - `server`: Server/VM configuration with empty serial (ID: 789)
  - `offline`: Offline host for testing offline scenarios (ID: 999)

- **TEST_ENCRYPTION_KEYS**: Synthetic encryption keys for testing

- **TEST_QUERY_RESULTS**: Mock query results for different osquery tables

- **TEST_ERROR_MESSAGES**: Standard error messages for testing error handling

- **NONEXISTENT_IDENTIFIERS**: Identifiers that should not exist, for negative testing

### Helper Functions

- `get_test_host(host_type)`: Get a copy of a test host by type
- `get_test_query_result(query_type)`: Get a copy of test query results by type

## Usage

### In Unit Tests

```python
from tests.fixtures import TEST_HOSTS, get_test_host, get_test_query_result

# Get a test host
test_host = get_test_host("laptop")

# Use in mock responses
mock_response = FleetResponse(
    success=True,
    data={
        "host": {
            "id": test_host["id"],
            "hostname": test_host["hostname"],
            "uuid": test_host["uuid"],
            "hardware_serial": test_host["hardware_serial"],
        }
    },
)
```

### In Integration Tests

Integration tests should **NOT** use hardcoded test data. Instead, they should:

1. **Fetch data dynamically** from the live Fleet instance at test runtime
2. **Select test subjects** from the returned data (e.g., first online host)
3. **Skip tests** if no suitable hosts are available

Example:

```python
async def test_query_by_hostname(self, live_fleet_client):
    """Test querying a host by hostname against live Fleet instance."""
    async with live_fleet_client:
        # Fetch hosts dynamically
        response = await live_fleet_client.get("/hosts")
        hosts = response.data.get("hosts", [])
        online_hosts = [h for h in hosts if h.get("status") == "online"]
        
        if not online_hosts:
            pytest.skip("No online hosts available")
        
        # Use the first available online host
        test_host = online_hosts[0]
        hostname = test_host.get("hostname")
        
        # Run test with dynamic data
        ...
```

## Test Data Characteristics

All test data in this directory is:

- **Clearly synthetic**: Uses obvious placeholder values
  - Hostnames: `test-*.example.com`
  - UUIDs: Simple patterns like `12345678-1234-1234-1234-123456789abc`
  - Serial numbers: `TEST-SN-001`, `TEST-SN-002`, etc.
  - Host IDs: Simple integers like `123`, `456`, `789`

- **Not based on real data**: Does not represent any actual Fleet instance

- **Portable**: Works across different Fleet instances without modification

## Adding New Test Data

When adding new test data:

1. **Use obviously fake values**: Make it clear the data is synthetic
2. **Follow the naming pattern**: Use `test-*`, `TEST-*`, or simple sequential patterns
3. **Document the purpose**: Add comments explaining what the data represents
4. **Update this README**: Document any new fixtures or helper functions

## Security Note

**Never commit real Fleet instance data to this repository**, including:

- Real hostnames from your infrastructure
- Real UUIDs from actual devices
- Real serial numbers
- Real API tokens or credentials
- Real IP addresses or network information

If you need to test with real data, use integration tests that fetch data dynamically at runtime.

