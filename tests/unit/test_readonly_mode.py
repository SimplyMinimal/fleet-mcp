"""Tests for read-only mode functionality."""

import os
from unittest.mock import patch

import pytest

from fleet_mcp.config import FleetConfig
from fleet_mcp.server import FleetMCPServer


@pytest.fixture(autouse=True)
def isolate_env_vars():
    """Isolate tests from environment variables.

    This ensures unit tests aren't affected by environment variables
    that might be set in the shell or loaded from .env files.
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


@pytest.mark.unit
class TestReadOnlyMode:
    """Test read-only mode configuration and behavior."""

    def test_readonly_config_default(self):
        """Test that readonly defaults to True (safe by default)."""
        config = FleetConfig(
            server_url="https://test.example.com", api_token="test-token"
        )
        assert config.readonly is True

    def test_readonly_config_explicit_true(self):
        """Test setting readonly to True explicitly."""
        config = FleetConfig(
            server_url="https://test.example.com", api_token="test-token", readonly=True
        )
        assert config.readonly is True

    def test_readonly_config_explicit_false(self):
        """Test setting readonly to False explicitly."""
        config = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token",
            readonly=False,
        )
        assert config.readonly is False

    @patch.dict(
        "os.environ",
        {
            "FLEET_READONLY": "true",
            "FLEET_SERVER_URL": "https://test.example.com",
            "FLEET_API_TOKEN": "test-token",
        },
        clear=True,
    )
    def test_readonly_from_env_true(self):
        """Test setting readonly via environment variable (true)."""
        config = FleetConfig()
        assert config.readonly is True

    def test_allow_select_queries_config_default(self):
        """Test that allow_select_queries defaults to False."""
        config = FleetConfig(
            server_url="https://test.example.com", api_token="test-token"
        )
        assert config.allow_select_queries is False

    def test_allow_select_queries_config_explicit_true(self):
        """Test setting allow_select_queries to True explicitly."""
        config = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token",
            allow_select_queries=True,
        )
        assert config.allow_select_queries is True

    def test_allow_select_queries_config_explicit_false(self):
        """Test setting allow_select_queries to False explicitly."""
        config = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token",
            allow_select_queries=False,
        )
        assert config.allow_select_queries is False

    @patch.dict(
        "os.environ",
        {
            "FLEET_ALLOW_SELECT_QUERIES": "true",
            "FLEET_SERVER_URL": "https://test.example.com",
            "FLEET_API_TOKEN": "test-token",
        },
        clear=True,
    )
    def test_allow_select_queries_from_env_true(self):
        """Test setting allow_select_queries via environment variable (true)."""
        config = FleetConfig()
        assert config.allow_select_queries is True

    @patch.dict(
        "os.environ",
        {
            "FLEET_ALLOW_SELECT_QUERIES": "false",
            "FLEET_SERVER_URL": "https://test.example.com",
            "FLEET_API_TOKEN": "test-token",
        },
        clear=True,
    )
    def test_allow_select_queries_from_env_false(self):
        """Test setting allow_select_queries via environment variable (false)."""
        config = FleetConfig()
        assert config.allow_select_queries is False

    @patch.dict(
        "os.environ",
        {
            "FLEET_READONLY": "false",
            "FLEET_SERVER_URL": "https://test.example.com",
            "FLEET_API_TOKEN": "test-token",
        },
        clear=True,
    )
    def test_readonly_from_env_false(self):
        """Test setting readonly via environment variable (false)."""
        config = FleetConfig()
        assert config.readonly is False

    @patch.dict(
        "os.environ",
        {
            "FLEET_READONLY": "1",
            "FLEET_SERVER_URL": "https://test.example.com",
            "FLEET_API_TOKEN": "test-token",
        },
        clear=True,
    )
    def test_readonly_from_env_truthy(self):
        """Test setting readonly via environment variable (truthy value)."""
        config = FleetConfig()
        assert config.readonly is True

    @patch.dict(
        "os.environ",
        {
            "FLEET_READONLY": "0",
            "FLEET_SERVER_URL": "https://test.example.com",
            "FLEET_API_TOKEN": "test-token",
        },
        clear=True,
    )
    def test_readonly_from_env_falsy(self):
        """Test setting readonly via environment variable (falsy value)."""
        config = FleetConfig()
        assert config.readonly is False

    def test_readonly_server_name(self):
        """Test that readonly mode affects server name."""
        config = FleetConfig(
            server_url="https://test.example.com", api_token="test-token", readonly=True
        )

        with patch("fleet_mcp.server.FleetClient"):
            server = FleetMCPServer(config)
            assert "READ-ONLY MODE" in server.mcp.name

    def test_normal_server_name(self):
        """Test that normal mode doesn't include readonly indicator."""
        config = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token",
            readonly=False,
        )

        with patch("fleet_mcp.server.FleetClient"):
            server = FleetMCPServer(config)
            assert "READ-ONLY MODE" not in server.mcp.name

    def test_readonly_server_instructions(self):
        """Test that readonly mode affects server instructions."""
        config = FleetConfig(
            server_url="https://test.example.com", api_token="test-token", readonly=True
        )

        with patch("fleet_mcp.server.FleetClient"):
            server = FleetMCPServer(config)
            assert server.mcp.instructions is not None
            assert "READ-ONLY" in server.mcp.instructions
            assert (
                "No create, update, delete, or query execution operations are available"
                in server.mcp.instructions
            )

    def test_normal_server_instructions(self):
        """Test that normal mode doesn't mention readonly restrictions."""
        config = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token",
            readonly=False,
        )

        with patch("fleet_mcp.server.FleetClient"):
            server = FleetMCPServer(config)
            assert server.mcp.instructions is not None
            assert "READ-ONLY" not in server.mcp.instructions
            assert (
                "No create, update, or delete operations are available"
                not in server.mcp.instructions
            )
