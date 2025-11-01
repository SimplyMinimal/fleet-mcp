"""Test data fixtures for Fleet MCP tests.

This module provides synthetic test data for use in unit and integration tests.
All data is clearly fake and does not represent any real Fleet instance.
"""

# Synthetic host identifiers for testing
TEST_HOSTS = {
    "laptop": {
        "id": 123,
        "hostname": "test-laptop-001.example.com",
        "uuid": "12345678-1234-1234-1234-123456789abc",
        "hardware_serial": "TEST-SN-001",
        "status": "online",
    },
    "workstation": {
        "id": 456,
        "hostname": "test-workstation-002.example.com",
        "uuid": "87654321-4321-4321-4321-cba987654321",
        "hardware_serial": "TEST-SN-002",
        "status": "online",
    },
    "server": {
        "id": 789,
        "hostname": "test-server-003.example.com",
        "uuid": "abcdef12-3456-7890-abcd-ef1234567890",
        "hardware_serial": "",  # Empty serial (common for VMs)
        "status": "online",
    },
    "offline": {
        "id": 999,
        "hostname": "test-offline-004.example.com",
        "uuid": "99999999-9999-9999-9999-999999999999",
        "hardware_serial": "TEST-SN-999",
        "status": "offline",
    },
}

# Synthetic encryption keys for testing
TEST_ENCRYPTION_KEYS = {
    "valid": "TEST-KEY-ABC123-DEF456-GHI789",
    "invalid": None,
}

# Synthetic query results for testing
TEST_QUERY_RESULTS = {
    "system_info": [
        {
            "hostname": "test-laptop-001.example.com",
            "cpu_brand": "Test CPU Brand",
            "cpu_physical_cores": "4",
            "physical_memory": "16000000000",
        }
    ],
    "os_version": [
        {
            "name": "Test OS",
            "version": "1.0.0",
            "major": "1",
            "minor": "0",
            "patch": "0",
        }
    ],
    "processes": [
        {"name": "test-process-1", "pid": "1001"},
        {"name": "test-process-2", "pid": "1002"},
        {"name": "test-process-3", "pid": "1003"},
    ],
}

# Synthetic error messages for testing
TEST_ERROR_MESSAGES = {
    "not_found": "Resource Not Found",
    "forbidden": "Forbidden - insufficient permissions",
    "bad_request": "Bad Request - invalid parameters",
    "server_error": "Internal Server Error",
}

# Nonexistent identifiers for negative testing
NONEXISTENT_IDENTIFIERS = {
    "hostname": "nonexistent-host-12345.example.com",
    "uuid": "00000000-0000-0000-0000-000000000000",
    "serial": "NONEXISTENT-SERIAL-999",
}


def get_test_host(host_type: str = "laptop") -> dict:
    """Get a test host by type.

    Args:
        host_type: Type of host to get (laptop, workstation, server, offline)

    Returns:
        Dictionary containing test host data
    """
    return TEST_HOSTS.get(host_type, TEST_HOSTS["laptop"]).copy()


def get_test_query_result(query_type: str = "system_info") -> list:
    """Get test query results by type.

    Args:
        query_type: Type of query result to get (system_info, os_version, processes)

    Returns:
        List of dictionaries containing test query results
    """
    return TEST_QUERY_RESULTS.get(query_type, TEST_QUERY_RESULTS["system_info"]).copy()
