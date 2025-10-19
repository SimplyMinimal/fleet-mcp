"""Unit tests for the Fleet MCP Server health check functionality."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from fleet_mcp.config import FleetConfig
from fleet_mcp.server import FleetMCPServer


class TestServerHealthCheck:
    """Test suite for server health check functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Fleet configuration."""
        return FleetConfig(
            server_url="https://test.fleet.com", api_token="test-token-123456789"
        )

    @pytest.mark.asyncio
    async def test_health_check_tool_registered(self, mock_config):
        """Test that health check tool is registered."""
        server = FleetMCPServer(mock_config)
        tools = await server.mcp.list_tools()
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]

        assert "fleet_health_check" in tool_names

    @pytest.mark.asyncio
    async def test_get_cache_info_with_cache(self, tmp_path):
        """Test _get_cache_info with existing cache."""
        # Create a mock cache file
        cache_dir = tmp_path / ".fleet-mcp" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "osquery_fleet_schema.json"

        # Write mock schema data
        mock_schema = {
            "processes": {
                "description": "All running processes",
                "platforms": ["darwin", "linux", "windows"],
                "columns": [{"name": "pid", "type": "bigint"}],
            },
            "users": {
                "description": "Local user accounts",
                "platforms": ["darwin", "linux", "windows"],
                "columns": [{"name": "uid", "type": "bigint"}],
            },
        }
        with open(cache_file, "w") as f:
            json.dump(mock_schema, f)

        # Mock the cache file path
        with patch(
            "fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", cache_file
        ), patch("fleet_mcp.tools.table_discovery.CACHE_DIR", cache_dir):
            cache_info = await FleetMCPServer._get_cache_info()

            # Verify cache info structure
            assert cache_info["cached"] is True
            assert cache_info["cache_file_path"] == str(cache_file)
            assert cache_info["file_size_bytes"] > 0
            assert cache_info["file_size_human"] is not None
            assert cache_info["tables_loaded"] == 2  # processes and users
            assert cache_info["cache_age_seconds"] is not None
            assert cache_info["cache_age_hours"] is not None
            assert cache_info["cache_valid"] is True
            assert cache_info["cache_ttl_hours"] == 24
            assert "ago" in cache_info["last_modified"]

    @pytest.mark.asyncio
    async def test_get_cache_info_no_cache(self, tmp_path):
        """Test _get_cache_info when cache doesn't exist."""
        # Use a non-existent cache file
        cache_dir = tmp_path / ".fleet-mcp" / "cache"
        cache_file = cache_dir / "osquery_fleet_schema.json"

        with patch(
            "fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", cache_file
        ), patch("fleet_mcp.tools.table_discovery.CACHE_DIR", cache_dir):
            # Mock the schema download to fail (so we don't create cache)
            with patch(
                "fleet_mcp.tools.table_discovery.TableSchemaCache._download_fleet_schema",
                side_effect=Exception("Download failed"),
            ):
                cache_info = await FleetMCPServer._get_cache_info()

                # Verify cache information shows no cache
                assert cache_info["cached"] is False
                assert cache_info["file_size_bytes"] is None
                assert cache_info["cache_age_seconds"] is None
                assert cache_info["cache_valid"] is False

    def test_format_bytes_helper(self):
        """Test the _format_bytes helper function."""
        # Test various sizes
        assert FleetMCPServer._format_bytes(None) == "N/A"
        assert FleetMCPServer._format_bytes(0) == "0 B"
        assert FleetMCPServer._format_bytes(500) == "500.00 B"
        assert FleetMCPServer._format_bytes(1024) == "1.00 KB"
        assert FleetMCPServer._format_bytes(1536) == "1.50 KB"
        assert FleetMCPServer._format_bytes(1048576) == "1.00 MB"
        assert FleetMCPServer._format_bytes(1572864) == "1.50 MB"
        assert FleetMCPServer._format_bytes(1073741824) == "1.00 GB"

    @pytest.mark.asyncio
    async def test_get_cache_info_error_handling(self):
        """Test that _get_cache_info handles errors gracefully."""
        # Mock get_table_cache to raise an exception
        with patch(
            "fleet_mcp.tools.table_discovery.get_table_cache",
            side_effect=Exception("Cache error"),
        ):
            cache_info = await FleetMCPServer._get_cache_info()

            # Should return error info instead of crashing
            assert cache_info["cached"] is False
            assert "error" in cache_info
            assert "Cache error" in cache_info["error"]
            assert "message" in cache_info

