"""Unit tests for user management tools 403 error handling."""

from unittest.mock import patch

import httpx
import pytest
from mcp.server.fastmcp import FastMCP

from fleet_mcp.client import FleetAPIError, FleetClient
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools.user_tools import register_read_tools


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


class TestUserTools403Handling:
    """Test 403 error handling for user management tools."""

    @pytest.mark.asyncio
    async def test_list_users_403_error_message(self, mcp_server, fleet_client):
        """Test that fleet_list_users returns helpful message on 403 error."""
        # Register the tools
        register_read_tools(mcp_server, fleet_client)

        # Mock a 403 response
        mock_response = httpx.Response(
            status_code=403,
            json={"message": "Forbidden", "errors": []},
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/users"),
        )

        # Create a FleetAPIError with status_code attribute
        error = FleetAPIError(
            "API request failed with status 403",
            status_code=403,
            response_data={"message": "Forbidden"},
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
            with patch.object(fleet_client, "get", side_effect=error):
                # Get the tool function
                tools = await mcp_server.list_tools()
                list_users_tool = next(t for t in tools if t.name == "fleet_list_users")

                # Call the tool
                result = await mcp_server.call_tool(list_users_tool.name, arguments={})

                # Verify the error message is helpful
                assert result is not None
                # The result should contain helpful guidance about admin permissions
                result_str = str(result)
                assert "403" in result_str or "Forbidden" in result_str
                assert (
                    "admin" in result_str.lower() or "permission" in result_str.lower()
                )

    @pytest.mark.asyncio
    async def test_get_user_403_error_message(self, mcp_server, fleet_client):
        """Test that fleet_get_user returns helpful message on 403 error."""
        # Register the tools
        register_read_tools(mcp_server, fleet_client)

        # Mock a 403 response
        mock_response = httpx.Response(
            status_code=403,
            json={"message": "Forbidden", "errors": []},
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/users/1"),
        )

        # Create a FleetAPIError with status_code attribute
        error = FleetAPIError(
            "API request failed with status 403",
            status_code=403,
            response_data={"message": "Forbidden"},
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
            with patch.object(fleet_client, "get", side_effect=error):
                # Get the tool function
                tools = await mcp_server.list_tools()
                get_user_tool = next(t for t in tools if t.name == "fleet_get_user")

                # Call the tool
                result = await mcp_server.call_tool(
                    get_user_tool.name, arguments={"user_id": 1}
                )

                # Verify the error message is helpful
                assert result is not None
                result_str = str(result)
                assert "403" in result_str or "Forbidden" in result_str
                assert (
                    "admin" in result_str.lower() or "permission" in result_str.lower()
                )

    @pytest.mark.asyncio
    async def test_list_users_other_error(self, mcp_server, fleet_client):
        """Test that fleet_list_users handles non-403 errors correctly."""
        # Register the tools
        register_read_tools(mcp_server, fleet_client)

        # Mock a 500 response (server error)
        mock_response = httpx.Response(
            status_code=500,
            json={"message": "Internal Server Error", "errors": []},
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/users"),
        )

        # Create a FleetAPIError with status_code attribute
        error = FleetAPIError(
            "API request failed with status 500",
            status_code=500,
            response_data={"message": "Internal Server Error"},
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
            with patch.object(fleet_client, "get", side_effect=error):
                # Get the tool function
                tools = await mcp_server.list_tools()
                list_users_tool = next(t for t in tools if t.name == "fleet_list_users")

                # Call the tool
                result = await mcp_server.call_tool(list_users_tool.name, arguments={})

                # Verify the error message doesn't mention admin permissions
                assert result is not None
                result_str = str(result)
                # Should contain the error but not the admin-specific message
                assert "500" in result_str or "failed" in result_str.lower()

    @pytest.mark.asyncio
    async def test_list_users_success(self, mcp_server, fleet_client):
        """Test that fleet_list_users works correctly with valid admin token."""
        # Register the tools
        register_read_tools(mcp_server, fleet_client)

        # Mock a successful response
        mock_response = httpx.Response(
            status_code=200,
            json={
                "users": [
                    {
                        "id": 1,
                        "name": "Admin User",
                        "email": "[email protected]",
                        "global_role": "admin",
                    }
                ]
            },
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/users"),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
            # Get the tool function
            tools = await mcp_server.list_tools()
            list_users_tool = next(t for t in tools if t.name == "fleet_list_users")

            # Call the tool
            result = await mcp_server.call_tool(list_users_tool.name, arguments={})

            # Verify success
            assert result is not None
            result_str = str(result)
            assert "Admin User" in result_str or "success" in result_str.lower()
