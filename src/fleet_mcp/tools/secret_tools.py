"""Secret variable management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all secret variable management tools with the MCP server.

    Secret variables are encrypted values that can be used in scripts and profiles.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only secret variable management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_secrets(
        page: int = 0,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """List secret variables in Fleet.

        Secret variables are encrypted values that can be used in scripts and profiles.
        This endpoint returns only the names and IDs, not the actual secret values.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of secrets per page

        Returns:
            Dict containing list of secret variable identifiers.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                }
                response = await client.get(
                    "/api/latest/fleet/custom_variables",
                    params=params,
                )
                data = response.data or {}
                return {
                    "success": True,
                    "message": f"Retrieved {data.get('count', 0)} secret variables",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to list secret variables: {e}")
            return {
                "success": False,
                "message": f"Failed to list secret variables: {str(e)}",
                "data": None,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write secret variable management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_create_secret(
        name: str,
        value: str,
    ) -> dict[str, Any]:
        """Create a new secret variable in Fleet.

        Secret variables are encrypted values that can be used in scripts and profiles.
        The value is encrypted server-side using Fleet's private key.

        Args:
            name: Name of the secret variable (must be unique)
            value: Value of the secret (will be encrypted)

        Returns:
            Dict containing the created secret variable information.
        """
        try:
            async with client:
                payload = {
                    "name": name,
                    "value": value,
                }
                response = await client.post(
                    "/api/latest/fleet/custom_variables",
                    json_data=payload,
                )
                return {
                    "success": True,
                    "message": f"Created secret variable '{name}'",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to create secret variable '{name}': {e}")
            return {
                "success": False,
                "message": f"Failed to create secret variable: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_delete_secret(secret_id: int) -> dict[str, Any]:
        """Delete a secret variable from Fleet by ID.

        Args:
            secret_id: ID of the secret variable to delete

        Returns:
            Dict containing the deletion result.
        """
        try:
            async with client:
                await client.delete(
                    f"/api/latest/fleet/custom_variables/{secret_id}"
                )
                return {
                    "success": True,
                    "message": f"Deleted secret variable {secret_id}",
                    "data": None,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to delete secret variable {secret_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete secret variable: {str(e)}",
                "data": None,
            }

