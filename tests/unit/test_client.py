"""Tests for Fleet API client."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch

from fleet_mcp.client import FleetClient, FleetAPIError, FleetAuthenticationError
from fleet_mcp.config import FleetConfig


@pytest.fixture
def fleet_config():
    """Create a test Fleet configuration."""
    return FleetConfig(
        server_url="https://test.fleet.com",
        api_token="test-token-123456789"
    )


@pytest.fixture
def fleet_client(fleet_config):
    """Create a test Fleet client."""
    return FleetClient(fleet_config)


class TestFleetClient:
    """Test Fleet API client functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_request(self, fleet_client):
        """Test successful API request."""
        mock_response = httpx.Response(
            status_code=200,
            json={"hosts": [{"id": 1, "hostname": "test-host"}]},
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/hosts")
        )
        
        with patch.object(httpx.AsyncClient, 'request', return_value=mock_response):
            async with fleet_client:
                response = await fleet_client.get("/hosts")
                
                assert response.success is True
                assert response.data["hosts"][0]["hostname"] == "test-host"
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, fleet_client):
        """Test authentication error handling."""
        mock_response = httpx.Response(
            status_code=401,
            json={"message": "Authentication failed"},
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/hosts")
        )
        
        with patch.object(httpx.AsyncClient, 'request', return_value=mock_response):
            async with fleet_client:
                with pytest.raises(FleetAuthenticationError):
                    await fleet_client.get("/hosts")
    
    @pytest.mark.asyncio
    async def test_url_building(self, fleet_client):
        """Test URL building for API endpoints."""
        # Test endpoint without /api prefix
        url = fleet_client._build_url("/hosts")
        assert url == "/api/latest/fleet/hosts"

        # Test endpoint with /api prefix
        url = fleet_client._build_url("/api/latest/fleet/hosts")
        assert url == "/api/latest/fleet/hosts"
        
        # Test endpoint without leading slash
        url = fleet_client._build_url("hosts")
        assert url == "/api/latest/fleet/hosts"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, fleet_client):
        """Test successful health check."""
        mock_response = httpx.Response(
            status_code=200,
            json={"config": {"server_settings": {}}},
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/config")
        )
        
        with patch.object(httpx.AsyncClient, 'request', return_value=mock_response):
            async with fleet_client:
                response = await fleet_client.health_check()
                
                assert response.success is True
                assert "Fleet server is accessible" in response.message
    
    @pytest.mark.asyncio
    async def test_health_check_auth_failure(self, fleet_client):
        """Test health check with authentication failure."""
        mock_response = httpx.Response(
            status_code=401,
            json={"message": "Authentication failed"},
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/config")
        )
        
        with patch.object(httpx.AsyncClient, 'request', return_value=mock_response):
            async with fleet_client:
                response = await fleet_client.health_check()
                
                assert response.success is False
                assert "Authentication failed" in response.message
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, fleet_client):
        """Test retry logic on timeout."""
        # First call times out, second succeeds
        mock_responses = [
            httpx.TimeoutException("Request timed out"),
            httpx.Response(
                status_code=200,
                json={"hosts": []},
                request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/hosts")
            )
        ]
        
        with patch.object(httpx.AsyncClient, 'request', side_effect=mock_responses):
            async with fleet_client:
                response = await fleet_client.get("/hosts")
                
                assert response.success is True
                assert response.data["hosts"] == []
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, fleet_client):
        """Test behavior when max retries are exceeded."""
        # All calls time out
        with patch.object(httpx.AsyncClient, 'request', side_effect=httpx.TimeoutException("Timeout")):
            async with fleet_client:
                with pytest.raises(FleetAPIError, match="Request timed out after retries"):
                    await fleet_client.get("/hosts")
