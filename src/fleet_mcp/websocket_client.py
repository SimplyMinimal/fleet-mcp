"""WebSocket client for Fleet live query results."""

import asyncio
import json
import logging
import ssl
import time
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import urlparse

import websockets
from websockets import ClientConnection

from fleet_mcp.config import FleetConfig

logger = logging.getLogger(__name__)


class FleetWebSocketClient:
    """WebSocket client for receiving Fleet live query results in real-time.

    This client connects to Fleet's WebSocket endpoint to receive streaming
    results from live query campaigns. It handles authentication, subscription
    to campaigns, and message parsing.

    Example:
        async with FleetWebSocketClient(config) as ws_client:
            await ws_client.subscribe_to_campaign(campaign_id)
            async for message in ws_client.stream_messages(timeout=60.0):
                if message["type"] == "result":
                    print(f"Got result: {message['data']}")
    """

    def __init__(self, config: FleetConfig):
        """Initialize WebSocket client.

        Args:
            config: Fleet configuration containing server URL and API token
        """
        self.config = config
        self.ws: ClientConnection | None = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to Fleet WebSocket endpoint.

        Raises:
            ConnectionError: If connection fails
        """
        # Convert https:// to wss:// or http:// to ws://
        parsed = urlparse(self.config.server_url)
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        ws_url = f"{ws_scheme}://{parsed.netloc}/api/latest/fleet/results/websocket"

        logger.info(f"Connecting to Fleet WebSocket: {ws_url}")

        try:
            # Build additional headers with authentication
            # Note: websockets 14.0+ renamed extra_headers to additional_headers
            additional_headers = {
                "Authorization": f"Bearer {self.config.api_token}",
            }

            # Configure SSL for WebSocket connection
            # The websockets library handles SSL differently than httpx:
            # - For wss:// with verify_ssl=True: Don't pass ssl parameter (library creates default context)
            # - For wss:// with verify_ssl=False: Pass custom SSL context with verification disabled
            # - For ws://: Don't pass ssl parameter
            ssl_context: ssl.SSLContext | None = None
            if ws_scheme == "wss" and not self.config.verify_ssl:
                # Disable SSL verification for wss:// connections
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                logger.debug("SSL verification disabled for WebSocket connection")

            # Connect to WebSocket with appropriate SSL configuration
            # For wss:// with verify_ssl=True, omit ssl parameter to use default verification
            # For wss:// with verify_ssl=False, pass custom SSL context
            if ssl_context is not None:
                self.ws = await websockets.connect(
                    ws_url,
                    additional_headers=additional_headers,
                    ssl=ssl_context,
                    ping_interval=20,  # Send ping every 20 seconds
                    ping_timeout=10,  # Wait 10 seconds for pong
                )
            else:
                self.ws = await websockets.connect(
                    ws_url,
                    additional_headers=additional_headers,
                    ping_interval=20,  # Send ping every 20 seconds
                    ping_timeout=10,  # Wait 10 seconds for pong
                )
            self._connected = True
            logger.info("WebSocket connection established")

        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise ConnectionError(f"Failed to connect to Fleet WebSocket: {e}") from e

    async def authenticate(self) -> None:
        """Authenticate WebSocket connection.

        Sends authentication message with API token.

        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If authentication fails
        """
        if not self.ws or not self._connected:
            raise RuntimeError("WebSocket not connected")

        logger.debug("Authenticating WebSocket connection")

        auth_msg = {
            "type": "auth",
            "data": {"token": self.config.api_token},
        }

        try:
            await self.ws.send(json.dumps(auth_msg))
            logger.debug("Authentication message sent")
        except Exception as e:
            logger.error(f"Failed to send authentication: {e}")
            raise ValueError(f"WebSocket authentication failed: {e}") from e

    async def subscribe_to_campaign(self, campaign_id: int) -> None:
        """Subscribe to live query campaign results.

        Args:
            campaign_id: ID of the campaign to subscribe to

        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If subscription fails
        """
        if not self.ws or not self._connected:
            raise RuntimeError("WebSocket not connected")

        logger.info(f"Subscribing to campaign {campaign_id}")

        subscribe_msg = {
            "type": "select_campaign",
            "data": {"campaign_id": campaign_id},
        }

        try:
            await self.ws.send(json.dumps(subscribe_msg))
            logger.debug(f"Subscription message sent for campaign {campaign_id}")
        except Exception as e:
            logger.error(f"Failed to subscribe to campaign: {e}")
            raise ValueError(f"Campaign subscription failed: {e}") from e

    async def stream_messages(
        self, timeout: float = 60.0
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream messages from WebSocket until timeout or completion.

        Yields parsed messages as they arrive. Automatically handles timeout
        and connection errors.

        Args:
            timeout: Maximum time to wait for messages (seconds)

        Yields:
            Dict containing message type and data

        Raises:
            RuntimeError: If WebSocket is not connected
        """
        if not self.ws or not self._connected:
            raise RuntimeError("WebSocket not connected")

        start_time = time.time()
        logger.debug(f"Starting message stream (timeout: {timeout}s)")

        try:
            while True:
                # Calculate remaining timeout
                elapsed = time.time() - start_time
                remaining = timeout - elapsed

                if remaining <= 0:
                    logger.info(f"WebSocket stream timed out after {timeout}s")
                    break

                try:
                    # Wait for message with remaining timeout
                    message_str = await asyncio.wait_for(
                        self.ws.recv(), timeout=remaining
                    )

                    # Parse JSON message
                    try:
                        message = json.loads(message_str)
                        msg_type = message.get("type")
                        data = message.get("data", {})

                        logger.debug(f"Received message type: {msg_type}")

                        yield {
                            "type": msg_type,
                            "data": data,
                        }

                        # Check if campaign is finished
                        if msg_type == "status" and data.get("status") == "finished":
                            logger.info("Campaign finished, stopping stream")
                            break

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse WebSocket message: {e}")
                        yield {
                            "type": "error",
                            "data": {"error": f"JSON parse error: {str(e)}"},
                        }

                except asyncio.TimeoutError:
                    logger.info(f"WebSocket stream timed out after {timeout}s")
                    break

                except websockets.exceptions.ConnectionClosed as e:
                    logger.warning(f"WebSocket connection closed: {e}")
                    break

        except Exception as e:
            logger.error(f"Error in message stream: {e}")
            yield {
                "type": "error",
                "data": {"error": str(e)},
            }

    async def close(self) -> None:
        """Close WebSocket connection."""
        if self.ws and self._connected:
            logger.info("Closing WebSocket connection")
            await self.ws.close()
            self._connected = False
            self.ws = None

    async def __aenter__(self) -> "FleetWebSocketClient":
        """Async context manager entry.

        Connects and authenticates the WebSocket connection.

        Returns:
            Self for use in async with statement
        """
        await self.connect()
        await self.authenticate()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit.

        Closes the WebSocket connection.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        await self.close()
