"""Fleet API client for making HTTP requests to Fleet DM instances."""

import asyncio
import logging
from typing import Any

import httpx
from pydantic import BaseModel

from .config import FleetConfig

logger = logging.getLogger(__name__)


class FleetAPIError(Exception):
    """Base exception for Fleet API errors."""

    def __init__(self, message: str, status_code: int | None = None, response_data: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class FleetAuthenticationError(FleetAPIError):
    """Authentication failed with Fleet API."""
    pass


class FleetNotFoundError(FleetAPIError):
    """Resource not found in Fleet."""
    pass


class FleetValidationError(FleetAPIError):
    """Validation error from Fleet API."""
    pass


class FleetResponse(BaseModel):
    """Standardized response from Fleet API operations."""

    success: bool
    data: dict[str, Any] | None = None
    message: str
    status_code: int | None = None
    metadata: dict[str, Any] | None = None


class FleetClient:
    """HTTP client for Fleet DM API interactions."""

    def __init__(self, config: FleetConfig):
        """Initialize Fleet client with configuration.
        
        Args:
            config: Fleet configuration instance
        """
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "FleetClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.server_url,
                timeout=httpx.Timeout(self.config.timeout),
                verify=self.config.verify_ssl,
                headers={
                    "Authorization": f"Bearer {self.config.api_token}",
                    "Content-Type": "application/json",
                    "User-Agent": self.config.user_agent,
                }
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for API endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Full URL for the endpoint
        """
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        # Fleet API endpoints typically start with /api/latest/fleet/
        if not endpoint.startswith("/api/"):
            endpoint = f"/api/latest/fleet{endpoint}"

        return endpoint

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        retry_count: int = 0
    ) -> FleetResponse:
        """Make HTTP request to Fleet API with error handling and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON request body
            retry_count: Current retry attempt
            
        Returns:
            FleetResponse with standardized response data
            
        Raises:
            FleetAPIError: For various API errors
        """
        await self._ensure_client()

        url = self._build_url(endpoint)

        try:
            logger.debug(f"Making {method} request to {url}")

            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data
            )

            # Handle different response status codes
            if response.status_code == 200:
                try:
                    data = response.json()
                    return FleetResponse(
                        success=True,
                        data=data,
                        message="Request successful",
                        status_code=response.status_code
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    return FleetResponse(
                        success=True,
                        data={"raw_response": response.text},
                        message="Request successful (non-JSON response)",
                        status_code=response.status_code
                    )

            elif response.status_code == 401:
                error_data = self._parse_error_response(response)
                raise FleetAuthenticationError(
                    "Authentication failed - check your API token",
                    status_code=response.status_code,
                    response_data=error_data
                )

            elif response.status_code == 404:
                error_data = self._parse_error_response(response)
                raise FleetNotFoundError(
                    "Resource not found",
                    status_code=response.status_code,
                    response_data=error_data
                )

            elif response.status_code == 422:
                error_data = self._parse_error_response(response)
                raise FleetValidationError(
                    f"Validation error: {error_data.get('message', 'Invalid request')}",
                    status_code=response.status_code,
                    response_data=error_data
                )

            else:
                error_data = self._parse_error_response(response)
                raise FleetAPIError(
                    f"API request failed with status {response.status_code}",
                    status_code=response.status_code,
                    response_data=error_data
                )

        except httpx.TimeoutException:
            if retry_count < self.config.max_retries:
                logger.warning(f"Request timeout, retrying ({retry_count + 1}/{self.config.max_retries})")
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self._make_request(method, endpoint, params, json_data, retry_count + 1)

            raise FleetAPIError("Request timed out after retries")

        except httpx.ConnectError:
            raise FleetAPIError(f"Failed to connect to Fleet server at {self.config.server_url}")

        except FleetAPIError:
            # Don't retry Fleet API errors (auth, validation, etc.)
            raise

        except Exception as e:
            if retry_count < self.config.max_retries:
                logger.warning(f"Request failed, retrying ({retry_count + 1}/{self.config.max_retries}): {e}")
                await asyncio.sleep(2 ** retry_count)
                return await self._make_request(method, endpoint, params, json_data, retry_count + 1)

            raise FleetAPIError(f"Unexpected error: {str(e)}")

    def _parse_error_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse error response from Fleet API.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed error data
        """
        try:
            return response.json()
        except Exception:
            return {"message": response.text or "Unknown error", "status_code": response.status_code}

    # HTTP method helpers
    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> FleetResponse:
        """Make GET request."""
        return await self._make_request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json_data: dict[str, Any] | None = None) -> FleetResponse:
        """Make POST request."""
        return await self._make_request("POST", endpoint, json_data=json_data)

    async def patch(self, endpoint: str, json_data: dict[str, Any] | None = None) -> FleetResponse:
        """Make PATCH request."""
        return await self._make_request("PATCH", endpoint, json_data=json_data)

    async def delete(self, endpoint: str) -> FleetResponse:
        """Make DELETE request."""
        return await self._make_request("DELETE", endpoint)

    # Health check
    async def health_check(self) -> FleetResponse:
        """Check if Fleet server is accessible and authentication works.
        
        Returns:
            FleetResponse indicating server health
        """
        try:
            # Try to get server info as a health check
            response = await self.get("/config")
            return FleetResponse(
                success=True,
                message="Fleet server is accessible and authentication successful",
                data={"server_url": self.config.server_url},
                metadata={"health_check": True}
            )
        except FleetAuthenticationError:
            return FleetResponse(
                success=False,
                message="Authentication failed - check your API token",
                metadata={"health_check": True}
            )
        except FleetAPIError as e:
            return FleetResponse(
                success=False,
                message=f"Fleet server health check failed: {str(e)}",
                metadata={"health_check": True}
            )
