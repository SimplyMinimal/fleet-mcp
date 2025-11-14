"""Custom variable management tools for Fleet MCP.

Custom variables can be used in scripts and configuration profiles with the
$FLEET_SECRET_ prefix. These variables are hidden when viewed in the Fleet UI or API.
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all custom variable management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only custom variable management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_custom_variables(
        page: int = 0,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """List all custom variables that can be used in scripts and profiles.

        Custom variables are prefixed with $FLEET_SECRET_ when used in scripts
        and configuration profiles. The values are hidden when viewed in the
        Fleet UI or API.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of variables per page

        Returns:
            Dict containing list of custom variables (without values) and pagination metadata.

        Example:
            >>> result = await fleet_list_custom_variables()
            >>> for var in result["custom_variables"]:
            ...     print(f"ID: {var['id']}, Name: {var['name']}")
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                }

                response = await client.get(
                    "/api/v1/fleet/custom_variables", params=params
                )

                if response.success:
                    if response.data:
                        # Fleet API returns None for custom_variables when empty, not []
                        variables = response.data.get("custom_variables") or []
                        count = response.data.get("count", len(variables))
                        return {
                            "success": True,
                            "custom_variables": variables,
                            "count": count,
                            "page": page,
                            "per_page": per_page,
                            "message": f"Found {count} custom variable{'s' if count != 1 else ''}",
                        }
                    else:
                        # Success but no data - return empty list
                        return {
                            "success": True,
                            "custom_variables": [],
                            "count": 0,
                            "page": page,
                            "per_page": per_page,
                            "message": "Found 0 custom variables",
                        }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "custom_variables": [],
                        "count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list custom variables: {e}")
            return {
                "success": False,
                "message": f"Failed to list custom variables: {str(e)}",
                "custom_variables": [],
                "count": 0,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write custom variable management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_create_custom_variable(
        name: str,
        value: str,
    ) -> dict[str, Any]:
        """Create a custom variable for use in scripts and configuration profiles.

        Custom variables can be used in scripts and profiles by prefixing them
        with $FLEET_SECRET_ (e.g., $FLEET_SECRET_API_TOKEN). The variable values
        are hidden when viewed in the Fleet UI or API.

        Args:
            name: Variable name without the FLEET_SECRET_ prefix (e.g., "API_TOKEN")
            value: The value for the custom variable

        Returns:
            Dict containing the created variable's ID and name (value is not returned).

        Example:
            >>> result = await fleet_create_custom_variable(
            ...     name="API_TOKEN",
            ...     value="secret-value-here"
            ... )
            >>> print(f"Created variable with ID: {result['data']['id']}")

        Note:
            - Variable names should not include the FLEET_SECRET_ prefix
            - Values are stored securely and not returned in API responses
            - Variables are global and can be used across all teams
        """
        try:
            async with client:
                json_data = {
                    "name": name,
                    "value": value,
                }

                response = await client.post(
                    "/api/v1/fleet/custom_variables", json_data=json_data
                )

                if response.success and response.data:
                    return {
                        "success": True,
                        "data": response.data,
                        "message": f"Created custom variable '{name}' with ID {response.data.get('id')}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "data": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to create custom variable '{name}': {e}")
            return {
                "success": False,
                "message": f"Failed to create custom variable: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_delete_custom_variable(variable_id: int) -> dict[str, Any]:
        """Delete a custom variable from Fleet.

        Removes a custom variable that was previously created. This will affect
        any scripts or configuration profiles that reference this variable.

        Args:
            variable_id: ID of the custom variable to delete

        Returns:
            Dict indicating success or failure of the deletion.

        Example:
            >>> result = await fleet_delete_custom_variable(variable_id=123)
            >>> print(result["message"])

        Warning:
            Deleting a variable that is currently used in scripts or profiles
            may cause those scripts/profiles to fail when executed.
        """
        try:
            async with client:
                response = await client.delete(
                    f"/api/v1/fleet/custom_variables/{variable_id}"
                )

                if response.success:
                    return {
                        "success": True,
                        "message": f"Successfully deleted custom variable {variable_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to delete custom variable {variable_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete custom variable: {str(e)}",
            }
