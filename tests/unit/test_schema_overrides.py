"""Unit tests for Fleet schema override functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from fleet_mcp.tools.table_discovery import (
    TableSchemaCache,
)


@pytest.fixture
def mock_override_yaml():
    """Mock Fleet schema override YAML data."""
    return {
        "vscode_extensions": {
            "name": "vscode_extensions",
            "description": "Installed extensions for Visual Studio Code",
            "notes": "Querying this table requires joining against the `users` table. [Learn more](https://fleetdm.com/guides/osquery-consider-joining-against-the-users-table)",
            "examples": [
                "SELECT * FROM users CROSS JOIN vscode_extensions USING (uid);",
                "SELECT extension.name, extension.publisher, extension.version FROM users JOIN vscode_extensions extension USING (uid);",
            ],
        },
        "chrome_extensions": {
            "name": "chrome_extensions",
            "description": "Chrome extensions installed in Chromium browsers",
            "notes": "Querying this table requires joining against the `users` table. On ChromeOS, this table requires the fleetd Chrome extension.",
            "examples": [
                "SELECT * FROM users CROSS JOIN chrome_extensions USING (uid);",
                "SELECT u.username, ce.name FROM users u INNER JOIN chrome_extensions ce USING (uid);",
            ],
        },
    }


@pytest.fixture
def mock_base_schema():
    """Mock base Fleet schema."""
    return {
        "vscode_extensions": {
            "description": "Installed extensions for Visual Studio Code",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": ["name", "uuid", "version", "uid"],
            "column_details": {},
            "examples": [],
            "notes": None,
        },
        "chrome_extensions": {
            "description": "Chrome extensions",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": ["uid", "name", "version"],
            "column_details": {},
            "examples": [],
            "notes": None,
        },
        "processes": {
            "description": "Running processes",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": ["pid", "name"],
            "column_details": {},
            "examples": [],
            "notes": None,
        },
    }


class TestSchemaOverrides:
    """Test schema override functionality."""

    @pytest.mark.asyncio
    async def test_merge_overrides_with_schema(
        self, mock_base_schema, mock_override_yaml
    ):
        """Test merging override data with base schema."""
        cache = TableSchemaCache()
        cache.fleet_schemas = mock_base_schema
        cache.schema_overrides = mock_override_yaml

        # Merge vscode_extensions
        merged = cache._merge_overrides_with_schema(
            "vscode_extensions", mock_base_schema["vscode_extensions"]
        )

        assert merged["has_overrides"] is True
        assert merged["override_source"] == "fleet_yaml"
        assert "override_notes" in merged
        assert "Querying this table requires joining" in merged["override_notes"]
        assert "override_examples" in merged
        assert len(merged["override_examples"]) == 2

    @pytest.mark.asyncio
    async def test_merge_without_overrides(self, mock_base_schema):
        """Test merging when no overrides exist."""
        cache = TableSchemaCache()
        cache.fleet_schemas = mock_base_schema
        cache.schema_overrides = {}

        # Merge processes (no override)
        merged = cache._merge_overrides_with_schema(
            "processes", mock_base_schema["processes"]
        )

        assert "has_overrides" not in merged or merged.get("has_overrides") is False
        assert "override_notes" not in merged
        assert "override_examples" not in merged

    @pytest.mark.asyncio
    async def test_load_cached_overrides(self, tmp_path, mock_override_yaml):
        """Test loading overrides from cache file."""
        test_cache_file = tmp_path / "test_overrides.json"

        # Write mock overrides to temp file
        with open(test_cache_file, "w") as f:
            json.dump(mock_override_yaml, f)

        cache = TableSchemaCache()

        # Load from cache
        with patch(
            "fleet_mcp.tools.table_discovery.SCHEMA_OVERRIDES_CACHE_FILE",
            test_cache_file,
        ):
            overrides = await cache._load_cached_overrides()

            assert "vscode_extensions" in overrides
            assert "chrome_extensions" in overrides
            assert (
                "Querying this table requires joining"
                in overrides["vscode_extensions"]["notes"]
            )

    @pytest.mark.asyncio
    async def test_save_overrides_cache(self, tmp_path, mock_override_yaml):
        """Test saving overrides to cache file."""
        test_cache_file = tmp_path / "test_overrides.json"

        cache = TableSchemaCache()

        with patch(
            "fleet_mcp.tools.table_discovery.SCHEMA_OVERRIDES_CACHE_FILE",
            test_cache_file,
        ):
            await cache._save_overrides_cache(mock_override_yaml)

            # Verify file was created and contains correct data
            assert test_cache_file.exists()
            with open(test_cache_file) as f:
                saved_data = json.load(f)

            assert "vscode_extensions" in saved_data
            assert saved_data["vscode_extensions"]["name"] == "vscode_extensions"

    @pytest.mark.asyncio
    async def test_get_fleet_schemas_by_platform_with_overrides(
        self, mock_base_schema, mock_override_yaml
    ):
        """Test that platform filtering includes override data."""
        cache = TableSchemaCache()
        cache.fleet_schemas = mock_base_schema
        cache.schema_overrides = mock_override_yaml

        tables = cache._get_fleet_schemas_by_platform("darwin")

        # Find vscode_extensions in results
        vscode_table = next(
            (t for t in tables if t["name"] == "vscode_extensions"), None
        )
        assert vscode_table is not None
        assert vscode_table.get("has_overrides") is True
        assert "override_notes" in vscode_table

    @pytest.mark.asyncio
    async def test_cache_info_includes_overrides(self, tmp_path, mock_override_yaml):
        """Test that cache info includes override statistics."""
        test_cache_file = tmp_path / "test_overrides.json"

        # Write mock overrides to temp file
        with open(test_cache_file, "w") as f:
            json.dump(mock_override_yaml, f)

        cache = TableSchemaCache()
        cache.schema_overrides = mock_override_yaml
        cache.overrides_source = "cache"

        with patch(
            "fleet_mcp.tools.table_discovery.SCHEMA_OVERRIDES_CACHE_FILE",
            test_cache_file,
        ):
            info = cache.get_cache_info()

            assert "loaded_overrides_count" in info
            assert info["loaded_overrides_count"] == 2
            assert "overrides_source" in info
            assert info["overrides_source"] == "cache"
            assert "overrides_cache_file" in info

    @pytest.mark.asyncio
    async def test_download_schema_overrides_with_mock(self, mock_base_schema):
        """Test downloading schema overrides with mocked HTTP responses."""
        cache = TableSchemaCache()
        cache.fleet_schemas = mock_base_schema

        # Mock HTTP responses
        mock_response_vscode = MagicMock()
        mock_response_vscode.status_code = 200
        mock_response_vscode.text = yaml.dump(
            {
                "name": "vscode_extensions",
                "notes": "Requires joining with users table",
                "examples": ["SELECT * FROM users JOIN vscode_extensions USING (uid);"],
            }
        )

        mock_response_chrome = MagicMock()
        mock_response_chrome.status_code = 200
        mock_response_chrome.text = yaml.dump(
            {
                "name": "chrome_extensions",
                "notes": "Requires joining with users table",
                "examples": ["SELECT * FROM users JOIN chrome_extensions USING (uid);"],
            }
        )

        mock_response_processes = MagicMock()
        mock_response_processes.status_code = 404

        async def mock_get(url):
            if "vscode_extensions" in url:
                return mock_response_vscode
            elif "chrome_extensions" in url:
                return mock_response_chrome
            else:
                return mock_response_processes

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = mock_get
            mock_client_class.return_value = mock_client

            overrides = await cache._download_schema_overrides()

            # Should have downloaded 2 overrides (404 for processes is skipped)
            assert len(overrides) == 2
            assert "vscode_extensions" in overrides
            assert "chrome_extensions" in overrides
