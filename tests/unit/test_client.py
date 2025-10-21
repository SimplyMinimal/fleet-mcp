"""Tests for Fleet API client."""

from unittest.mock import patch

import httpx
import pytest

from fleet_mcp.client import (
    FleetAPIError,
    FleetAuthenticationError,
    FleetBadRequestError,
    FleetClient,
    FleetConflictError,
    FleetNotFoundError,
    FleetPermissionError,
    FleetValidationError,
)
from fleet_mcp.config import FleetConfig


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


class TestFleetClient:
    """Test Fleet API client functionality."""

    @pytest.mark.asyncio
    async def test_successful_request(self, fleet_client):
        """Test successful API request."""
        mock_response = httpx.Response(
            status_code=200,
            json={"hosts": [{"id": 1, "hostname": "test-host"}]},
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/hosts"),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
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
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/hosts"),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
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
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/config"),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
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
            request=httpx.Request("GET", "https://test.fleet.com/api/v1/fleet/config"),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
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
                request=httpx.Request(
                    "GET", "https://test.fleet.com/api/v1/fleet/hosts"
                ),
            ),
        ]

        with patch.object(httpx.AsyncClient, "request", side_effect=mock_responses):
            async with fleet_client:
                response = await fleet_client.get("/hosts")

                assert response.success is True
                assert response.data["hosts"] == []

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, fleet_client):
        """Test behavior when max retries are exceeded."""
        # All calls time out
        with patch.object(
            httpx.AsyncClient, "request", side_effect=httpx.TimeoutException("Timeout")
        ):
            async with fleet_client:
                with pytest.raises(
                    FleetAPIError, match="Request timed out after retries"
                ):
                    await fleet_client.get("/hosts")

    @pytest.mark.asyncio
    async def test_accepted_request_202(self, fleet_client):
        """Test that HTTP 202 (Accepted) is treated as success."""
        mock_response = httpx.Response(
            status_code=202,
            json={
                "host_id": 259,
                "execution_id": "84aca157-252b-4be3-af63-598b09204c87",
            },
            request=httpx.Request(
                "POST", "https://test.fleet.com/api/v1/fleet/scripts/run"
            ),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
            async with fleet_client:
                response = await fleet_client.post(
                    "/scripts/run",
                    json_data={"host_id": 259, "script_contents": "gpupdate /force"},
                )

                assert response.success is True
                assert response.status_code == 202
                assert (
                    response.data["execution_id"]
                    == "84aca157-252b-4be3-af63-598b09204c87"
                )
                assert (
                    "accepted" in response.message.lower()
                    or "queued" in response.message.lower()
                )

    @pytest.mark.asyncio
    async def test_bad_request_error_400(self, fleet_client):
        """Test that HTTP 400 raises FleetBadRequestError."""
        mock_response = httpx.Response(
            status_code=400,
            json={"message": "Invalid JSON format"},
            request=httpx.Request("POST", "https://test.fleet.com/api/v1/fleet/hosts"),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
            async with fleet_client:
                with pytest.raises(FleetBadRequestError) as exc_info:
                    await fleet_client.post("/hosts", json_data={"invalid": "data"})

                assert exc_info.value.status_code == 400
                assert "Invalid JSON format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_permission_error_403(self, fleet_client):
        """Test that HTTP 403 raises FleetPermissionError."""
        mock_response = httpx.Response(
            status_code=403,
            json={"message": "Scripts are disabled globally"},
            request=httpx.Request(
                "POST", "https://test.fleet.com/api/v1/fleet/scripts/run"
            ),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
            async with fleet_client:
                with pytest.raises(FleetPermissionError) as exc_info:
                    await fleet_client.post("/scripts/run", json_data={"host_id": 1})

                assert exc_info.value.status_code == 403
                assert "Scripts are disabled globally" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_not_found_error_404(self, fleet_client):
        """Test that HTTP 404 raises FleetNotFoundError."""
        mock_response = httpx.Response(
            status_code=404,
            json={"message": "Script not found"},
            request=httpx.Request(
                "GET", "https://test.fleet.com/api/v1/fleet/scripts/999"
            ),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
            async with fleet_client:
                with pytest.raises(FleetNotFoundError) as exc_info:
                    await fleet_client.get("/scripts/999")

                assert exc_info.value.status_code == 404
                assert "Script not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_conflict_error_409(self, fleet_client):
        """Test that HTTP 409 raises FleetConflictError."""
        mock_response = httpx.Response(
            status_code=409,
            json={"message": "Script already queued on host"},
            request=httpx.Request(
                "POST", "https://test.fleet.com/api/v1/fleet/scripts/run"
            ),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
            async with fleet_client:
                with pytest.raises(FleetConflictError) as exc_info:
                    await fleet_client.post("/scripts/run", json_data={"host_id": 1})

                assert exc_info.value.status_code == 409
                assert "Script already queued on host" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_error_422(self, fleet_client):
        """Test that HTTP 422 raises FleetValidationError."""
        mock_response = httpx.Response(
            status_code=422,
            json={"message": "Host does not have fleetd installed"},
            request=httpx.Request(
                "POST", "https://test.fleet.com/api/v1/fleet/scripts/run"
            ),
        )

        with patch.object(httpx.AsyncClient, "request", return_value=mock_response):
            async with fleet_client:
                with pytest.raises(FleetValidationError) as exc_info:
                    await fleet_client.post("/scripts/run", json_data={"host_id": 1})

                assert exc_info.value.status_code == 422
                assert "Host does not have fleetd installed" in str(exc_info.value)
