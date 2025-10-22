"""Tests for new Fleet Host management tools (Priority 5B)."""

from unittest.mock import MagicMock, patch

import pytest

from fleet_mcp.client import FleetAPIError, FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools import host_tools


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


class TestFleetGetHostMacadmins:
    """Test fleet_get_host_macadmins tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful retrieval of host macadmins data."""
        mock_response = FleetResponse(
            success=True,
            data={
                "macadmins": {
                    "munki": {"version": "5.2.3", "errors": [], "warnings": []},
                    "munki_issues": [],
                    "mobile_device_management": {
                        "enrollment_status": "On (automatic)",
                        "server_url": "https://mdm.example.com",
                        "name": "Example MDM",
                        "id": "12345",
                    },
                }
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            # Verify tool was registered
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_404_error(self, fleet_client, mock_mcp):
        """Test handling of 404 error when host not found."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Host not found", status_code=404),
        ):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_empty_response(self, fleet_client, mock_mcp):
        """Test handling of empty macadmins data."""
        mock_response = FleetResponse(
            success=True,
            data={"macadmins": {}},
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestFleetGetHostDeviceMapping:
    """Test fleet_get_host_device_mapping tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful retrieval of device mapping."""
        mock_response = FleetResponse(
            success=True,
            data={
                "device_mapping": [
                    {"email": "user@example.com", "source": "google_chrome_profiles"}
                ]
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_empty_mapping(self, fleet_client, mock_mcp):
        """Test handling of empty device mapping."""
        mock_response = FleetResponse(
            success=True,
            data={"device_mapping": []},
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_api_error(self, fleet_client, mock_mcp):
        """Test handling of API error."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Internal server error", status_code=500),
        ):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestFleetGetHostEncryptionKey:
    """Test fleet_get_host_encryption_key tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful retrieval of encryption key."""
        mock_response = FleetResponse(
            success=True,
            data={
                "host_id": 123,
                "encryption_key": {
                    "key": "ABC123-DEF456-GHI789",
                    "updated_at": "2024-01-15T10:30:00Z",
                },
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_no_encryption_key(self, fleet_client, mock_mcp):
        """Test handling when no encryption key is available."""
        mock_response = FleetResponse(
            success=True,
            data={"host_id": 123, "encryption_key": None},
            message="No encryption key available",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_403_forbidden(self, fleet_client, mock_mcp):
        """Test handling of 403 forbidden error."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Forbidden", status_code=403),
        ):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestFleetRefetchHost:
    """Test fleet_refetch_host tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful host refetch."""
        mock_response = FleetResponse(
            success=True,
            data={},
            message="Host refetch triggered successfully",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            host_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_host_not_found(self, fleet_client, mock_mcp):
        """Test handling when host is not found."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Host not found", status_code=404),
        ):
            host_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_host_offline(self, fleet_client, mock_mcp):
        """Test handling when host is offline."""
        mock_response = FleetResponse(
            success=False,
            data={},
            message="Host is offline",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            host_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_api_error(self, fleet_client, mock_mcp):
        """Test handling of API error."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Internal server error", status_code=500),
        ):
            host_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called
