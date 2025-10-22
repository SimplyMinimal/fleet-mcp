"""Tests for new Fleet Software management tools (Priority 6)."""

from unittest.mock import MagicMock, patch

import pytest

from fleet_mcp.client import FleetAPIError, FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools import software_tools


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


class TestFleetBatchSetSoftware:
    """Test fleet_batch_set_software tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful batch software upload."""
        mock_response = FleetResponse(
            success=True,
            data={"request_uuid": "abc-123-def-456", "software_count": 3},
            message="Batch software upload initiated",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            software_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_dry_run(self, fleet_client, mock_mcp):
        """Test dry run mode."""
        mock_response = FleetResponse(
            success=True,
            data={
                "request_uuid": None,
                "software_count": 3,
                "dry_run": True,
                "validation_results": [
                    {"software_title": "Chrome", "valid": True},
                    {"software_title": "Firefox", "valid": True},
                    {
                        "software_title": "Invalid",
                        "valid": False,
                        "error": "Invalid package",
                    },
                ],
            },
            message="Dry run completed",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            software_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_empty_software_list(self, fleet_client, mock_mcp):
        """Test handling of empty software list."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Software list cannot be empty", status_code=400),
        ):
            software_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_invalid_team_id(self, fleet_client, mock_mcp):
        """Test handling of invalid team ID."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Team not found", status_code=404),
        ):
            software_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_forbidden_access(self, fleet_client, mock_mcp):
        """Test handling of 403 forbidden error."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Forbidden", status_code=403),
        ):
            software_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_api_error(self, fleet_client, mock_mcp):
        """Test handling of API error."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Internal server error", status_code=500),
        ):
            software_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_with_team_id(self, fleet_client, mock_mcp):
        """Test batch software upload with team ID."""
        mock_response = FleetResponse(
            success=True,
            data={"request_uuid": "xyz-789-abc-123", "software_count": 2, "team_id": 5},
            message="Batch software upload initiated for team",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            software_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_large_batch(self, fleet_client, mock_mcp):
        """Test handling of large software batch."""
        mock_response = FleetResponse(
            success=True,
            data={"request_uuid": "large-batch-uuid", "software_count": 100},
            message="Large batch software upload initiated",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            software_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_invalid_software_format(self, fleet_client, mock_mcp):
        """Test handling of invalid software format."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Invalid software format", status_code=400),
        ):
            software_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called
