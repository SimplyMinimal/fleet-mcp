"""Activity feed tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all activity feed tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only activity feed tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_activities(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "created_at",
        order_direction: str = "desc",
    ) -> dict[str, Any]:
        """List activities in Fleet.

        Returns a list of all activities (audit log) with pagination support.
        Activities include user actions, system events, and configuration changes.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of activities per page
            order_key: Column to sort by (created_at, type, actor_email)
            order_direction: Sort direction (asc or desc)

        Returns:
            Dict containing list of activities and pagination metadata.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                    "order_key": order_key,
                    "order_direction": order_direction,
                }

                response = await client.get(
                    "/api/latest/fleet/activities", params=params
                )

                # Explicit success check to prevent incorrect success reporting
                if not response.success or not response.data:
                    return {
                        "success": False,
                        "message": response.message or "No data returned from API",
                        "data": None,
                    }

                data = response.data
                activities = data.get("activities", [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(activities)} activities",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to list activities: {e}")

            # Provide helpful message for 403 Forbidden errors
            if e.status_code == 403:
                return {
                    "success": False,
                    "message": (
                        "Failed to list activities: Access denied (403 Forbidden). "
                        "This endpoint requires appropriate permissions. "
                        "Please verify that your API token has the necessary privileges."
                    ),
                    "data": None,
                }

            return {
                "success": False,
                "message": f"Failed to list activities: {str(e)}",
                "data": None,
            }
