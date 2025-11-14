"""Unit tests for custom variable management tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fleet_mcp.client import FleetAPIError, FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools import custom_variable_tools


@pytest.fixture
def fleet_config():
    """Create a test Fleet configuration."""
    return FleetConfig(
        server_url="https://test.fleet.com", api_token="test-token-123456789"
    )


@pytest.fixture
def fleet_client(fleet_config):
    """Create a test Fleet client."""
    return FleetClient(fleet_config)


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server."""
    mcp = MagicMock()
    # Store registered tools
    mcp._tools = {}

    def tool_decorator():
        def decorator(func):
            mcp._tools[func.__name__] = func
            return func

        return decorator

    mcp.tool = tool_decorator
    return mcp


class TestFleetListCustomVariables:
    """Test cases for fleet_list_custom_variables tool."""

    @pytest.mark.asyncio
    async def test_list_custom_variables_success(self, fleet_client, mock_mcp):
        """Test successful listing of custom variables."""
        mock_response = FleetResponse(
            success=True,
            data={
                "custom_variables": [
                    {"id": 1, "name": "API_TOKEN"},
                    {"id": 2, "name": "SECRET_KEY"},
                ],
                "count": 2,
                "meta": {"has_next_results": False, "has_previous_results": False},
            },
            message="Success",
            status_code=200,
        )

        # Register the tools
        custom_variable_tools.register_read_tools(mock_mcp, fleet_client)

        # Get the registered tool
        tool_func = mock_mcp._tools["fleet_list_custom_variables"]

        with patch.object(fleet_client, "get", return_value=mock_response):
            result = await tool_func()

        assert result["success"] is True
        assert len(result["custom_variables"]) == 2
        assert result["count"] == 2
        assert result["custom_variables"][0]["name"] == "API_TOKEN"
        assert result["custom_variables"][1]["name"] == "SECRET_KEY"

    @pytest.mark.asyncio
    async def test_list_custom_variables_api_error(self, fleet_client, mock_mcp):
        """Test handling of API errors."""
        custom_variable_tools.register_read_tools(mock_mcp, fleet_client)
        tool_func = mock_mcp._tools["fleet_list_custom_variables"]

        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Unauthorized", status_code=401),
        ):
            result = await tool_func()

        assert result["success"] is False
        assert "Unauthorized" in result["message"]
        assert result["custom_variables"] == []
        assert result["count"] == 0


class TestFleetCreateCustomVariable:
    """Test cases for fleet_create_custom_variable tool."""

    @pytest.mark.asyncio
    async def test_create_custom_variable_success(self, fleet_client, mock_mcp):
        """Test successful creation of a custom variable."""
        mock_response = FleetResponse(
            success=True,
            data={"id": 123, "name": "NEW_TOKEN"},
            message="Success",
            status_code=200,
        )

        custom_variable_tools.register_write_tools(mock_mcp, fleet_client)
        tool_func = mock_mcp._tools["fleet_create_custom_variable"]

        with patch.object(fleet_client, "post", return_value=mock_response):
            result = await tool_func(name="NEW_TOKEN", value="secret-value")

        assert result["success"] is True
        assert result["data"]["id"] == 123
        assert result["data"]["name"] == "NEW_TOKEN"
        assert "Created custom variable 'NEW_TOKEN'" in result["message"]

    @pytest.mark.asyncio
    async def test_create_custom_variable_api_error(self, fleet_client, mock_mcp):
        """Test handling of API errors during creation."""
        custom_variable_tools.register_write_tools(mock_mcp, fleet_client)
        tool_func = mock_mcp._tools["fleet_create_custom_variable"]

        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Variable already exists", status_code=409),
        ):
            result = await tool_func(name="DUPLICATE", value="value")

        assert result["success"] is False
        assert "Variable already exists" in result["message"]
        assert result["data"] is None


class TestFleetDeleteCustomVariable:
    """Test cases for fleet_delete_custom_variable tool."""

    @pytest.mark.asyncio
    async def test_delete_custom_variable_success(self, fleet_client, mock_mcp):
        """Test successful deletion of a custom variable."""
        mock_response = FleetResponse(
            success=True, data=None, message="Success", status_code=200
        )

        custom_variable_tools.register_write_tools(mock_mcp, fleet_client)
        tool_func = mock_mcp._tools["fleet_delete_custom_variable"]

        with patch.object(fleet_client, "delete", return_value=mock_response):
            result = await tool_func(variable_id=123)

        assert result["success"] is True
        assert "Successfully deleted custom variable 123" in result["message"]

    @pytest.mark.asyncio
    async def test_delete_custom_variable_not_found(self, fleet_client, mock_mcp):
        """Test deletion of non-existent variable."""
        custom_variable_tools.register_write_tools(mock_mcp, fleet_client)
        tool_func = mock_mcp._tools["fleet_delete_custom_variable"]

        with patch.object(
            fleet_client,
            "delete",
            side_effect=FleetAPIError("Not found", status_code=404),
        ):
            result = await tool_func(variable_id=999)

        assert result["success"] is False
        assert "Not found" in result["message"]
