"""Unit tests for the Fleet MCP Server health check functionality."""

import json
from unittest.mock import patch

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

    @pytest.fixture(autouse=True)
    def reset_global_cache(self):
        """Reset the global table cache before and after each test.

        This ensures that tests don't interfere with each other by leaving
        cached data or mock patches in place.
        """
        # Reset before test
        import fleet_mcp.tools.table_discovery as td

        original_cache = td._table_cache
        td._table_cache = None

        yield

        # Reset after test
        td._table_cache = original_cache

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

        # Mock the cache file path and reset the global cache
        with (
            patch("fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", cache_file),
            patch("fleet_mcp.tools.table_discovery.CACHE_DIR", cache_dir),
            patch("fleet_mcp.tools.table_discovery._table_cache", None),
        ):
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

            # Verify new fields
            assert "schema_source" in cache_info
            assert "errors" in cache_info
            assert "warnings" in cache_info
            assert "status" in cache_info

            # Should have warning about low table count
            assert cache_info["status"] == "warning"
            assert len(cache_info["warnings"]) > 0
            assert "Low table count" in cache_info["warnings"][0]

    @pytest.mark.asyncio
    async def test_get_cache_info_no_cache(self, tmp_path):
        """Test _get_cache_info when cache doesn't exist."""
        # Use a non-existent cache file
        cache_dir = tmp_path / ".fleet-mcp" / "cache"
        cache_file = cache_dir / "osquery_fleet_schema.json"

        with (
            patch("fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", cache_file),
            patch("fleet_mcp.tools.table_discovery.CACHE_DIR", cache_dir),
            patch("fleet_mcp.tools.table_discovery._table_cache", None),
        ):
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
    async def test_get_cache_info_healthy_cache(self, tmp_path):
        """Test _get_cache_info with a healthy cache (100+ tables)."""
        # Create a mock cache file with many tables
        cache_dir = tmp_path / ".fleet-mcp" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "osquery_fleet_schema.json"

        # Generate 100 mock tables
        mock_schema = {}
        for i in range(100):
            mock_schema[f"table_{i}"] = {
                "description": f"Test table {i}",
                "platforms": ["darwin", "linux", "windows"],
                "columns": [{"name": "id", "type": "bigint"}],
            }

        with open(cache_file, "w") as f:
            json.dump(mock_schema, f)

        # Mock the cache file path and reset the global cache
        with (
            patch("fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", cache_file),
            patch("fleet_mcp.tools.table_discovery.CACHE_DIR", cache_dir),
            patch("fleet_mcp.tools.table_discovery._table_cache", None),
        ):
            cache_info = await FleetMCPServer._get_cache_info()

            # Verify healthy status
            assert cache_info["cached"] is True
            assert cache_info["tables_loaded"] == 100
            assert cache_info["status"] == "healthy"
            assert len(cache_info["errors"]) == 0
            # Should not have low table count warning
            low_count_warnings = [
                w for w in cache_info["warnings"] if "Low table count" in w
            ]
            assert len(low_count_warnings) == 0

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
            assert cache_info["status"] == "error"
            assert "error" in cache_info
            assert "Cache error" in cache_info["error"]
            assert "message" in cache_info
            assert "errors" in cache_info
            assert len(cache_info["errors"]) > 0

    @pytest.mark.asyncio
    async def test_get_fleet_user_info_success(self, mock_config):
        """Test _get_fleet_user_info with successful API response.

        Tests with realistic Fleet API response structure including all fields
        from the /api/v1/fleet/me endpoint.
        """
        from fleet_mcp.client import FleetResponse

        server = FleetMCPServer(mock_config)

        # Mock the get_current_user response with realistic Fleet API structure
        # This matches the actual /api/v1/fleet/me endpoint response
        mock_user_data = {
            "user": {
                "created_at": "2020-11-13T22:57:12Z",
                "updated_at": "2020-11-16T23:49:41Z",
                "id": 1,
                "name": "Admin User",
                "email": "admin@example.com",
                "global_role": "admin",
                "enabled": True,
                "force_password_reset": False,
                "gravatar_url": "",
                "sso_enabled": False,
                "role": "admin",  # Role on a specific team (if not global admin)
                "teams": [
                    {
                        "id": 1,
                        "name": "Engineering",
                        "description": "Engineering team",
                        "role": "admin",
                    },
                    {
                        "id": 2,
                        "name": "Operations",
                        "description": "Operations team",
                        "role": "maintainer",
                    },
                ],
            },
            "available_teams": [
                {
                    "id": 1,
                    "name": "Engineering",
                    "description": "Engineering team",
                },
                {
                    "id": 2,
                    "name": "Operations",
                    "description": "Operations team",
                },
                {
                    "id": 3,
                    "name": "Security",
                    "description": "Security team",
                },
            ],
        }

        mock_response = FleetResponse(
            success=True,
            data=mock_user_data,
            message="Success",
        )

        with patch.object(
            server.client,
            "get_current_user",
            return_value=mock_response,
        ):
            user_info = await server._get_fleet_user_info()

            # Verify user info structure
            assert user_info["fleet_user_role"] == "admin"
            assert user_info["fleet_user_email"] == "admin@example.com"
            assert user_info["fleet_user_name"] == "Admin User"
            assert user_info["fleet_user_global_role"] == "admin"
            # Should extract team IDs from user.teams, not available_teams
            assert user_info["fleet_user_teams"] == [1, 2]
            assert user_info["fleet_user_error"] is None

    @pytest.mark.asyncio
    async def test_get_fleet_user_info_failure(self, mock_config):
        """Test _get_fleet_user_info when API call fails."""
        from fleet_mcp.client import FleetResponse

        server = FleetMCPServer(mock_config)

        # Mock a failed get_current_user response
        mock_response = FleetResponse(
            success=False,
            data=None,
            message="Authentication failed",
        )

        with patch.object(
            server.client,
            "get_current_user",
            return_value=mock_response,
        ):
            user_info = await server._get_fleet_user_info()

            # Verify error handling
            assert user_info["fleet_user_role"] is None
            assert user_info["fleet_user_email"] is None
            assert user_info["fleet_user_name"] is None
            assert user_info["fleet_user_global_role"] is None
            assert user_info["fleet_user_teams"] is None
            assert user_info["fleet_user_error"] == "Authentication failed"

    @pytest.mark.asyncio
    async def test_get_fleet_user_info_exception(self, mock_config):
        """Test _get_fleet_user_info when an exception occurs."""
        server = FleetMCPServer(mock_config)

        # Mock an exception during get_current_user
        with patch.object(
            server.client,
            "get_current_user",
            side_effect=Exception("Network error"),
        ):
            user_info = await server._get_fleet_user_info()

            # Verify error handling
            assert user_info["fleet_user_role"] is None
            assert user_info["fleet_user_email"] is None
            assert user_info["fleet_user_name"] is None
            assert user_info["fleet_user_global_role"] is None
            assert user_info["fleet_user_teams"] is None
            assert "Network error" in user_info["fleet_user_error"]

    @pytest.mark.asyncio
    async def test_get_fleet_user_info_null_global_role(self, mock_config):
        """Test _get_fleet_user_info when global_role is null (team-specific user).

        Non-admin users who only have team-specific roles will have null global_role.
        """
        from fleet_mcp.client import FleetResponse

        server = FleetMCPServer(mock_config)

        # Mock a team-specific user (no global role)
        mock_user_data = {
            "user": {
                "id": 2,
                "name": "Team Lead",
                "email": "lead@example.com",
                "global_role": None,  # No global role
                "role": "maintainer",  # Role on specific team
                "teams": [
                    {
                        "id": 1,
                        "name": "Engineering",
                        "role": "maintainer",
                    }
                ],
            }
        }

        mock_response = FleetResponse(
            success=True,
            data=mock_user_data,
            message="Success",
        )

        with patch.object(
            server.client,
            "get_current_user",
            return_value=mock_response,
        ):
            user_info = await server._get_fleet_user_info()

            # Verify handling of null global_role
            assert user_info["fleet_user_role"] == "maintainer"
            assert user_info["fleet_user_email"] == "lead@example.com"
            assert user_info["fleet_user_name"] == "Team Lead"
            assert user_info["fleet_user_global_role"] is None  # Should be None
            assert user_info["fleet_user_teams"] == [1]
            assert user_info["fleet_user_error"] is None

    @pytest.mark.asyncio
    async def test_get_fleet_user_info_empty_teams(self, mock_config):
        """Test _get_fleet_user_info when teams array is empty."""
        from fleet_mcp.client import FleetResponse

        server = FleetMCPServer(mock_config)

        # Mock a user with no team assignments
        mock_user_data = {
            "user": {
                "id": 3,
                "name": "Observer User",
                "email": "observer@example.com",
                "global_role": "observer",
                "role": None,
                "teams": [],  # Empty teams array
            }
        }

        mock_response = FleetResponse(
            success=True,
            data=mock_user_data,
            message="Success",
        )

        with patch.object(
            server.client,
            "get_current_user",
            return_value=mock_response,
        ):
            user_info = await server._get_fleet_user_info()

            # Verify handling of empty teams
            assert user_info["fleet_user_role"] is None
            assert user_info["fleet_user_email"] == "observer@example.com"
            assert user_info["fleet_user_name"] == "Observer User"
            assert user_info["fleet_user_global_role"] == "observer"
            assert (
                user_info["fleet_user_teams"] is None
            )  # Should be None, not empty list
            assert user_info["fleet_user_error"] is None

    @pytest.mark.asyncio
    async def test_get_fleet_user_info_uses_user_teams_not_available_teams(
        self, mock_config
    ):
        """Test that _get_fleet_user_info uses user.teams, not available_teams.

        The API response includes both user.teams (teams the user is a member of)
        and available_teams (all teams in the Fleet instance). We should only
        extract team IDs from user.teams.
        """
        from fleet_mcp.client import FleetResponse

        server = FleetMCPServer(mock_config)

        # Mock response with both user.teams and available_teams
        mock_user_data = {
            "user": {
                "id": 1,
                "name": "Admin User",
                "email": "admin@example.com",
                "global_role": "admin",
                "teams": [
                    {"id": 1, "name": "Engineering"},
                    {"id": 2, "name": "Operations"},
                ],
            },
            "available_teams": [
                {"id": 1, "name": "Engineering"},
                {"id": 2, "name": "Operations"},
                {"id": 3, "name": "Security"},
                {"id": 4, "name": "Finance"},
            ],
        }

        mock_response = FleetResponse(
            success=True,
            data=mock_user_data,
            message="Success",
        )

        with patch.object(
            server.client,
            "get_current_user",
            return_value=mock_response,
        ):
            user_info = await server._get_fleet_user_info()

            # Should only have teams from user.teams (1, 2), not all available_teams (1, 2, 3, 4)
            assert user_info["fleet_user_teams"] == [1, 2]
            assert user_info["fleet_user_error"] is None

    @pytest.mark.asyncio
    async def test_health_check_includes_server_config(self, mock_config):
        """Test that health check includes server configuration."""
        # Create server with specific config
        config = FleetConfig(
            server_url="https://test.fleet.com",
            api_token="test-token-123456789",
            readonly=True,
            allow_select_queries=True,
        )
        server = FleetMCPServer(config)

        # Mock the health check and user info calls
        mock_response = httpx.Response(
            status_code=200,
            json={"config": {"server_settings": {}}},
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/config"),
        )

        mock_user_info = {
            "fleet_user_role": "admin",
            "fleet_user_email": "admin@example.com",
            "fleet_user_name": "Admin User",
            "fleet_user_global_role": "admin",
            "fleet_user_teams": [1, 2],
            "fleet_user_error": None,
        }

        with (
            patch.object(httpx.AsyncClient, "request", return_value=mock_response),
            patch.object(server, "_get_fleet_user_info", return_value=mock_user_info),
        ):
            # Call the health check tool using the MCP server's call_tool method
            result = await server.mcp.call_tool("fleet_health_check", arguments={})

            # The result is a list of TextContent objects, so we need to parse it
            # Extract the actual result from the response

            result_str = str(result)

            # Verify server_config is included in the result
            assert "server_config" in result_str
            assert "readonly_mode" in result_str
            assert "allow_select_queries" in result_str

            # Verify fleet_user is included
            assert "fleet_user" in result_str
            assert "fleet_user_role" in result_str
            assert "admin@example.com" in result_str

    @pytest.mark.asyncio
    async def test_preload_schema_cache_with_cache(self, mock_config, tmp_path):
        """Test _preload_schema_cache with existing cache."""
        # Create a mock cache file
        cache_dir = tmp_path / ".fleet-mcp" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "osquery_fleet_schema.json"

        # Write mock schema data with 100+ tables for healthy status
        mock_schema = {}
        for i in range(100):
            mock_schema[f"table_{i}"] = {
                "description": f"Test table {i}",
                "platforms": ["darwin", "linux", "windows"],
                "columns": [{"name": "id", "type": "bigint"}],
            }

        with open(cache_file, "w") as f:
            json.dump(mock_schema, f)

        # Mock the cache file path
        with (
            patch("fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", cache_file),
            patch("fleet_mcp.tools.table_discovery.CACHE_DIR", cache_dir),
            patch("fleet_mcp.tools.table_discovery._table_cache", None),
        ):
            server = FleetMCPServer(mock_config)

            # Call preload method
            await server._preload_schema_cache()

            # Verify cache was loaded by checking the global cache
            from fleet_mcp.tools.table_discovery import get_table_cache

            cache = await get_table_cache()
            assert len(cache.fleet_schemas) == 100
            assert cache.fleet_schemas_loaded is True

    @pytest.mark.asyncio
    async def test_preload_schema_cache_no_cache(self, mock_config, tmp_path):
        """Test _preload_schema_cache when cache doesn't exist."""
        # Use a non-existent cache file
        cache_dir = tmp_path / ".fleet-mcp" / "cache"
        cache_file = cache_dir / "osquery_fleet_schema.json"

        with (
            patch("fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", cache_file),
            patch("fleet_mcp.tools.table_discovery.CACHE_DIR", cache_dir),
            patch("fleet_mcp.tools.table_discovery._table_cache", None),
        ):
            # Mock the schema download to fail
            with patch(
                "fleet_mcp.tools.table_discovery.TableSchemaCache._download_fleet_schema",
                side_effect=Exception("Download failed"),
            ):
                server = FleetMCPServer(mock_config)

                # Call preload method - should not raise exception
                await server._preload_schema_cache()

                # Verify cache was attempted to be loaded
                from fleet_mcp.tools.table_discovery import get_table_cache

                cache = await get_table_cache()
                # Should fall back to bundled schemas
                assert cache.fleet_schemas_loaded is True

    @pytest.mark.asyncio
    async def test_preload_schema_cache_with_overrides(self, mock_config, tmp_path):
        """Test _preload_schema_cache with schema overrides."""
        # Create mock cache files
        cache_dir = tmp_path / ".fleet-mcp" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "osquery_fleet_schema.json"
        overrides_file = cache_dir / "osquery_schema_overrides.json"

        # Write mock schema data
        mock_schema = {}
        for i in range(100):
            mock_schema[f"table_{i}"] = {
                "description": f"Test table {i}",
                "platforms": ["darwin", "linux", "windows"],
                "columns": [{"name": "id", "type": "bigint"}],
            }

        with open(cache_file, "w") as f:
            json.dump(mock_schema, f)

        # Write mock overrides
        mock_overrides = {
            "table_0": {
                "notes": "Special requirements for table_0",
                "examples": ["SELECT * FROM table_0;"],
            }
        }

        with open(overrides_file, "w") as f:
            json.dump(mock_overrides, f)

        # Mock the cache file paths
        with (
            patch("fleet_mcp.tools.table_discovery.SCHEMA_CACHE_FILE", cache_file),
            patch(
                "fleet_mcp.tools.table_discovery.SCHEMA_OVERRIDES_CACHE_FILE",
                overrides_file,
            ),
            patch("fleet_mcp.tools.table_discovery.CACHE_DIR", cache_dir),
            patch("fleet_mcp.tools.table_discovery._table_cache", None),
        ):
            server = FleetMCPServer(mock_config)

            # Call preload method
            await server._preload_schema_cache()

            # Verify cache and overrides were loaded
            from fleet_mcp.tools.table_discovery import get_table_cache

            cache = await get_table_cache()
            assert len(cache.fleet_schemas) == 100
            assert len(cache.schema_overrides) == 1
            assert cache.overrides_loaded is True

    @pytest.mark.asyncio
    async def test_preload_schema_cache_error_handling(self, mock_config):
        """Test that _preload_schema_cache handles errors gracefully."""
        server = FleetMCPServer(mock_config)

        # Mock get_table_cache to raise an exception
        with patch(
            "fleet_mcp.tools.table_discovery.get_table_cache",
            side_effect=Exception("Cache initialization error"),
        ):
            # Should not raise exception
            await server._preload_schema_cache()

            # Server should still be functional
            assert server.config == mock_config
