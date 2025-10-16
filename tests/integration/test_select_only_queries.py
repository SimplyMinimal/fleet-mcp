"""Integration tests for SELECT-only query mode."""

import pytest

from fleet_mcp.config import FleetConfig
from fleet_mcp.server import FleetMCPServer


@pytest.mark.integration
@pytest.mark.asyncio
class TestSelectOnlyQueryMode:
    """Integration tests for SELECT-only query mode in read-only mode."""

    async def test_readonly_without_select_queries_blocks_all_queries(self):
        """Test that readonly mode without allow_select_queries blocks query tools."""
        config = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
            allow_select_queries=False,
        )

        server = FleetMCPServer(config)
        tools = await server.mcp.list_tools()
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]

        # Query execution tools should NOT be available
        assert "fleet_run_live_query" not in tool_names
        assert "fleet_run_saved_query" not in tool_names
        assert "fleet_query_host" not in tool_names
        assert "fleet_query_host_by_identifier" not in tool_names

        # Read-only query tools should still be available
        assert "fleet_list_queries" in tool_names
        assert "fleet_get_query" in tool_names

    async def test_readonly_with_select_queries_enables_query_tools(self):
        """Test that readonly mode with allow_select_queries enables SELECT-only query tools."""
        config = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
            allow_select_queries=True,
        )

        server = FleetMCPServer(config)
        tools = await server.mcp.list_tools()
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]

        # Query execution tools SHOULD be available
        assert "fleet_run_live_query" in tool_names
        assert "fleet_run_saved_query" in tool_names
        assert "fleet_query_host" in tool_names
        assert "fleet_query_host_by_identifier" in tool_names

        # Read-only query tools should still be available
        assert "fleet_list_queries" in tool_names
        assert "fleet_get_query" in tool_names

        # Write tools should NOT be available
        assert "fleet_create_query" not in tool_names
        assert "fleet_delete_query" not in tool_names
        assert "fleet_create_policy" not in tool_names
        assert "fleet_delete_host" not in tool_names

    async def test_write_mode_has_all_tools(self):
        """Test that write mode (readonly=False) has all tools regardless of allow_select_queries."""
        config = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=False,
            allow_select_queries=False,  # This should be ignored when readonly=False
        )

        server = FleetMCPServer(config)
        tools = await server.mcp.list_tools()
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]

        # All query tools should be available
        assert "fleet_run_live_query" in tool_names
        assert "fleet_run_saved_query" in tool_names
        assert "fleet_query_host" in tool_names
        assert "fleet_query_host_by_identifier" in tool_names
        assert "fleet_list_queries" in tool_names
        assert "fleet_get_query" in tool_names

        # Write tools should be available
        assert "fleet_create_query" in tool_names
        assert "fleet_delete_query" in tool_names
        assert "fleet_create_policy" in tool_names

    async def test_server_name_reflects_select_query_mode(self):
        """Test that server name reflects SELECT query mode."""
        # Readonly without SELECT queries
        config1 = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
            allow_select_queries=False,
        )
        server1 = FleetMCPServer(config1)
        assert "READ-ONLY MODE - no write operations available" in server1.mcp.name

        # Readonly with SELECT queries
        config2 = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
            allow_select_queries=True,
        )
        server2 = FleetMCPServer(config2)
        assert "READ-ONLY MODE - SELECT queries allowed" in server2.mcp.name

        # Write mode
        config3 = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=False,
        )
        server3 = FleetMCPServer(config3)
        assert "READ-ONLY MODE" not in server3.mcp.name

    async def test_server_instructions_reflect_select_query_mode(self):
        """Test that server instructions reflect SELECT query mode."""
        # Readonly without SELECT queries
        config1 = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
            allow_select_queries=False,
        )
        server1 = FleetMCPServer(config1)
        assert "READ-ONLY MODE" in server1.mcp.instructions
        assert (
            "No create, update, delete, or query execution operations are available"
            in server1.mcp.instructions
        )

        # Readonly with SELECT queries
        config2 = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
            allow_select_queries=True,
        )
        server2 = FleetMCPServer(config2)
        assert "READ-ONLY MODE - SELECT queries allowed" in server2.mcp.instructions
        assert (
            "You can run SELECT queries to read data from hosts"
            in server2.mcp.instructions
        )
        assert (
            "All queries are validated to ensure they are SELECT-only"
            in server2.mcp.instructions
        )

    async def test_tool_count_differences(self):
        """Test that tool counts differ based on configuration."""
        # Readonly without SELECT queries
        config1 = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
            allow_select_queries=False,
        )
        server1 = FleetMCPServer(config1)
        tools1 = await server1.mcp.list_tools()

        # Readonly with SELECT queries
        config2 = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
            allow_select_queries=True,
        )
        server2 = FleetMCPServer(config2)
        tools2 = await server2.mcp.list_tools()

        # Write mode
        config3 = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=False,
        )
        server3 = FleetMCPServer(config3)
        tools3 = await server3.mcp.list_tools()

        # SELECT query mode should have 4 more tools than strict readonly
        # (fleet_run_live_query, fleet_run_saved_query, fleet_query_host, fleet_query_host_by_identifier)
        assert len(tools2) == len(tools1) + 4

        # Write mode should have more tools than SELECT query mode
        assert len(tools3) > len(tools2)

    async def test_config_defaults(self):
        """Test that configuration defaults are correct."""
        config = FleetConfig(
            server_url="https://test.example.com", api_token="test-token-123456789"
        )

        # Default should be readonly=True, allow_select_queries=False
        assert config.readonly is True
        assert config.allow_select_queries is False

    async def test_allow_select_queries_ignored_when_not_readonly(self):
        """Test that allow_select_queries is effectively ignored when readonly=False."""
        # Both configurations should result in the same tools when readonly=False
        config1 = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=False,
            allow_select_queries=False,
        )
        server1 = FleetMCPServer(config1)
        tools1 = await server1.mcp.list_tools()

        config2 = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=False,
            allow_select_queries=True,
        )
        server2 = FleetMCPServer(config2)
        tools2 = await server2.mcp.list_tools()

        # Should have the same number of tools
        assert len(tools1) == len(tools2)

        # Should have the same tool names
        tool_names1 = {t.name if hasattr(t, "name") else str(t) for t in tools1}
        tool_names2 = {t.name if hasattr(t, "name") else str(t) for t in tools2}
        assert tool_names1 == tool_names2
