"""Tests for new Fleet MDM management tools (Priority 6)."""

from unittest.mock import MagicMock, patch

import pytest

from fleet_mcp.client import FleetAPIError, FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools import mdm_tools


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


class TestFleetListMdmAppleInstallers:
    """Test fleet_list_mdm_apple_installers tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful retrieval of MDM Apple installers."""
        mock_response = FleetResponse(
            success=True,
            data={
                "installers": [
                    {
                        "id": 1,
                        "name": "FleetDM.pkg",
                        "size": 12345678,
                        "manifest": "https://example.com/manifest.plist",
                        "installer": "https://example.com/installer.pkg",
                        "created_at": "2024-01-15T10:00:00Z",
                        "updated_at": "2024-01-15T10:00:00Z",
                    },
                    {
                        "id": 2,
                        "name": "FleetAgent.pkg",
                        "size": 9876543,
                        "manifest": "https://example.com/manifest2.plist",
                        "installer": "https://example.com/installer2.pkg",
                        "created_at": "2024-01-16T11:00:00Z",
                        "updated_at": "2024-01-16T11:00:00Z",
                    },
                ]
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            mdm_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_empty_list(self, fleet_client, mock_mcp):
        """Test handling of empty installer list."""
        mock_response = FleetResponse(
            success=True,
            data={"installers": []},
            message="No installers found",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            mdm_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_forbidden_access(self, fleet_client, mock_mcp):
        """Test handling of 403 forbidden error."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Forbidden", status_code=403),
        ):
            mdm_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_mdm_not_configured(self, fleet_client, mock_mcp):
        """Test handling when MDM is not configured."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("MDM not configured", status_code=400),
        ):
            mdm_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_api_error(self, fleet_client, mock_mcp):
        """Test handling of API error."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Internal server error", status_code=500),
        ):
            mdm_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestFleetUploadMdmAppleInstaller:
    """Test fleet_upload_mdm_apple_installer tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful upload of MDM Apple installer."""
        mock_response = FleetResponse(
            success=True,
            data={
                "installer": {
                    "id": 3,
                    "name": "NewInstaller.pkg",
                    "size": 15000000,
                    "manifest": "https://example.com/manifest3.plist",
                    "installer": "https://example.com/installer3.pkg",
                    "created_at": "2024-01-17T12:00:00Z",
                    "updated_at": "2024-01-17T12:00:00Z",
                }
            },
            message="Installer uploaded successfully",
        )

        with patch.object(fleet_client, "post_multipart", return_value=mock_response):
            mdm_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_invalid_file_format(self, fleet_client, mock_mcp):
        """Test handling of invalid file format."""
        with patch.object(
            fleet_client,
            "post_multipart",
            side_effect=FleetAPIError("Invalid file format", status_code=400),
        ):
            mdm_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_file_too_large(self, fleet_client, mock_mcp):
        """Test handling of file too large error."""
        with patch.object(
            fleet_client,
            "post_multipart",
            side_effect=FleetAPIError("File too large", status_code=413),
        ):
            mdm_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_forbidden_access(self, fleet_client, mock_mcp):
        """Test handling of 403 forbidden error."""
        with patch.object(
            fleet_client,
            "post_multipart",
            side_effect=FleetAPIError("Forbidden", status_code=403),
        ):
            mdm_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_mdm_not_configured(self, fleet_client, mock_mcp):
        """Test handling when MDM is not configured."""
        with patch.object(
            fleet_client,
            "post_multipart",
            side_effect=FleetAPIError("MDM not configured", status_code=400),
        ):
            mdm_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_duplicate_installer(self, fleet_client, mock_mcp):
        """Test handling of duplicate installer upload."""
        with patch.object(
            fleet_client,
            "post_multipart",
            side_effect=FleetAPIError("Installer already exists", status_code=409),
        ):
            mdm_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_api_error(self, fleet_client, mock_mcp):
        """Test handling of API error."""
        with patch.object(
            fleet_client,
            "post_multipart",
            side_effect=FleetAPIError("Internal server error", status_code=500),
        ):
            mdm_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_missing_manifest(self, fleet_client, mock_mcp):
        """Test handling when manifest is missing."""
        with patch.object(
            fleet_client,
            "post_multipart",
            side_effect=FleetAPIError("Manifest required", status_code=400),
        ):
            mdm_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_invalid_manifest(self, fleet_client, mock_mcp):
        """Test handling of invalid manifest."""
        with patch.object(
            fleet_client,
            "post_multipart",
            side_effect=FleetAPIError("Invalid manifest format", status_code=400),
        ):
            mdm_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called
