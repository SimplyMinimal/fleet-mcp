"""Integration tests for read-only mode functionality.

These tests verify that readonly mode works correctly with actual server
configuration and tool registration.
"""

import pytest

from fleet_mcp.config import FleetConfig, get_default_config_file, load_config
from fleet_mcp.server import FleetMCPServer


@pytest.mark.integration
class TestReadOnlyModeIntegration:
    """Integration tests for read-only mode."""

    @pytest.mark.asyncio
    async def test_readonly_mode_blocks_write_tools(self):
        """Test that readonly mode prevents write tools from being registered."""
        config = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
        )

        server = FleetMCPServer(config)
        tools = await server.mcp.list_tools()

        # Categorize tools
        write_tools = []
        for tool in tools:
            tool_name = tool.name if hasattr(tool, "name") else str(tool)
            if any(
                keyword in tool_name.lower()
                for keyword in [
                    "create",
                    "delete",
                    "update",
                    "transfer",
                    "run_live",
                    "run_saved",
                ]
            ):
                write_tools.append(tool_name)

        # In readonly mode, no write tools should be available
        assert (
            len(write_tools) == 0
        ), f"Found write tools in readonly mode: {write_tools}"

    @pytest.mark.asyncio
    async def test_write_mode_enables_write_tools(self):
        """Test that disabling readonly mode enables write tools."""
        config = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=False,
        )

        server = FleetMCPServer(config)
        tools = await server.mcp.list_tools()

        # Categorize tools
        write_tools = []
        for tool in tools:
            tool_name = tool.name if hasattr(tool, "name") else str(tool)
            if any(
                keyword in tool_name.lower()
                for keyword in [
                    "create",
                    "delete",
                    "update",
                    "transfer",
                    "run_live",
                    "run_saved",
                ]
            ):
                write_tools.append(tool_name)

        # With readonly=False, write tools should be available
        assert len(write_tools) > 0, "No write tools found when readonly=False"

        # Verify specific write tools are present
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]
        expected_write_tools = [
            "fleet_create_policy",
            "fleet_create_query",
            "fleet_delete_host",
            "fleet_delete_policy",
            "fleet_delete_query",
        ]

        for expected_tool in expected_write_tools:
            assert (
                expected_tool in tool_names
            ), f"Expected write tool '{expected_tool}' not found"

    @pytest.mark.asyncio
    async def test_readonly_mode_server_name(self):
        """Test that server name reflects readonly mode."""
        # Test readonly mode
        config_readonly = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
        )
        server_readonly = FleetMCPServer(config_readonly)
        assert "READ-ONLY MODE" in server_readonly.mcp.name

        # Test write mode
        config_write = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=False,
        )
        server_write = FleetMCPServer(config_write)
        assert "READ-ONLY MODE" not in server_write.mcp.name

    @pytest.mark.asyncio
    async def test_readonly_mode_from_config_file(self):
        """Test loading readonly mode from configuration file."""
        config_file = get_default_config_file()

        if config_file.exists():
            config = load_config(config_file)
            server = FleetMCPServer(config)

            # Verify server reflects config
            if config.readonly:
                assert "READ-ONLY MODE" in server.mcp.name
            else:
                assert "READ-ONLY MODE" not in server.mcp.name

    @pytest.mark.asyncio
    async def test_tool_count_difference(self):
        """Test that readonly mode has fewer tools than write mode."""
        # Readonly mode
        config_readonly = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=True,
        )
        server_readonly = FleetMCPServer(config_readonly)
        tools_readonly = await server_readonly.mcp.list_tools()

        # Write mode
        config_write = FleetConfig(
            server_url="https://test.example.com",
            api_token="test-token-123456789",
            readonly=False,
        )
        server_write = FleetMCPServer(config_write)
        tools_write = await server_write.mcp.list_tools()

        # Write mode should have more tools
        assert len(tools_write) > len(
            tools_readonly
        ), f"Write mode ({len(tools_write)} tools) should have more tools than readonly mode ({len(tools_readonly)} tools)"

        # The difference should be the write tools
        difference = len(tools_write) - len(tools_readonly)
        assert difference >= 10, f"Expected at least 10 write tools, found {difference}"
