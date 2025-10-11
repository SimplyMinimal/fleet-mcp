"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import shared fixtures so they're available to all tests
from tests.fixtures.fleet_fixtures import (
    test_fleet_config,
    test_fleet_config_write_mode,
    test_fleet_client,
    live_fleet_config,
    live_fleet_client,
    sample_host_data,
    sample_query_data,
    sample_policy_data,
)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", 
        "unit: marks tests as unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", 
        "integration: marks tests as integration tests (require Fleet server)"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow running"
    )


@pytest.fixture(scope="session")
def fleet_server_available():
    """Check if Fleet server is available for integration tests.
    
    This can be used to skip integration tests if the server is not available.
    """
    import os
    import httpx
    
    server_url = os.getenv("FLEET_SERVER_URL", "http://192.168.68.125:1337")
    
    try:
        # Quick connectivity check
        response = httpx.get(f"{server_url}/healthz", timeout=5.0)
        return response.status_code in [200, 401, 404]  # Server is responding
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on their location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

