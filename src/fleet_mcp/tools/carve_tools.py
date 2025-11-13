"""Carve management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetClient
from .common import (
    build_pagination_params,
    format_success_response,
    handle_fleet_api_errors,
)

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all carve management tools with the MCP server.

    Carves are file extraction sessions initiated by osquery on hosts.
    All carve tools are read-only as carves are created by osquery agents.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("list carves", {"data": None})
    async def fleet_list_carves(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "created_at",
        order_direction: str = "desc",
    ) -> dict[str, Any]:
        """List file carving sessions in Fleet.

        Carves are file extraction sessions initiated by osquery on hosts.
        This endpoint lists all carve sessions with their metadata.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of carves per page
            order_key: Field to order by (created_at, name, host_id)
            order_direction: Sort direction (asc, desc)

        Returns:
            Dict containing list of carve sessions and pagination metadata.
        """
        async with client:
            params = build_pagination_params(
                page=page,
                per_page=per_page,
                order_key=order_key,
                order_direction=order_direction,
            )
            response = await client.get("/api/latest/fleet/carves", params=params)
            data = response.data or {}
            return format_success_response(
                f"Retrieved {len(data.get('carves', []))} carves",
                data=data,
            )

    @mcp.tool()
    @handle_fleet_api_errors("get carve", {"data": None})
    async def fleet_get_carve(carve_id: int) -> dict[str, Any]:
        """Get detailed information about a specific carve session.

        Args:
            carve_id: The ID of the carve session to retrieve

        Returns:
            Dict containing detailed carve session information including
            metadata, status, and block information.
        """
        async with client:
            response = await client.get(f"/api/latest/fleet/carves/{carve_id}")
            return format_success_response(
                f"Retrieved carve {carve_id}",
                data=response,
            )

    @mcp.tool()
    @handle_fleet_api_errors("get carve block", {"data": None})
    async def fleet_get_carve_block(
        carve_id: int,
        block_id: int,
    ) -> dict[str, Any]:
        """Get a specific block of data from a carve session.

        Carves are split into blocks for efficient transfer. This endpoint
        retrieves a specific block of the carved file.

        Args:
            carve_id: The ID of the carve session
            block_id: The ID of the block to retrieve (0-based)

        Returns:
            Dict containing the block data (base64 encoded).
        """
        async with client:
            response = await client.get(
                f"/api/latest/fleet/carves/{carve_id}/block/{block_id}"
            )
            return format_success_response(
                f"Retrieved block {block_id} from carve {carve_id}",
                data=response,
            )
