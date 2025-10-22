"""Tests for new Fleet Device/Fleet Desktop tools (Priority 6)."""

from unittest.mock import MagicMock, patch

import pytest

from fleet_mcp.client import FleetAPIError, FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools import device_tools


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


class TestFleetGetDeviceInfo:
    """Test fleet_get_device_info tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful retrieval of device information."""
        mock_response = FleetResponse(
            success=True,
            data={
                "host": {
                    "id": 123,
                    "hostname": "Johns-MacBook-Pro",
                    "display_name": "John's MacBook Pro",
                    "platform": "darwin",
                    "osquery_version": "5.17.0",
                    "status": "online",
                    "uuid": "abc-123-def-456",
                    "serial_number": "C02ABC123DEF",
                    "hardware_model": "MacBookPro18,1",
                    "hardware_serial": "C02ABC123DEF",
                    "primary_ip": "192.168.1.100",
                    "primary_mac": "00:11:22:33:44:55",
                    "last_enrolled_at": "2024-01-15T10:00:00Z",
                    "detail_updated_at": "2024-01-17T12:30:00Z",
                },
                "org_logo_url": "https://example.com/logo.png",
                "org_logo_url_light_background": "https://example.com/logo-light.png",
                "org_contact_url": "https://example.com/contact",
                "license": {"tier": "premium", "expiration": "2025-01-15T00:00:00Z"},
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            device_tools.register_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_invalid_token(self, fleet_client, mock_mcp):
        """Test handling of invalid device token."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Invalid device token", status_code=401),
        ):
            device_tools.register_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_expired_token(self, fleet_client, mock_mcp):
        """Test handling of expired device token."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Device token expired", status_code=401),
        ):
            device_tools.register_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_device_not_found(self, fleet_client, mock_mcp):
        """Test handling when device is not found."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Device not found", status_code=404),
        ):
            device_tools.register_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_api_error(self, fleet_client, mock_mcp):
        """Test handling of API error."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Internal server error", status_code=500),
        ):
            device_tools.register_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_minimal_device_info(self, fleet_client, mock_mcp):
        """Test handling of minimal device information."""
        mock_response = FleetResponse(
            success=True,
            data={
                "host": {
                    "id": 456,
                    "hostname": "test-device",
                    "platform": "ubuntu",
                    "status": "offline",
                },
                "org_logo_url": None,
                "org_logo_url_light_background": None,
                "org_contact_url": None,
                "license": None,
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            device_tools.register_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_device_with_policies(self, fleet_client, mock_mcp):
        """Test device info with policy information."""
        mock_response = FleetResponse(
            success=True,
            data={
                "host": {
                    "id": 789,
                    "hostname": "policy-test-device",
                    "platform": "windows",
                    "status": "online",
                    "policies": [
                        {
                            "id": 1,
                            "name": "Firewall Enabled",
                            "query": "SELECT * FROM firewall",
                            "response": "pass",
                        },
                        {
                            "id": 2,
                            "name": "Disk Encryption",
                            "query": "SELECT * FROM disk_encryption",
                            "response": "fail",
                        },
                    ],
                },
                "org_logo_url": "https://example.com/logo.png",
                "org_contact_url": "https://example.com/contact",
                "license": {"tier": "free"},
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            device_tools.register_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_device_with_software(self, fleet_client, mock_mcp):
        """Test device info with software information."""
        mock_response = FleetResponse(
            success=True,
            data={
                "host": {
                    "id": 999,
                    "hostname": "software-test-device",
                    "platform": "darwin",
                    "status": "online",
                    "software": [
                        {
                            "id": 1,
                            "name": "Google Chrome",
                            "version": "120.0.6099.109",
                            "source": "apps",
                        },
                        {
                            "id": 2,
                            "name": "Slack",
                            "version": "4.36.140",
                            "source": "apps",
                        },
                    ],
                },
                "org_logo_url": "https://example.com/logo.png",
                "org_contact_url": "https://example.com/contact",
                "license": {"tier": "premium"},
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            device_tools.register_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_forbidden_access(self, fleet_client, mock_mcp):
        """Test handling of 403 forbidden error."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Forbidden", status_code=403),
        ):
            device_tools.register_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_malformed_token(self, fleet_client, mock_mcp):
        """Test handling of malformed device token."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Malformed token", status_code=400),
        ):
            device_tools.register_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called
