"""Device management tools for Fleet MCP.

This module provides tools for managing Fleet Desktop device information.
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all device management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only device management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_get_device_info(device_token: str) -> dict[str, Any]:
        """Get device information using a device token.

        This endpoint is used by Fleet Desktop to retrieve device-specific
        information using a device authentication token.

        Args:
            device_token: The device authentication token

        Returns:
            Dict containing device information.

        Example:
            >>> result = await fleet_get_device_info(device_token="abc123...")
            >>> print(result["device"])
        """
        try:
            async with client:
                response = await client.get(f"/device/{device_token}")

                if response.success and response.data:
                    return {
                        "success": True,
                        "device": response.data,
                        "message": "Retrieved device information successfully",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "device": {},
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get device info: {e}")
            return {
                "success": False,
                "message": f"Failed to get device info: {str(e)}",
                "device": {},
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write device management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    # No write tools for device management currently
    pass
