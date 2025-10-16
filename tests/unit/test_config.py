"""Tests for Fleet MCP configuration."""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from fleet_mcp.config import FleetConfig, load_config


@pytest.fixture(autouse=True)
def isolate_env_vars():
    """Isolate tests from .env file by clearing Fleet-related env vars.

    This ensures unit tests aren't affected by the .env file in the project root.
    """
    # Save original values
    original_env = {}
    fleet_vars = [
        "FLEET_SERVER_URL",
        "FLEET_API_TOKEN",
        "FLEET_VERIFY_SSL",
        "FLEET_TIMEOUT",
        "FLEET_MAX_RETRIES",
        "FLEET_READONLY",
        "FLEET_ALLOW_SELECT_QUERIES",
    ]

    for var in fleet_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_env.items():
        os.environ[var] = value


class TestFleetConfig:
    """Test FleetConfig validation and loading."""

    def test_valid_config(self):
        """Test creating a valid configuration."""
        config = FleetConfig(
            server_url="https://fleet.example.com", api_token="test-token-123456789"
        )

        assert config.server_url == "https://fleet.example.com"
        assert config.api_token == "test-token-123456789"
        assert config.verify_ssl is True
        assert config.timeout == 30

    def test_server_url_normalization(self):
        """Test server URL normalization."""
        # Test adding https://
        config = FleetConfig(
            server_url="fleet.example.com", api_token="test-token-123456789"
        )
        assert config.server_url == "https://fleet.example.com"

        # Test removing trailing slash
        config = FleetConfig(
            server_url="https://fleet.example.com/", api_token="test-token-123456789"
        )
        assert config.server_url == "https://fleet.example.com"

    def test_invalid_server_url(self):
        """Test invalid server URL validation."""
        with pytest.raises(ValidationError):
            FleetConfig(server_url="", api_token="test-token-123456789")

    def test_invalid_api_token(self):
        """Test invalid API token validation."""
        with pytest.raises(ValidationError):
            FleetConfig(server_url="https://fleet.example.com", api_token="")

        with pytest.raises(ValidationError):
            FleetConfig(server_url="https://fleet.example.com", api_token="short")

    def test_invalid_timeout(self):
        """Test invalid timeout validation."""
        with pytest.raises(ValidationError):
            FleetConfig(
                server_url="https://fleet.example.com",
                api_token="test-token-123456789",
                timeout=0,
            )

        with pytest.raises(ValidationError):
            FleetConfig(
                server_url="https://fleet.example.com",
                api_token="test-token-123456789",
                timeout=400,
            )


class TestConfigLoading:
    """Test configuration loading from environment and files."""

    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        # Set environment variables
        os.environ["FLEET_SERVER_URL"] = "https://test.fleet.com"
        os.environ["FLEET_API_TOKEN"] = "env-token-123456789"
        os.environ["FLEET_VERIFY_SSL"] = "false"
        os.environ["FLEET_TIMEOUT"] = "60"

        try:
            config = load_config()

            assert config.server_url == "https://test.fleet.com"
            assert config.api_token == "env-token-123456789"
            assert config.verify_ssl is False
            assert config.timeout == 60

        finally:
            # Clean up environment variables
            for key in [
                "FLEET_SERVER_URL",
                "FLEET_API_TOKEN",
                "FLEET_VERIFY_SSL",
                "FLEET_TIMEOUT",
            ]:
                os.environ.pop(key, None)

    def test_load_from_toml_file(self):
        """Test loading configuration from TOML file."""
        toml_content = """
[fleet]
server_url = "https://file.fleet.com"
api_token = "file-token-123456789"
verify_ssl = false
timeout = 45
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_file = Path(f.name)

        try:
            config = load_config(config_file)

            assert config.server_url == "https://file.fleet.com"
            assert config.api_token == "file-token-123456789"
            assert config.verify_ssl is False
            assert config.timeout == 45

        finally:
            config_file.unlink()

    def test_env_overrides_file(self):
        """Test that environment variables override file configuration."""
        toml_content = """
[fleet]
server_url = "https://file.fleet.com"
api_token = "file-token-123456789"
verify_ssl = false
timeout = 45
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            config_file = Path(f.name)

        # Set environment variable to override file
        os.environ["FLEET_SERVER_URL"] = "https://env.fleet.com"
        os.environ["FLEET_API_TOKEN"] = (
            "env-token-123456789"  # Need this for validation
        )

        try:
            config = load_config(config_file)

            # Environment should override file
            assert config.server_url == "https://env.fleet.com"
            assert config.api_token == "env-token-123456789"
            # File values should be used for non-overridden settings
            assert config.verify_ssl is False
            assert config.timeout == 45

        finally:
            config_file.unlink()
            os.environ.pop("FLEET_SERVER_URL", None)
            os.environ.pop("FLEET_API_TOKEN", None)
