"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

import pytest

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import shared fixtures so they're available to all tests
from tests.fixtures.fleet_fixtures import (  # noqa: F401
    live_fleet_client,
    live_fleet_config,
    sample_host_data,
    sample_policy_data,
    sample_query_data,
    test_fleet_client,
    test_fleet_config,
    test_fleet_config_write_mode,
)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (require Fleet server)",
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")


@pytest.fixture(scope="session")
def fleet_server_available():
    """Check if Fleet server is available for integration tests.

    This can be used to skip integration tests if the server is not available.
    Reads server URL from environment variables or .env file.
    """
    import os

    import httpx
    from dotenv import load_dotenv

    # Load .env file explicitly for tests
    load_dotenv()

    server_url = os.getenv("FLEET_SERVER_URL", "http://192.168.68.125:1337")
    verify_ssl = os.getenv("FLEET_VERIFY_SSL", "true").lower() in ("true", "1", "yes")

    try:
        # Quick connectivity check
        response = httpx.get(f"{server_url}/healthz", timeout=5.0, verify=verify_ssl)
        return response.status_code in [200, 401, 404]  # Server is responding
    except Exception:
        return False


@pytest.fixture(autouse=True)
def reset_table_cache():
    """Reset the global table schema cache before and after each test.

    This ensures that tests don't interfere with each other by leaving
    cached data or mock patches in place. This is especially important
    for tests that patch the cache file path or global cache instance.
    """
    import fleet_mcp.tools.table_discovery as td

    # Save original cache
    original_cache = td._table_cache

    # Reset before test
    td._table_cache = None

    yield

    # Reset after test
    td._table_cache = original_cache


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on their location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
