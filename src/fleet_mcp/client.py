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

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class FleetAuthenticationError(FleetAPIError):
    """Authentication failed with Fleet API (401 Unauthorized)."""

    pass


class FleetPermissionError(FleetAPIError):
    """Permission denied or feature disabled (403 Forbidden)."""

    pass


class FleetNotFoundError(FleetAPIError):
    """Resource not found in Fleet (404 Not Found)."""

    pass


class FleetConflictError(FleetAPIError):
    """Resource conflict (409 Conflict)."""

    pass


class FleetValidationError(FleetAPIError):
    """Validation or business logic error (422 Unprocessable Entity)."""

    pass


class FleetBadRequestError(FleetAPIError):
    """Bad request or malformed input (400 Bad Request)."""

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

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
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
                },
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
        retry_count: int = 0,
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
        assert self._client is not None  # Ensured by _ensure_client()

        url = self._build_url(endpoint)

        try:
            logger.debug(f"Making {method} request to {url}")

            response = await self._client.request(
                method=method, url=url, params=params, json=json_data
            )

            # Handle different response status codes
            if response.status_code in (200, 202, 204):
                # 204 No Content is a success response with no body (e.g., DELETE)
                if response.status_code == 204:
                    return FleetResponse(
                        success=True,
                        data={},
                        message="Request successful (no content)",
                        status_code=response.status_code,
                    )

                try:
                    data = response.json()
                    message = "Request successful"
                    if response.status_code == 202:
                        message = "Request accepted (queued for processing)"
                    return FleetResponse(
                        success=True,
                        data=data,
                        message=message,
                        status_code=response.status_code,
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    message = "Request successful (non-JSON response)"
                    if response.status_code == 202:
                        message = "Request accepted (non-JSON response)"
                    return FleetResponse(
                        success=True,
                        data={"raw_response": response.text},
                        message=message,
                        status_code=response.status_code,
                    )

            elif response.status_code == 400:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Bad request - malformed input")
                raise FleetBadRequestError(
                    f"Bad request: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 401:
                error_data = self._parse_error_response(response)
                raise FleetAuthenticationError(
                    "Authentication failed - check your API token",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 403:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get(
                    "message", "Permission denied or feature disabled"
                )
                raise FleetPermissionError(
                    f"Forbidden: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 404:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Resource not found")
                raise FleetNotFoundError(
                    f"Not found: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 409:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Resource conflict")
                raise FleetConflictError(
                    f"Conflict: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 422:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Invalid request")
                raise FleetValidationError(
                    f"Validation error: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            else:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get(
                    "message", f"Request failed with status {response.status_code}"
                )
                raise FleetAPIError(
                    f"API error: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

        except httpx.TimeoutException as e:
            if retry_count < self.config.max_retries:
                logger.warning(
                    f"Request timeout, retrying ({retry_count + 1}/{self.config.max_retries})"
                )
                await asyncio.sleep(2**retry_count)  # Exponential backoff
                return await self._make_request(
                    method, endpoint, params, json_data, retry_count + 1
                )

            raise FleetAPIError("Request timed out after retries") from e

        except httpx.ConnectError as e:
            raise FleetAPIError(
                f"Failed to connect to Fleet server at {self.config.server_url}"
            ) from e

        except FleetAPIError:
            # Don't retry Fleet API errors (auth, validation, etc.)
            raise

        except Exception as e:
            if retry_count < self.config.max_retries:
                logger.warning(
                    f"Request failed, retrying ({retry_count + 1}/{self.config.max_retries}): {e}"
                )
                await asyncio.sleep(2**retry_count)
                return await self._make_request(
                    method, endpoint, params, json_data, retry_count + 1
                )

            raise FleetAPIError(f"Unexpected error: {str(e)}") from e

    def _parse_error_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse error response from Fleet API.

        Args:
            response: HTTP response object

        Returns:
            Parsed error data
        """
        try:
            json_data = response.json()
            if isinstance(json_data, dict):
                return json_data
            return {"message": str(json_data), "status_code": response.status_code}
        except Exception:
            return {
                "message": response.text or "Unknown error",
                "status_code": response.status_code,
            }

    # HTTP method helpers
    async def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> FleetResponse:
        """Make GET request."""
        return await self._make_request("GET", endpoint, params=params)

    async def post(
        self, endpoint: str, json_data: dict[str, Any] | None = None
    ) -> FleetResponse:
        """Make POST request."""
        return await self._make_request("POST", endpoint, json_data=json_data)

    async def patch(
        self, endpoint: str, json_data: dict[str, Any] | None = None
    ) -> FleetResponse:
        """Make PATCH request."""
        return await self._make_request("PATCH", endpoint, json_data=json_data)

    async def delete(
        self, endpoint: str, json_data: dict[str, Any] | None = None
    ) -> FleetResponse:
        """Make DELETE request."""
        return await self._make_request("DELETE", endpoint, json_data=json_data)

    async def post_multipart(
        self,
        endpoint: str,
        files: dict[str, tuple[str, str]] | None = None,
        data: dict[str, str] | None = None,
    ) -> FleetResponse:
        """Make POST request with multipart form data.

        Args:
            endpoint: API endpoint
            files: Dict of files to upload {field_name: (filename, content)}
            data: Dict of form data fields

        Returns:
            FleetResponse with standardized response data
        """
        await self._ensure_client()
        assert self._client is not None

        url = self._build_url(endpoint)

        try:
            logger.debug(f"Making POST multipart request to {url}")

            # For multipart requests, we need to use a client without the default
            # Content-Type header so httpx can set it with the correct multipart boundary
            # Create a temporary client with only Authorization header
            temp_headers = {
                "Authorization": f"Bearer {self.config.api_token}",
                "User-Agent": self.config.user_agent,
            }

            async with httpx.AsyncClient(
                base_url=self.config.server_url,
                timeout=httpx.Timeout(self.config.timeout),
                verify=self.config.verify_ssl,
                headers=temp_headers,
            ) as temp_client:
                response = await temp_client.post(url, files=files, data=data)

            if response.status_code == 200 or response.status_code == 202:
                try:
                    data_response = response.json()
                    message = "Request successful"
                    if response.status_code == 202:
                        message = "Request accepted (queued for processing)"
                    return FleetResponse(
                        success=True,
                        data=data_response,
                        message=message,
                        status_code=response.status_code,
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    message = "Request successful (non-JSON response)"
                    if response.status_code == 202:
                        message = "Request accepted (non-JSON response)"
                    return FleetResponse(
                        success=True,
                        data={"raw_response": response.text},
                        message=message,
                        status_code=response.status_code,
                    )

            elif response.status_code == 400:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Bad request - malformed input")
                raise FleetBadRequestError(
                    f"Bad request: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 401:
                error_data = self._parse_error_response(response)
                raise FleetAuthenticationError(
                    "Authentication failed - check your API token",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 403:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get(
                    "message", "Permission denied or feature disabled"
                )
                raise FleetPermissionError(
                    f"Forbidden: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 404:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Resource not found")
                raise FleetNotFoundError(
                    f"Not found: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 409:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Resource conflict")
                raise FleetConflictError(
                    f"Conflict: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 422:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Invalid request")
                raise FleetValidationError(
                    f"Validation error: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            else:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get(
                    "message", f"Request failed with status {response.status_code}"
                )
                logger.error(
                    f"POST multipart failed with status {response.status_code}: {error_data}"
                )
                raise FleetAPIError(
                    f"API error: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

        except FleetAPIError:
            raise
        except Exception as e:
            logger.error(f"Multipart request exception: {str(e)}")
            raise FleetAPIError(f"Multipart request failed: {str(e)}") from e

    async def patch_multipart(
        self,
        endpoint: str,
        files: dict[str, tuple[str, str]] | None = None,
        data: dict[str, str] | None = None,
    ) -> FleetResponse:
        """Make PATCH request with multipart form data.

        Args:
            endpoint: API endpoint
            files: Dict of files to upload {field_name: (filename, content)}
            data: Dict of form data fields

        Returns:
            FleetResponse with standardized response data
        """
        await self._ensure_client()
        assert self._client is not None

        url = self._build_url(endpoint)

        try:
            logger.debug(f"Making PATCH multipart request to {url}")

            # For multipart requests, we need to use a client without the default
            # Content-Type header so httpx can set it with the correct multipart boundary
            # Create a temporary client with only Authorization header
            temp_headers = {
                "Authorization": f"Bearer {self.config.api_token}",
                "User-Agent": self.config.user_agent,
            }

            async with httpx.AsyncClient(
                base_url=self.config.server_url,
                timeout=httpx.Timeout(self.config.timeout),
                verify=self.config.verify_ssl,
                headers=temp_headers,
            ) as temp_client:
                response = await temp_client.patch(url, files=files, data=data)

            if response.status_code == 200 or response.status_code == 202:
                try:
                    data_response = response.json()
                    message = "Request successful"
                    if response.status_code == 202:
                        message = "Request accepted (queued for processing)"
                    return FleetResponse(
                        success=True,
                        data=data_response,
                        message=message,
                        status_code=response.status_code,
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    message = "Request successful (non-JSON response)"
                    if response.status_code == 202:
                        message = "Request accepted (non-JSON response)"
                    return FleetResponse(
                        success=True,
                        data={"raw_response": response.text},
                        message=message,
                        status_code=response.status_code,
                    )

            elif response.status_code == 400:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Bad request - malformed input")
                raise FleetBadRequestError(
                    f"Bad request: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 401:
                error_data = self._parse_error_response(response)
                raise FleetAuthenticationError(
                    "Authentication failed - check your API token",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 403:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get(
                    "message", "Permission denied or feature disabled"
                )
                raise FleetPermissionError(
                    f"Forbidden: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 404:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Resource not found")
                raise FleetNotFoundError(
                    f"Not found: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 409:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Resource conflict")
                raise FleetConflictError(
                    f"Conflict: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            elif response.status_code == 422:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get("message", "Invalid request")
                raise FleetValidationError(
                    f"Validation error: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            else:
                error_data = self._parse_error_response(response)
                error_msg = error_data.get(
                    "message", f"Request failed with status {response.status_code}"
                )
                raise FleetAPIError(
                    f"API error: {error_msg}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

        except FleetAPIError:
            raise
        except Exception as e:
            raise FleetAPIError(f"Multipart request failed: {str(e)}") from e

    # Health check
    async def health_check(self) -> FleetResponse:
        """Check if Fleet server is accessible and authentication works.

        Returns:
            FleetResponse indicating server health
        """
        try:
            # Try to get server info as a health check
            await self.get("/config")
            return FleetResponse(
                success=True,
                message="Fleet server is accessible and authentication successful",
                data={"server_url": self.config.server_url},
                metadata={"health_check": True},
            )
        except FleetAuthenticationError:
            return FleetResponse(
                success=False,
                message="Authentication failed - check your API token",
                metadata={"health_check": True},
            )
        except FleetAPIError as e:
            return FleetResponse(
                success=False,
                message=f"Fleet server health check failed: {str(e)}",
                metadata={"health_check": True},
            )

    async def get_current_user(self) -> FleetResponse:
        """Get information about the currently authenticated user.

        Returns:
            FleetResponse containing user information including role, email, name, etc.
        """
        try:
            response = await self.get("/api/v1/fleet/me")
            return response
        except FleetAPIError as e:
            logger.warning(f"Failed to get current user info: {e}")
            return FleetResponse(
                success=False,
                message=f"Failed to get current user info: {str(e)}",
                data=None,
            )
