"""Label management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all label management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only label management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_labels(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "name",
        order_direction: str = "asc",
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """List all labels in Fleet with optional filtering and pagination.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of labels per page
            order_key: Field to order by (name, created_at, updated_at)
            order_direction: Sort direction (asc, desc)
            team_id: Filter labels by team ID

        Returns:
            Dict containing list of labels and pagination metadata.
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

                response = await client.get("/labels", params=params)

                if response.success and response.data:
                    labels = response.data.get("labels", [])
                    return {
                        "success": True,
                        "labels": labels,
                        "count": len(labels),
                        "page": page,
                        "per_page": per_page,
                        "message": f"Found {len(labels)} labels",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "labels": [],
                        "count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list labels: {e}")
            return {
                "success": False,
                "message": f"Failed to list labels: {str(e)}",
                "labels": [],
                "count": 0,
            }

    @mcp.tool()
    async def fleet_get_label(label_id: int) -> dict[str, Any]:
        """Get detailed information about a specific label.

        Args:
            label_id: The ID of the label to retrieve

        Returns:
            Dict containing detailed label information.
        """
        try:
            async with client:
                response = await client.get(f"/labels/{label_id}")

                if response.success and response.data:
                    label = response.data.get("label")
                    return {
                        "success": True,
                        "label": label,
                        "message": f"Retrieved label {label_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "label": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get label {label_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get label: {str(e)}",
                "label": None,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write label management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_create_label(
        name: str,
        description: str = "",
        query: str = "",
        platform: str = "",
    ) -> dict[str, Any]:
        """Create a new label in Fleet.

        Labels can be either dynamic (query-based) or manual (host list-based).
        - For dynamic labels: provide a query
        - For manual labels: leave query empty and use fleet_update_label to add hosts

        Args:
            name: Name of the label (required)
            description: Description of the label
            query: SQL query for dynamic labels (leave empty for manual labels)
            platform: Target platform (darwin, windows, linux, chrome, or empty for all)

        Returns:
            Dict containing the created label information.
        """
        try:
            async with client:
                json_data = {
                    "name": name,
                    "description": description,
                    "query": query,
                    "platform": platform,
                }

                response = await client.post("/labels", json_data=json_data)

                if response.success and response.data:
                    label = response.data.get("label")
                    return {
                        "success": True,
                        "label": label,
                        "message": f"Label '{name}' created successfully",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "label": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to create label '{name}': {e}")
            return {
                "success": False,
                "message": f"Failed to create label: {str(e)}",
                "label": None,
            }

    @mcp.tool()
    async def fleet_update_label(
        label_id: int,
        name: str | None = None,
        description: str | None = None,
        query: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing label in Fleet.

        Args:
            label_id: ID of the label to update
            name: New name for the label (optional)
            description: New description for the label (optional)
            query: New SQL query for the label (optional)

        Returns:
            Dict containing the updated label information.
        """
        try:
            async with client:
                json_data = {}
                if name is not None:
                    json_data["name"] = name
                if description is not None:
                    json_data["description"] = description
                if query is not None:
                    json_data["query"] = query

                response = await client.patch(
                    f"/labels/{label_id}", json_data=json_data
                )

                if response.success and response.data:
                    label = response.data.get("label")
                    return {
                        "success": True,
                        "label": label,
                        "message": f"Label {label_id} updated successfully",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "label": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to update label {label_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to update label: {str(e)}",
                "label": None,
            }

    @mcp.tool()
    async def fleet_delete_label(label_name: str) -> dict[str, Any]:
        """Delete a label from Fleet by name.

        Args:
            label_name: Name of the label to delete

        Returns:
            Dict indicating success or failure of the deletion.
        """
        try:
            async with client:
                response = await client.delete(f"/labels/{label_name}")

                return {
                    "success": response.success,
                    "message": response.message
                    or f"Label '{label_name}' deleted successfully",
                    "label_name": label_name,
                }

        except FleetAPIError as e:
            logger.error(f"Failed to delete label '{label_name}': {e}")
            return {
                "success": False,
                "message": f"Failed to delete label: {str(e)}",
                "label_name": label_name,
            }
