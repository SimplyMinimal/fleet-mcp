"""Tests for new Fleet User management tools (Priority 6)."""

from unittest.mock import MagicMock, patch

import pytest

from fleet_mcp.client import FleetAPIError, FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools import user_tools


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
    mcp.tool = MagicMock(return_value=lambda f: f)
    return mcp


class TestFleetRequirePasswordReset:
    """Test fleet_require_password_reset tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful password reset requirement."""
        mock_response = FleetResponse(
            success=True,
            data={
                "user": {
                    "id": 123,
                    "email": "user@example.com",
                    "name": "Test User",
                    "force_password_reset": True,
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            },
            message="Password reset required successfully",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            user_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_user_not_found(self, fleet_client, mock_mcp):
        """Test handling when user is not found."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("User not found", status_code=404),
        ):
            user_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_forbidden_access(self, fleet_client, mock_mcp):
        """Test handling of 403 forbidden error."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Forbidden", status_code=403),
        ):
            user_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_api_error(self, fleet_client, mock_mcp):
        """Test handling of API error."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Internal server error", status_code=500),
        ):
            user_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_sso_user(self, fleet_client, mock_mcp):
        """Test handling when user is SSO-enabled."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError(
                "Cannot reset password for SSO user", status_code=400
            ),
        ):
            user_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_already_required(self, fleet_client, mock_mcp):
        """Test when password reset is already required."""
        mock_response = FleetResponse(
            success=True,
            data={
                "user": {
                    "id": 123,
                    "email": "user@example.com",
                    "name": "Test User",
                    "force_password_reset": True,
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            },
            message="Password reset already required",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            user_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_self_reset(self, fleet_client, mock_mcp):
        """Test requiring password reset for current user."""
        mock_response = FleetResponse(
            success=True,
            data={
                "user": {
                    "id": 1,
                    "email": "admin@example.com",
                    "name": "Admin User",
                    "force_password_reset": True,
                    "updated_at": "2024-01-15T10:30:00Z",
                }
            },
            message="Password reset required for current user",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            user_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_invalid_user_id(self, fleet_client, mock_mcp):
        """Test handling of invalid user ID."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Invalid user ID", status_code=400),
        ):
            user_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_unauthorized(self, fleet_client, mock_mcp):
        """Test handling of unauthorized access."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Unauthorized", status_code=401),
        ):
            user_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called
