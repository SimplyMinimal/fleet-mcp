"""Unit tests for improved error handling in user and activity tools."""

from unittest.mock import patch

import pytest
from mcp.server.fastmcp import FastMCP

from fleet_mcp.client import FleetAPIError, FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools.activity_tools import (
    register_read_tools as register_activity_tools,
)
from fleet_mcp.tools.user_tools import register_read_tools as register_user_tools


@pytest.fixture
def fleet_config():
    """Create a test Fleet configuration."""
    return FleetConfig(
        server_url="https://test.fleet.com",
        api_token="test-token-123456789",
        readonly=True,
    )


@pytest.fixture
def fleet_client(fleet_config):
    """Create a test Fleet client."""
    return FleetClient(fleet_config)


@pytest.fixture
def mcp_server():
    """Create a FastMCP server instance."""
    return FastMCP("test-server")


class TestImprovedErrorHandling:
    """Test improved error handling for user and activity tools."""

    @pytest.mark.asyncio
    async def test_list_users_403_specific_message(self, mcp_server, fleet_client):
        """Test that fleet_list_users returns specific 403 error message."""
        register_user_tools(mcp_server, fleet_client)

        # Create a FleetAPIError with status_code 403
        error = FleetAPIError(
            "API request failed with status 403",
            status_code=403,
            response_data={"message": "Forbidden"},
        )

        with patch.object(fleet_client, "get", side_effect=error):
            tools = await mcp_server.list_tools()
            list_users_tool = next(t for t in tools if t.name == "fleet_list_users")
            result = await mcp_server.call_tool(list_users_tool.name, arguments={})

            # Verify specific 403 error message
            result_str = str(result)
            assert "403 Forbidden" in result_str
            assert "admin-level permissions" in result_str
            assert "API token has admin privileges" in result_str

    @pytest.mark.asyncio
    async def test_get_user_403_with_context(self, mcp_server, fleet_client):
        """Test that fleet_get_user includes user_id in error response."""
        register_user_tools(mcp_server, fleet_client)

        error = FleetAPIError(
            "API request failed with status 403",
            status_code=403,
            response_data={"message": "Forbidden"},
        )

        with patch.object(fleet_client, "get", side_effect=error):
            tools = await mcp_server.list_tools()
            get_user_tool = next(t for t in tools if t.name == "fleet_get_user")
            result = await mcp_server.call_tool(
                get_user_tool.name, arguments={"user_id": 123}
            )

            # Verify error message includes user_id context
            result_str = str(result)
            assert "403 Forbidden" in result_str
            assert "admin-level permissions" in result_str
            assert "user_id" in result_str or "123" in result_str

    @pytest.mark.asyncio
    async def test_list_users_generic_error(self, mcp_server, fleet_client):
        """Test that fleet_list_users handles non-403 errors correctly."""
        register_user_tools(mcp_server, fleet_client)

        error = FleetAPIError(
            "API request failed with status 500",
            status_code=500,
            response_data={"message": "Internal Server Error"},
        )

        with patch.object(fleet_client, "get", side_effect=error):
            tools = await mcp_server.list_tools()
            list_users_tool = next(t for t in tools if t.name == "fleet_list_users")
            result = await mcp_server.call_tool(list_users_tool.name, arguments={})

            # Verify generic error message (not 403-specific)
            result_str = str(result)
            assert "Failed to list users" in result_str
            # Should NOT contain 403-specific message
            assert "admin-level permissions" not in result_str

    @pytest.mark.asyncio
    async def test_list_users_empty_response_handling(self, mcp_server, fleet_client):
        """Test that fleet_list_users handles empty responses correctly."""
        register_user_tools(mcp_server, fleet_client)

        # Mock a response with success=False
        mock_response = FleetResponse(
            success=False, message="No data available", data=None
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            tools = await mcp_server.list_tools()
            list_users_tool = next(t for t in tools if t.name == "fleet_list_users")
            result = await mcp_server.call_tool(list_users_tool.name, arguments={})

            # Verify failure is reported correctly
            result_str = str(result)
            assert "success" in result_str.lower()
            assert "false" in result_str.lower() or "no data" in result_str.lower()

    @pytest.mark.asyncio
    async def test_get_user_empty_response_handling(self, mcp_server, fleet_client):
        """Test that fleet_get_user handles empty responses correctly."""
        register_user_tools(mcp_server, fleet_client)

        # Mock a response with success=False
        mock_response = FleetResponse(
            success=False, message="User not found", data=None
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            tools = await mcp_server.list_tools()
            get_user_tool = next(t for t in tools if t.name == "fleet_get_user")
            result = await mcp_server.call_tool(
                get_user_tool.name, arguments={"user_id": 999}
            )

            # Verify failure is reported correctly with context
            result_str = str(result)
            assert "success" in result_str.lower()
            assert "false" in result_str.lower() or "not found" in result_str.lower()
            assert "999" in result_str or "user_id" in result_str

    @pytest.mark.asyncio
    async def test_list_activities_403_specific_message(self, mcp_server, fleet_client):
        """Test that fleet_list_activities returns specific 403 error message."""
        register_activity_tools(mcp_server, fleet_client)

        error = FleetAPIError(
            "API request failed with status 403",
            status_code=403,
            response_data={"message": "Forbidden"},
        )

        with patch.object(fleet_client, "get", side_effect=error):
            tools = await mcp_server.list_tools()
            list_activities_tool = next(
                t for t in tools if t.name == "fleet_list_activities"
            )
            result = await mcp_server.call_tool(list_activities_tool.name, arguments={})

            # Verify specific 403 error message
            result_str = str(result)
            assert "403 Forbidden" in result_str
            assert "appropriate permissions" in result_str or "privileges" in result_str

    @pytest.mark.asyncio
    async def test_list_activities_empty_response_handling(
        self, mcp_server, fleet_client
    ):
        """Test that fleet_list_activities handles empty responses correctly."""
        register_activity_tools(mcp_server, fleet_client)

        # Mock a response with success=False
        mock_response = FleetResponse(
            success=False, message="No activities found", data=None
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            tools = await mcp_server.list_tools()
            list_activities_tool = next(
                t for t in tools if t.name == "fleet_list_activities"
            )
            result = await mcp_server.call_tool(list_activities_tool.name, arguments={})

            # Verify failure is reported correctly
            result_str = str(result)
            assert "success" in result_str.lower()
            assert "false" in result_str.lower() or "no" in result_str.lower()

    @pytest.mark.asyncio
    async def test_list_users_success_with_data(self, mcp_server, fleet_client):
        """Test that fleet_list_users handles successful responses correctly."""
        register_user_tools(mcp_server, fleet_client)

        # Mock a successful response
        mock_response = FleetResponse(
            success=True,
            message="Success",
            data={"users": [{"id": 1, "name": "Test User"}]},
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            tools = await mcp_server.list_tools()
            list_users_tool = next(t for t in tools if t.name == "fleet_list_users")
            result = await mcp_server.call_tool(list_users_tool.name, arguments={})

            # Verify success is reported correctly
            result_str = str(result)
            assert "success" in result_str.lower()
            assert "true" in result_str.lower() or "retrieved" in result_str.lower()

    @pytest.mark.asyncio
    async def test_get_user_success_with_data(self, mcp_server, fleet_client):
        """Test that fleet_get_user handles successful responses correctly."""
        register_user_tools(mcp_server, fleet_client)

        # Mock a successful response
        mock_response = FleetResponse(
            success=True,
            message="Success",
            data={"user": {"id": 123, "name": "Test User"}},
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            tools = await mcp_server.list_tools()
            get_user_tool = next(t for t in tools if t.name == "fleet_get_user")
            result = await mcp_server.call_tool(
                get_user_tool.name, arguments={"user_id": 123}
            )

            # Verify success is reported correctly
            result_str = str(result)
            assert "success" in result_str.lower()
            assert "true" in result_str.lower() or "retrieved" in result_str.lower()

    @pytest.mark.asyncio
    async def test_list_activities_success_with_data(self, mcp_server, fleet_client):
        """Test that fleet_list_activities handles successful responses correctly."""
        register_activity_tools(mcp_server, fleet_client)

        # Mock a successful response
        mock_response = FleetResponse(
            success=True,
            message="Success",
            data={"activities": [{"id": 1, "type": "user_login"}]},
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            tools = await mcp_server.list_tools()
            list_activities_tool = next(
                t for t in tools if t.name == "fleet_list_activities"
            )
            result = await mcp_server.call_tool(list_activities_tool.name, arguments={})

            # Verify success is reported correctly
            result_str = str(result)
            assert "success" in result_str.lower()
            assert "true" in result_str.lower() or "retrieved" in result_str.lower()
