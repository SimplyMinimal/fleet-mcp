"""VPP (Volume Purchase Program) / App Store tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetClient
from .common import format_success_response, handle_fleet_api_errors

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all VPP/App Store management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only VPP/App Store management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("list App Store apps", {"data": None})
    async def fleet_list_app_store_apps(team_id: int | None = None) -> dict[str, Any]:
        """List App Store apps available for installation.

        Returns a list of VPP (Volume Purchase Program) apps that are
        available for installation on Apple devices.

        Args:
            team_id: Optional team ID to filter apps

        Returns:
            Dict containing list of App Store apps.

        Example:
            >>> result = await fleet_list_app_store_apps(team_id=1)
            >>> print(result)
            {
                "success": True,
                "message": "Retrieved 5 App Store apps",
                "data": {
                    "app_store_apps": [
                        {
                            "id": 1,
                            "name": "Slack",
                            "bundle_identifier": "com.tinyspeck.slackmacgap",
                            "version": "4.35.0",
                            "platform": "darwin"
                        }
                    ]
                }
            }
        """
        async with client:
            params = {}
            if team_id is not None:
                params["team_id"] = team_id

            response = await client.get(
                "/api/latest/fleet/software/app_store_apps",
                params=params if params else None,
            )
            data = response.data or {}
            apps = data.get("app_store_apps", [])

            return format_success_response(
                f"Retrieved {len(apps)} App Store apps",
                data=data,
            )

    @mcp.tool()
    @handle_fleet_api_errors("list VPP tokens", {"data": None})
    async def fleet_list_vpp_tokens() -> dict[str, Any]:
        """List VPP tokens configured in Fleet.

        Returns a list of Volume Purchase Program tokens that are
        configured for App Store app distribution.

        Returns:
            Dict containing list of VPP tokens.
        """
        async with client:
            response = await client.get("/api/latest/fleet/vpp_tokens")
            data = response.data or {}
            tokens = data.get("vpp_tokens", [])

            return format_success_response(
                f"Retrieved {len(tokens)} VPP tokens",
                data=data,
            )


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write VPP/App Store management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("add App Store app", {"data": None})
    async def fleet_add_app_store_app(
        app_store_id: str,
        platform: str,
        team_id: int | None = None,
        self_service: bool = False,
        automatic_install: bool = False,
        labels_include_any: list[str] | None = None,
        labels_exclude_any: list[str] | None = None,
    ) -> dict[str, Any]:
        """Add an App Store app for installation.

        Adds a VPP app from the App Store to Fleet for distribution
        to Apple devices.

        Args:
            app_store_id: The App Store ID (Adam ID) of the app
            platform: Platform for the app (ios, ipados, darwin)
            team_id: Optional team ID to assign the app to
            self_service: Whether users can install the app themselves
            automatic_install: Whether to automatically install on all devices
            labels_include_any: Optional list of labels - install if host has any
            labels_exclude_any: Optional list of labels - don't install if host has any

        Returns:
            Dict containing the software title ID of the added app.
        """
        async with client:
            payload: dict[str, Any] = {
                "app_store_id": app_store_id,
                "platform": platform,
                "self_service": self_service,
                "automatic_install": automatic_install,
            }
            if team_id is not None:
                payload["team_id"] = team_id
            if labels_include_any is not None:
                payload["labels_include_any"] = labels_include_any
            if labels_exclude_any is not None:
                payload["labels_exclude_any"] = labels_exclude_any

            response = await client.post(
                "/api/latest/fleet/software/app_store_apps", json_data=payload
            )
            data = response.data or {}
            title_id = data.get("software_title_id")

            return format_success_response(
                f"Added App Store app {app_store_id} (title ID: {title_id})",
                data=data,
            )

    @mcp.tool()
    @handle_fleet_api_errors("update App Store app", {"data": None})
    async def fleet_update_app_store_app(
        title_id: int,
        team_id: int | None = None,
        self_service: bool = False,
        labels_include_any: list[str] | None = None,
        labels_exclude_any: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update an App Store app's settings.

        Updates the configuration of an existing App Store app,
        such as self-service availability and label filters.

        Args:
            title_id: Software title ID of the app
            team_id: Optional team ID
            self_service: Whether users can install the app themselves
            labels_include_any: Optional list of labels - install if host has any
            labels_exclude_any: Optional list of labels - don't install if host has any

        Returns:
            Dict containing the updated app information.
        """
        async with client:
            payload: dict[str, Any] = {
                "self_service": self_service,
            }
            if team_id is not None:
                payload["team_id"] = team_id
            if labels_include_any is not None:
                payload["labels_include_any"] = labels_include_any
            if labels_exclude_any is not None:
                payload["labels_exclude_any"] = labels_exclude_any

            response = await client.patch(
                f"/api/latest/fleet/software/titles/{title_id}/app_store_app",
                json_data=payload,
            )

            return format_success_response(
                f"Updated App Store app (title ID: {title_id})",
                data=response,
            )

    @mcp.tool()
    @handle_fleet_api_errors("delete VPP token", {"data": None})
    async def fleet_delete_vpp_token(token_id: int) -> dict[str, Any]:
        """Delete a VPP token.

        Removes a Volume Purchase Program token from Fleet. This will
        also remove all associated App Store apps.

        Args:
            token_id: ID of the VPP token to delete

        Returns:
            Dict containing the result of the deletion.
        """
        async with client:
            await client.delete(f"/api/latest/fleet/vpp_tokens/{token_id}")

            return format_success_response(
                f"VPP token {token_id} deleted successfully",
                data=None,
            )
