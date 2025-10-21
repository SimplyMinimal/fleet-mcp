"""Pack management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

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
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                    "order_key": order_key,
                    "order_direction": order_direction,
                }
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get("/api/latest/fleet/packs", params=params)
                data = response.data or {}
                return {
                    "success": True,
                    "message": f"Retrieved {len(data.get('packs', []))} packs",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to list packs: {e}")
            return {
                "success": False,
                "message": f"Failed to list packs: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_pack(pack_id: int) -> dict[str, Any]:
        """Get detailed information about a specific pack.

        Args:
            pack_id: The ID of the pack to retrieve

        Returns:
            Dict containing detailed pack information including queries.
        """
        try:
            async with client:
                response = await client.get(f"/api/latest/fleet/packs/{pack_id}")
                return {
                    "success": True,
                    "message": f"Retrieved pack {pack_id}",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get pack {pack_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get pack: {str(e)}",
                "data": None,
            }

    @mcp.tool()
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
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                }
                response = await client.get(
                    f"/api/latest/fleet/packs/{pack_id}/scheduled",
                    params=params,
                )
                return {
                    "success": True,
                    "message": f"Retrieved scheduled queries for pack {pack_id}",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to list scheduled queries for pack {pack_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to list scheduled queries: {str(e)}",
                "data": None,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write pack management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
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
        try:
            async with client:
                payload: dict[str, Any] = {
                    "name": name,
                    "description": description,
                }
                if team_id is not None:
                    payload["team_ids"] = [team_id]

                response = await client.post(
                    "/api/latest/fleet/packs", json_data=payload
                )
                return {
                    "success": True,
                    "message": f"Created pack '{name}'",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to create pack '{name}': {e}")
            return {
                "success": False,
                "message": f"Failed to create pack: {str(e)}",
                "data": None,
            }

    @mcp.tool()
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
        try:
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
                return {
                    "success": True,
                    "message": f"Updated pack {pack_id}",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to update pack {pack_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to update pack: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_delete_pack(pack_name: str) -> dict[str, Any]:
        """Delete a pack from Fleet by name.

        Args:
            pack_name: Name of the pack to delete

        Returns:
            Dict containing the deletion result.
        """
        try:
            async with client:
                await client.delete(f"/api/latest/fleet/packs/{pack_name}")
                return {
                    "success": True,
                    "message": f"Deleted pack '{pack_name}'",
                    "data": None,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to delete pack '{pack_name}': {e}")
            return {
                "success": False,
                "message": f"Failed to delete pack: {str(e)}",
                "data": None,
            }
