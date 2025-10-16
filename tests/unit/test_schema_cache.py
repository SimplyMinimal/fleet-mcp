"""Unit tests for the Fleet schema caching functionality."""

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fleet_mcp.tools.table_discovery import (
    CACHE_DIR,
    FLEET_SCHEMA_URL,
    SCHEMA_CACHE_FILE,
    SCHEMA_CACHE_TTL,
    TableSchemaCache,
)


@pytest.fixture
def mock_schema_json():
    """Mock Fleet schema JSON data."""
    return {
        "processes": {
            "description": "All running processes on the host",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": [
                {
                    "name": "pid",
                    "type": "BIGINT",
                    "description": "Process ID",
                    "required": False,
                },
                {
                    "name": "name",
                    "type": "TEXT",
                    "description": "Process name",
                    "required": False,
                },
            ],
            "examples": "SELECT pid, name FROM processes;",
            "notes": "Some notes about processes",
        },
        "users": {
            "description": "Local user accounts",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": [
                {
                    "name": "uid",
                    "type": "BIGINT",
                    "description": "User ID",
                    "required": False,
                },
                {
                    "name": "username",
                    "type": "TEXT",
                    "description": "Username",
                    "required": False,
                },
            ],
            "examples": "SELECT * FROM users;",
            "notes": None,
        },
    }


class TestTableSchemaCache:
    """Test the TableSchemaCache class."""

    @pytest.mark.asyncio
    async def test_parse_fleet_json_schema(self, mock_schema_json):
        """Test parsing of Fleet JSON schema format."""
        cache = TableSchemaCache()
        schemas = cache._parse_fleet_json_schema(mock_schema_json)

        # Check that we got both tables
        assert "processes" in schemas
        assert "users" in schemas

        # Check processes table
        processes = schemas["processes"]
        assert processes["description"] == "All running processes on the host"
        assert processes["platforms"] == ["darwin", "linux", "windows"]
        assert processes["evented"] is False
        assert "pid" in processes["columns"]
        assert "name" in processes["columns"]
        assert processes["column_details"]["pid"]["type"] == "BIGINT"
        assert processes["column_details"]["pid"]["description"] == "Process ID"
        assert len(processes["examples"]) == 1
        assert processes["notes"] == "Some notes about processes"

        # Check users table
        users = schemas["users"]
        assert users["description"] == "Local user accounts"
        assert "uid" in users["columns"]
        assert "username" in users["columns"]
        assert users["notes"] is None

    @pytest.mark.asyncio
    async def test_download_fleet_schema(self, mock_schema_json):
        """Test downloading schema from GitHub."""
        cache = TableSchemaCache()

        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.json.return_value = mock_schema_json
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            schemas = await cache._download_fleet_schema()

            # Verify the request was made
            mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
                FLEET_SCHEMA_URL
            )

            # Verify schemas were parsed correctly
            assert "processes" in schemas
            assert "users" in schemas

    @pytest.mark.asyncio
    async def test_cache_file_operations(self, mock_schema_json, tmp_path):
        """Test saving and loading cache file."""
        # Use a temporary cache file
        test_cache_file = tmp_path / "test_schema.json"

        cache = TableSchemaCache()

        # Save mock schema to temp file
        with open(test_cache_file, "w") as f:
            json.dump(mock_schema_json, f)

        # Load from cache
        with patch(
            "fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", test_cache_file
        ):
            schemas = await cache._load_cached_schema()

            assert "processes" in schemas
            assert "users" in schemas

    @pytest.mark.asyncio
    async def test_cache_ttl_logic(self, mock_schema_json, tmp_path):
        """Test cache TTL validation."""
        test_cache_file = tmp_path / "test_schema.json"
        test_cache_dir = tmp_path

        cache = TableSchemaCache()

        # Create a fresh cache file
        with open(test_cache_file, "w") as f:
            json.dump(mock_schema_json, f)

        # Mock the cache file path
        with patch("fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", test_cache_file):
            with patch("fleet_mcp.tools.table_discovery.CACHE_DIR", test_cache_dir):
                # Test with fresh cache (should load from cache)
                await cache._load_fleet_schemas(force_refresh=False)
                assert len(cache.fleet_schemas) == 2

                # Verify cache was used (not downloaded)
                # We can check this by verifying no HTTP calls were made
                # This is implicit in the test - if download was attempted, it would fail

    @pytest.mark.asyncio
    async def test_force_refresh(self, mock_schema_json, tmp_path):
        """Test force refresh bypasses cache."""
        test_cache_file = tmp_path / "test_schema.json"
        test_cache_dir = tmp_path

        cache = TableSchemaCache()

        # Create a cache file
        with open(test_cache_file, "w") as f:
            json.dump({"old_table": {"description": "Old"}}, f)

        # Mock HTTP client to return new schema
        mock_response = MagicMock()
        mock_response.json.return_value = mock_schema_json
        mock_response.raise_for_status = MagicMock()

        with patch("fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", test_cache_file):
            with patch("fleet_mcp.tools.table_discovery.CACHE_DIR", test_cache_dir):
                with patch("httpx.AsyncClient") as mock_client:
                    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                        return_value=mock_response
                    )

                    # Force refresh should download new schema
                    await cache._load_fleet_schemas(force_refresh=True)

                    # Should have new schema, not old
                    assert "processes" in cache.fleet_schemas
                    assert "users" in cache.fleet_schemas
                    assert "old_table" not in cache.fleet_schemas

    @pytest.mark.asyncio
    async def test_fallback_to_bundled_schemas(self, tmp_path):
        """Test fallback to bundled schemas when download fails and no cache exists."""
        test_cache_file = tmp_path / "nonexistent.json"
        test_cache_dir = tmp_path

        cache = TableSchemaCache()

        # Mock HTTP client to fail
        with patch("fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", test_cache_file):
            with patch("fleet_mcp.tools.table_discovery.CACHE_DIR", test_cache_dir):
                with patch("httpx.AsyncClient") as mock_client:
                    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                        side_effect=Exception("Network error")
                    )

                    # Should fall back to bundled schemas
                    await cache._load_fleet_schemas(force_refresh=False)

                    # Should have bundled schemas
                    assert "rpm_packages" in cache.fleet_schemas
                    assert "processes" in cache.fleet_schemas

    @pytest.mark.asyncio
    async def test_get_cache_info(self, tmp_path):
        """Test cache info retrieval."""
        test_cache_file = tmp_path / "test_schema.json"

        cache = TableSchemaCache()
        cache.fleet_schemas = {"test_table": {}}

        # Create a cache file
        with open(test_cache_file, "w") as f:
            json.dump({"test": "data"}, f)

        with patch("fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", test_cache_file):
            info = cache.get_cache_info()

            assert info["cache_exists"] is True
            assert info["cache_age_seconds"] is not None
            assert info["cache_size_bytes"] > 0
            assert info["loaded_schemas_count"] == 1
            assert info["cache_ttl_hours"] == 24

    @pytest.mark.asyncio
    async def test_refresh_fleet_schemas(self, mock_schema_json):
        """Test manual schema refresh."""
        cache = TableSchemaCache()

        # Mock HTTP client
        mock_response = MagicMock()
        mock_response.json.return_value = mock_schema_json
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Refresh should succeed
            result = await cache.refresh_fleet_schemas()
            assert result is True
            assert len(cache.fleet_schemas) == 2

