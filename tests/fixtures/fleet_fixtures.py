"""Shared test fixtures for Fleet MCP tests."""

import pytest

from fleet_mcp.client import FleetClient
from fleet_mcp.config import FleetConfig


@pytest.fixture
def test_fleet_config():
    """Create a test Fleet configuration for unit tests.

    This uses a fake server URL and token for testing purposes.
    Default to readonly mode for safety.
    """
    return FleetConfig(
        server_url="https://test.fleet.com",
        api_token="test-token-123456789",
        readonly=True,
    )


@pytest.fixture
def test_fleet_config_write_mode():
    """Create a test Fleet configuration with write mode enabled.

    This uses a fake server URL and token for testing purposes.
    """
    return FleetConfig(
        server_url="https://test.fleet.com",
        api_token="test-token-123456789",
        readonly=False,
    )


@pytest.fixture
def test_fleet_client(test_fleet_config):
    """Create a test Fleet client for unit tests.

    Uses the test configuration with mocked server.
    """
    return FleetClient(test_fleet_config)


@pytest.fixture
def live_fleet_config():
    """Configuration for live Fleet server (integration tests).

    This should be configured with actual Fleet server credentials.
    Default to readonly mode for safety in tests.

    Reads from environment variables or .env file via pydantic-settings.
    Uses dotenv_values() to avoid polluting the global environment.
    """
    import os

    from dotenv import dotenv_values

    # Load .env file values without setting environment variables
    # This prevents pollution of the global environment that could affect other tests
    env_values = dotenv_values()

    # Get values from environment first, then fall back to .env file values
    def get_env(key: str, default: str) -> str:
        return os.getenv(key) or env_values.get(key, default)

    # Now create config from environment variables
    return FleetConfig(
        server_url=get_env("FLEET_SERVER_URL", "http://192.168.68.125:1337"),
        api_token=get_env(
            "FLEET_API_TOKEN",
            "+nHwmPaf7wSt9sg8qvNX0/LDL26TdM6wxXYD/4W9tfzmNeq+5GWBzmR15Oq6GpMgGzkLpPcH3vq4i9pXi/+lLw==",
        ),
        readonly=get_env("FLEET_READONLY", "true").lower() in ("true", "1", "yes"),
        verify_ssl=get_env("FLEET_VERIFY_SSL", "true").lower() in ("true", "1", "yes"),
    )


@pytest.fixture
def live_fleet_client(live_fleet_config):
    """Create a Fleet client connected to live server (integration tests).

    Uses the live Fleet server configuration.
    """
    return FleetClient(live_fleet_config)


@pytest.fixture
def sample_host_data():
    """Sample host data for testing."""
    return {
        "id": 1,
        "hostname": "test-host",
        "uuid": "test-uuid-123",
        "platform": "ubuntu",
        "osquery_version": "5.17.0",
        "status": "online",
    }


@pytest.fixture
def sample_query_data():
    """Sample query data for testing."""
    return {
        "id": 1,
        "name": "Test Query",
        "description": "A test query",
        "query": "SELECT * FROM system_info;",
        "saved": True,
    }


@pytest.fixture
def sample_policy_data():
    """Sample policy data for testing."""
    return {
        "id": 1,
        "name": "Test Policy",
        "description": "A test policy",
        "query": "SELECT 1;",
        "critical": False,
        "passing_host_count": 5,
        "failing_host_count": 2,
    }
