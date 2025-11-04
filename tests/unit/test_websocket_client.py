"""Unit tests for FleetWebSocketClient."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from websockets.exceptions import ConnectionClosed

from fleet_mcp.config import FleetConfig
from fleet_mcp.websocket_client import FleetWebSocketClient


@pytest.fixture
def fleet_config():
    """Create a test Fleet configuration."""
    return FleetConfig(
        server_url="https://test.fleet.com",
        api_token="test-token-123456789",
        verify_ssl=True,
    )


@pytest.fixture
def websocket_client(fleet_config):
    """Create a FleetWebSocketClient instance."""
    return FleetWebSocketClient(fleet_config)


class TestFleetWebSocketClient:
    """Test FleetWebSocketClient functionality."""

    @pytest.mark.asyncio
    async def test_init(self, websocket_client, fleet_config):
        """Test WebSocket client initialization."""
        assert websocket_client.config == fleet_config
        assert websocket_client.ws is None
        assert websocket_client._connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, websocket_client):
        """Test successful WebSocket connection."""
        mock_ws = AsyncMock()

        # Create an async context manager mock
        async def mock_connect(*args, **kwargs):
            return mock_ws

        with patch("websockets.connect", new=mock_connect):
            await websocket_client.connect()

            # Verify connection was established
            assert websocket_client.ws == mock_ws
            assert websocket_client._connected is True

    @pytest.mark.asyncio
    async def test_connect_http_url(self):
        """Test WebSocket connection with HTTP URL (should use ws://)."""
        config = FleetConfig(
            server_url="http://test.fleet.com",
            api_token="test-token",
            verify_ssl=False,
        )
        client = FleetWebSocketClient(config)

        mock_ws = AsyncMock()

        # Create an async context manager mock
        async def mock_connect(*args, **kwargs):
            return mock_ws

        with patch("websockets.connect", new=mock_connect):
            await client.connect()

            # Verify connection was established
            assert client.ws == mock_ws
            assert client._connected is True

    @pytest.mark.asyncio
    async def test_connect_verify_ssl_false(self):
        """Test WebSocket connection with SSL verification disabled."""
        config = FleetConfig(
            server_url="https://test.fleet.com",
            api_token="test-token",
            verify_ssl=False,
        )
        client = FleetWebSocketClient(config)

        mock_ws = AsyncMock()
        connect_kwargs = {}

        # Create an async context manager mock that captures kwargs
        async def mock_connect(*args, **kwargs):
            connect_kwargs.update(kwargs)
            return mock_ws

        with patch("websockets.connect", new=mock_connect):
            await client.connect()

            # Verify connection was established
            assert client.ws == mock_ws
            assert client._connected is True

            # Verify SSL context was provided (for verify_ssl=False)
            assert "ssl" in connect_kwargs
            assert connect_kwargs["ssl"] is not None

    @pytest.mark.asyncio
    async def test_connect_verify_ssl_true(self):
        """Test WebSocket connection with SSL verification enabled (default)."""
        config = FleetConfig(
            server_url="https://test.fleet.com",
            api_token="test-token",
            verify_ssl=True,
        )
        client = FleetWebSocketClient(config)

        mock_ws = AsyncMock()
        connect_kwargs = {}

        # Create an async context manager mock that captures kwargs
        async def mock_connect(*args, **kwargs):
            connect_kwargs.update(kwargs)
            return mock_ws

        with patch("websockets.connect", new=mock_connect):
            await client.connect()

            # Verify connection was established
            assert client.ws == mock_ws
            assert client._connected is True

            # Verify SSL parameter was NOT provided (library will use default SSL context)
            # This is the fix for the "ssl=None is incompatible with wss://" error
            assert "ssl" not in connect_kwargs

    @pytest.mark.asyncio
    async def test_authenticate_success(self, websocket_client):
        """Test successful authentication."""
        mock_ws = AsyncMock()
        websocket_client.ws = mock_ws
        websocket_client._connected = True

        await websocket_client.authenticate()

        # Verify auth message was sent
        mock_ws.send.assert_called_once()
        sent_message = json.loads(mock_ws.send.call_args[0][0])
        assert sent_message["type"] == "auth"
        assert sent_message["data"]["token"] == "test-token-123456789"

    @pytest.mark.asyncio
    async def test_authenticate_not_connected(self, websocket_client):
        """Test authentication fails when not connected."""
        with pytest.raises(RuntimeError, match="WebSocket not connected"):
            await websocket_client.authenticate()

    @pytest.mark.asyncio
    async def test_subscribe_to_campaign_success(self, websocket_client):
        """Test successful campaign subscription."""
        mock_ws = AsyncMock()
        websocket_client.ws = mock_ws
        websocket_client._connected = True

        campaign_id = 123
        await websocket_client.subscribe_to_campaign(campaign_id)

        # Verify subscription message was sent
        mock_ws.send.assert_called_once()
        sent_message = json.loads(mock_ws.send.call_args[0][0])
        assert sent_message["type"] == "select_campaign"
        assert sent_message["data"]["campaign_id"] == campaign_id

    @pytest.mark.asyncio
    async def test_subscribe_to_campaign_not_connected(self, websocket_client):
        """Test campaign subscription fails when not connected."""
        with pytest.raises(RuntimeError, match="WebSocket not connected"):
            await websocket_client.subscribe_to_campaign(123)

    @pytest.mark.asyncio
    async def test_stream_messages_success(self, websocket_client):
        """Test successful message streaming."""
        mock_ws = AsyncMock()
        websocket_client.ws = mock_ws
        websocket_client._connected = True

        # Mock messages to receive
        messages = [
            json.dumps({"type": "result", "data": {"host_id": 1, "rows": []}}),
            json.dumps({"type": "result", "data": {"host_id": 2, "rows": []}}),
            json.dumps({"type": "status", "data": {"status": "finished"}}),
        ]

        mock_ws.recv = AsyncMock(side_effect=messages)

        received_messages = []
        async for message in websocket_client.stream_messages(timeout=10.0):
            received_messages.append(message)

        # Verify all messages were received
        assert len(received_messages) == 3
        assert received_messages[0]["type"] == "result"
        assert received_messages[1]["type"] == "result"
        assert received_messages[2]["type"] == "status"
        assert received_messages[2]["data"]["status"] == "finished"

    @pytest.mark.asyncio
    async def test_stream_messages_timeout(self, websocket_client):
        """Test message streaming with timeout."""
        mock_ws = AsyncMock()
        websocket_client.ws = mock_ws
        websocket_client._connected = True

        # Mock recv to raise TimeoutError
        mock_ws.recv = AsyncMock(side_effect=asyncio.TimeoutError())

        received_messages = []
        async for message in websocket_client.stream_messages(timeout=0.1):
            received_messages.append(message)

        # Should exit cleanly on timeout
        assert len(received_messages) == 0

    @pytest.mark.asyncio
    async def test_stream_messages_connection_closed(self, websocket_client):
        """Test message streaming handles connection closure."""
        mock_ws = AsyncMock()
        websocket_client.ws = mock_ws
        websocket_client._connected = True

        # Mock recv to raise ConnectionClosed
        mock_ws.recv = AsyncMock(side_effect=ConnectionClosed(None, None))

        received_messages = []
        async for message in websocket_client.stream_messages(timeout=10.0):
            received_messages.append(message)

        # Should exit cleanly on connection closed
        assert len(received_messages) == 0

    @pytest.mark.asyncio
    async def test_stream_messages_not_connected(self, websocket_client):
        """Test message streaming fails when not connected."""
        with pytest.raises(RuntimeError, match="WebSocket not connected"):
            async for _ in websocket_client.stream_messages():
                pass

    @pytest.mark.asyncio
    async def test_stream_messages_error(self, websocket_client):
        """Test message streaming handles errors."""
        mock_ws = AsyncMock()
        websocket_client.ws = mock_ws
        websocket_client._connected = True

        # Mock recv to raise an exception
        mock_ws.recv = AsyncMock(side_effect=Exception("Test error"))

        received_messages = []
        async for message in websocket_client.stream_messages(timeout=10.0):
            received_messages.append(message)

        # Should receive error message
        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "error"
        assert "Test error" in received_messages[0]["data"]["error"]

    @pytest.mark.asyncio
    async def test_close_success(self, websocket_client):
        """Test successful WebSocket closure."""
        mock_ws = AsyncMock()
        websocket_client.ws = mock_ws
        websocket_client._connected = True

        await websocket_client.close()

        # Verify close was called
        mock_ws.close.assert_called_once()
        assert websocket_client._connected is False

    @pytest.mark.asyncio
    async def test_close_not_connected(self, websocket_client):
        """Test closing when not connected (should not raise error)."""
        await websocket_client.close()
        # Should complete without error
        assert websocket_client._connected is False

    @pytest.mark.asyncio
    async def test_context_manager(self, websocket_client):
        """Test async context manager support."""
        mock_ws = AsyncMock()

        # Create an async context manager mock
        async def mock_connect(*args, **kwargs):
            return mock_ws

        with patch("websockets.connect", new=mock_connect):
            async with websocket_client as client:
                assert client._connected is True
                assert client.ws == mock_ws

            # Verify close was called on exit
            mock_ws.close.assert_called_once()
            assert client._connected is False

    @pytest.mark.asyncio
    async def test_context_manager_exception(self, websocket_client):
        """Test context manager closes connection even on exception."""
        mock_ws = AsyncMock()

        # Create an async context manager mock
        async def mock_connect(*args, **kwargs):
            return mock_ws

        with patch("websockets.connect", new=mock_connect):
            with pytest.raises(ValueError):
                async with websocket_client:
                    raise ValueError("Test exception")

            # Verify close was called even after exception
            mock_ws.close.assert_called_once()
            assert websocket_client._connected is False
