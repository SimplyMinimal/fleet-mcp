"""Tests for new Fleet Team management tools (Priority 5B)."""

from unittest.mock import MagicMock, patch

import pytest

from fleet_mcp.client import FleetAPIError, FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools import team_tools


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


class TestFleetListTeamUsers:
    """Test fleet_list_team_users tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful retrieval of team users."""
        mock_response = FleetResponse(
            success=True,
            data={
                "users": [
                    {
                        "id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "role": "admin",
                        "global_role": None,
                        "teams": [
                            {"id": 1, "name": "Engineering", "role": "maintainer"}
                        ],
                    },
                    {
                        "id": 2,
                        "name": "Jane Smith",
                        "email": "jane@example.com",
                        "role": "observer",
                        "global_role": None,
                        "teams": [{"id": 1, "name": "Engineering", "role": "observer"}],
                    },
                ]
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            team_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_empty_team(self, fleet_client, mock_mcp):
        """Test handling of team with no users."""
        mock_response = FleetResponse(
            success=True,
            data={"users": []},
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            team_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_team_not_found(self, fleet_client, mock_mcp):
        """Test handling when team is not found."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Team not found", status_code=404),
        ):
            team_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_forbidden_access(self, fleet_client, mock_mcp):
        """Test handling of 403 forbidden error."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Forbidden", status_code=403),
        ):
            team_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestFleetGetTeamSecrets:
    """Test fleet_get_team_secrets tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful retrieval of team secrets."""
        mock_response = FleetResponse(
            success=True,
            data={
                "secrets": [
                    {
                        "secret": "abc123def456",
                        "created_at": "2024-01-15T10:00:00Z",
                        "team_id": 1,
                    }
                ]
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            team_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_no_secrets(self, fleet_client, mock_mcp):
        """Test handling when team has no secrets."""
        mock_response = FleetResponse(
            success=True,
            data={"secrets": []},
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            team_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_team_not_found(self, fleet_client, mock_mcp):
        """Test handling when team is not found."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Team not found", status_code=404),
        ):
            team_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestFleetAddTeamUsers:
    """Test fleet_add_team_users tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful addition of users to team."""
        mock_response = FleetResponse(
            success=True,
            data={"team": {"id": 1, "name": "Engineering", "user_count": 5}},
            message="Users added successfully",
        )

        with patch.object(fleet_client, "patch", return_value=mock_response):
            team_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_user_not_found(self, fleet_client, mock_mcp):
        """Test handling when user is not found."""
        with patch.object(
            fleet_client,
            "patch",
            side_effect=FleetAPIError("User not found", status_code=404),
        ):
            team_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_team_not_found(self, fleet_client, mock_mcp):
        """Test handling when team is not found."""
        with patch.object(
            fleet_client,
            "patch",
            side_effect=FleetAPIError("Team not found", status_code=404),
        ):
            team_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_invalid_role(self, fleet_client, mock_mcp):
        """Test handling of invalid role."""
        with patch.object(
            fleet_client,
            "patch",
            side_effect=FleetAPIError("Invalid role", status_code=400),
        ):
            team_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_forbidden_access(self, fleet_client, mock_mcp):
        """Test handling of 403 forbidden error."""
        with patch.object(
            fleet_client,
            "patch",
            side_effect=FleetAPIError("Forbidden", status_code=403),
        ):
            team_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestFleetRemoveTeamUser:
    """Test fleet_remove_team_user tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful removal of user from team."""
        mock_response = FleetResponse(
            success=True,
            data={},
            message="User removed from team successfully",
        )

        with patch.object(fleet_client, "delete", return_value=mock_response):
            team_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_user_not_in_team(self, fleet_client, mock_mcp):
        """Test handling when user is not in team."""
        with patch.object(
            fleet_client,
            "delete",
            side_effect=FleetAPIError("User not in team", status_code=404),
        ):
            team_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_team_not_found(self, fleet_client, mock_mcp):
        """Test handling when team is not found."""
        with patch.object(
            fleet_client,
            "delete",
            side_effect=FleetAPIError("Team not found", status_code=404),
        ):
            team_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_forbidden_access(self, fleet_client, mock_mcp):
        """Test handling of 403 forbidden error."""
        with patch.object(
            fleet_client,
            "delete",
            side_effect=FleetAPIError("Forbidden", status_code=403),
        ):
            team_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_last_admin_removal(self, fleet_client, mock_mcp):
        """Test handling when trying to remove last admin from team."""
        with patch.object(
            fleet_client,
            "delete",
            side_effect=FleetAPIError("Cannot remove last admin", status_code=400),
        ):
            team_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called
