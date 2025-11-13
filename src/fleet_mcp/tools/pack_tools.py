"""Pack management tools for Fleet MCP."""

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
    """Register all pack management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only pack management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("list packs", {"data": None})
    async def fleet_list_packs(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "name",
        order_direction: str = "asc",
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """List all query packs in Fleet with optional filtering and pagination.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of packs per page
            order_key: Field to order by (name, created_at, updated_at)
            order_direction: Sort direction (asc, desc)
            team_id: Filter packs by team ID

        Returns:
            Dict containing list of packs and pagination metadata.
        """
        async with client:
            params = build_pagination_params(
                page=page,
                per_page=per_page,
                order_key=order_key,
                order_direction=order_direction,
                team_id=team_id,
            )

            response = await client.get("/api/latest/fleet/packs", params=params)
            data = response.data or {}
            return format_success_response(
                f"Retrieved {len(data.get('packs', []))} packs",
                data=data,
            )

    @mcp.tool()
    @handle_fleet_api_errors("get pack", {"data": None})
    async def fleet_get_pack(pack_id: int) -> dict[str, Any]:
        """Get detailed information about a specific pack.

        Args:
            pack_id: The ID of the pack to retrieve

        Returns:
            Dict containing detailed pack information including queries.
        """
        async with client:
            response = await client.get(f"/api/latest/fleet/packs/{pack_id}")
            return format_success_response(
                f"Retrieved pack {pack_id}",
                data=response,
            )

    @mcp.tool()
    @handle_fleet_api_errors("list scheduled queries", {"data": None})
    async def fleet_list_scheduled_queries(
        pack_id: int,
        page: int = 0,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """List scheduled queries in a specific pack.

        Args:
            pack_id: The ID of the pack
            page: Page number for pagination (0-based)
            per_page: Number of queries per page

        Returns:
            Dict containing list of scheduled queries in the pack.
        """
        async with client:
            params = build_pagination_params(
                page=page,
                per_page=per_page,
            )
            response = await client.get(
                f"/api/latest/fleet/packs/{pack_id}/scheduled",
                params=params,
            )
            return format_success_response(
                f"Retrieved scheduled queries for pack {pack_id}",
                data=response,
            )


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write pack management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("create pack", {"data": None})
    async def fleet_create_pack(
        name: str,
        description: str = "",
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new query pack in Fleet.

        Args:
            name: Name of the pack
            description: Description of the pack
            team_id: Optional team ID to assign the pack to

        Returns:
            Dict containing the created pack information.
        """
        async with client:
            payload: dict[str, Any] = {
                "name": name,
                "description": description,
            }
            if team_id is not None:
                payload["team_ids"] = [team_id]

            response = await client.post("/api/latest/fleet/packs", json_data=payload)
            return format_success_response(
                f"Created pack '{name}'",
                data=response,
            )

    @mcp.tool()
    @handle_fleet_api_errors("update pack", {"data": None})
    async def fleet_update_pack(
        pack_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing pack in Fleet.

        Args:
            pack_id: ID of the pack to update
            name: New name for the pack (optional)
            description: New description for the pack (optional)

        Returns:
            Dict containing the updated pack information.
        """
        async with client:
            payload = {}
            if name is not None:
                payload["name"] = name
            if description is not None:
                payload["description"] = description

            if not payload:
                return {
                    "success": False,
                    "message": "No update parameters provided",
                    "data": None,
                }

            response = await client.patch(
                f"/api/latest/fleet/packs/{pack_id}",
                json_data=payload,
            )
            return format_success_response(
                f"Updated pack {pack_id}",
                data=response,
            )

    @mcp.tool()
    @handle_fleet_api_errors("delete pack", {"data": None})
    async def fleet_delete_pack(pack_name: str) -> dict[str, Any]:
        """Delete a pack from Fleet by name.

        Args:
            pack_name: Name of the pack to delete

        Returns:
            Dict containing the deletion result.
        """
        async with client:
            await client.delete(f"/api/latest/fleet/packs/{pack_name}")
            return format_success_response(
                f"Deleted pack '{pack_name}'",
                data=None,
            )
