"""Invite management tools for Fleet MCP."""

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
    """Register all invite management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only invite management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("list invites", {"data": None})
    async def fleet_list_invites(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "created_at",
        order_direction: str = "desc",
    ) -> dict[str, Any]:
        """List all pending user invites in Fleet.

        Invites are sent to users to join Fleet. This endpoint lists all
        pending invites that haven't been accepted yet.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of invites per page
            order_key: Field to order by (created_at, email, name)
            order_direction: Sort direction (asc, desc)

        Returns:
            Dict containing list of pending invites.
        """
        async with client:
            params = build_pagination_params(
                page=page,
                per_page=per_page,
                order_key=order_key,
                order_direction=order_direction,
            )
            response = await client.get("/api/latest/fleet/invites", params=params)
            data = response.data or {}
            invites = data.get("invites", [])
            return format_success_response(
                f"Retrieved {len(invites)} pending invites",
                data=data,
            )

    @mcp.tool()
    @handle_fleet_api_errors("verify invite token", {"data": None})
    async def fleet_verify_invite(token: str) -> dict[str, Any]:
        """Verify an invite token and get invite details.

        This endpoint verifies that an invite token is valid and returns
        the invite details. Used when a user clicks an invite link.

        Args:
            token: The invite token from the invite email

        Returns:
            Dict containing the invite details if valid.
        """
        async with client:
            params = {"token": token}
            response = await client.get(
                "/api/latest/fleet/invites/verify", params=params
            )
            return format_success_response(
                "Invite token is valid",
                data=response,
            )


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write invite management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("create invite", {"data": None})
    async def fleet_create_invite(
        email: str,
        name: str | None = None,
        position: str | None = None,
        global_role: str | None = None,
        teams: list[dict[str, Any]] | None = None,
        sso_enabled: bool = False,
    ) -> dict[str, Any]:
        """Create a new user invite in Fleet.

        Sends an invitation email to a user to join Fleet. The user can be
        assigned a global role or team-specific roles.

        Global roles: admin, maintainer, observer, observer_plus, gitops
        Team roles: admin, maintainer, observer, observer_plus, gitops

        Args:
            email: Email address of the user to invite (required)
            name: Full name of the user
            position: Job position/title of the user
            global_role: Global role (admin, maintainer, observer, observer_plus, gitops)
            teams: List of team assignments with roles, e.g. [{"id": 1, "role": "observer"}]
            sso_enabled: Whether SSO is enabled for this user

        Returns:
            Dict containing the created invite information.
        """
        async with client:
            payload: dict[str, Any] = {
                "email": email,
                "sso_enabled": sso_enabled,
            }

            if name is not None:
                payload["name"] = name
            if position is not None:
                payload["position"] = position
            if global_role is not None:
                payload["global_role"] = global_role
            if teams is not None:
                payload["teams"] = teams

            response = await client.post("/api/latest/fleet/invites", json_data=payload)
            invite_data = response.data or {}
            invite = invite_data.get("invite", {})
            return format_success_response(
                f"Invite sent to {email}",
                data=invite,
            )

    @mcp.tool()
    @handle_fleet_api_errors("update invite", {"data": None})
    async def fleet_update_invite(
        invite_id: int,
        name: str | None = None,
        position: str | None = None,
        global_role: str | None = None,
        teams: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update an existing invite in Fleet.

        Allows modifying the role and team assignments of a pending invite
        before it's accepted.

        Args:
            invite_id: ID of the invite to update
            name: New name for the user
            position: New position for the user
            global_role: New global role (admin, maintainer, observer, observer_plus, gitops)
            teams: New team assignments with roles

        Returns:
            Dict containing the updated invite information.
        """
        async with client:
            payload: dict[str, Any] = {}

            if name is not None:
                payload["name"] = name
            if position is not None:
                payload["position"] = position
            if global_role is not None:
                payload["global_role"] = global_role
            if teams is not None:
                payload["teams"] = teams

            if not payload:
                from .common import format_error_response

                return format_error_response(
                    "No update parameters provided",
                    data=None,
                )

            response = await client.patch(
                f"/api/latest/fleet/invites/{invite_id}",
                json_data=payload,
            )
            return format_success_response(
                f"Updated invite {invite_id}",
                data=response,
            )

    @mcp.tool()
    @handle_fleet_api_errors("delete invite", {"data": None})
    async def fleet_delete_invite(invite_id: int) -> dict[str, Any]:
        """Delete a pending invite from Fleet.

        Cancels a pending invite. The invite token will no longer be valid.

        Args:
            invite_id: ID of the invite to delete

        Returns:
            Dict containing the deletion result.
        """
        async with client:
            await client.delete(f"/api/latest/fleet/invites/{invite_id}")
            return format_success_response(
                f"Deleted invite {invite_id}",
                data=None,
            )
