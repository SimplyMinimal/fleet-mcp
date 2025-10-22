"""User and session management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all user and session management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only user and session management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_users(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "name",
        order_direction: str = "asc",
        query: str = "",
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """List users in Fleet.

        Returns a list of all users with pagination and filtering support.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of users per page
            order_key: Column to sort by (name, email, created_at, etc.)
            order_direction: Sort direction (asc or desc)
            query: Search query to filter users
            team_id: Optional team ID to filter users by team

        Returns:
            Dict containing list of users.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                    "order_key": order_key,
                    "order_direction": order_direction,
                }
                if query:
                    params["query"] = query
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get("/api/latest/fleet/users", params=params)

                # Explicit success check to prevent incorrect success reporting
                if not response.success or not response.data:
                    return {
                        "success": False,
                        "message": response.message or "No data returned from API",
                        "data": None,
                    }

                data = response.data
                users = data.get("users", [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(users)} users",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to list users: {e}")

            # Provide helpful message for 403 Forbidden errors
            if e.status_code == 403:
                return {
                    "success": False,
                    "message": (
                        "Failed to list users: Access denied (403 Forbidden). "
                        "This endpoint requires admin-level permissions. "
                        "Please verify that your API token has admin privileges."
                    ),
                    "data": None,
                }

            return {
                "success": False,
                "message": f"Failed to list users: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_user(
        user_id: int, include_ui_settings: bool = False
    ) -> dict[str, Any]:
        """Get user details by ID.

        Returns detailed information about a specific user including
        their roles, teams, and optionally UI settings.

        Args:
            user_id: ID of the user to retrieve
            include_ui_settings: Whether to include UI settings in response

        Returns:
            Dict containing user details.
        """
        try:
            async with client:
                params = {}
                if include_ui_settings:
                    params["include_ui_settings"] = "true"

                response = await client.get(
                    f"/api/latest/fleet/users/{user_id}",
                    params=params if params else None,
                )

                # Explicit success check to prevent incorrect success reporting
                if not response.success or not response.data:
                    return {
                        "success": False,
                        "message": response.message or "No data returned from API",
                        "user_id": user_id,
                        "data": None,
                    }

                return {
                    "success": True,
                    "message": f"Retrieved user {user_id}",
                    "data": response.data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get user {user_id}: {e}")

            # Provide helpful message for 403 Forbidden errors
            if e.status_code == 403:
                return {
                    "success": False,
                    "message": (
                        "Failed to get user: Access denied (403 Forbidden). "
                        "This endpoint requires admin-level permissions. "
                        "Please verify that your API token has admin privileges."
                    ),
                    "user_id": user_id,
                    "data": None,
                }

            return {
                "success": False,
                "message": f"Failed to get user {user_id}: {str(e)}",
                "user_id": user_id,
                "data": None,
            }

    @mcp.tool()
    async def fleet_list_user_sessions(user_id: int) -> dict[str, Any]:
        """List active sessions for a user.

        Returns all active sessions for a specific user.

        Args:
            user_id: ID of the user

        Returns:
            Dict containing list of user sessions.
        """
        try:
            async with client:
                response = await client.get(
                    f"/api/latest/fleet/users/{user_id}/sessions"
                )
                data = response.data or {}
                sessions = data.get("sessions", [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(sessions)} sessions for user {user_id}",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to list sessions for user {user_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to list user sessions: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_session(session_id: int) -> dict[str, Any]:
        """Get session details by ID.

        Returns information about a specific session.

        Args:
            session_id: ID of the session

        Returns:
            Dict containing session details.
        """
        try:
            async with client:
                response = await client.get(f"/api/latest/fleet/sessions/{session_id}")
                return {
                    "success": True,
                    "message": f"Retrieved session {session_id}",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get session: {str(e)}",
                "data": None,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write user and session management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_create_user(
        name: str,
        email: str,
        password: str | None = None,
        global_role: str | None = None,
        teams: list[dict[str, Any]] | None = None,
        sso_enabled: bool = False,
        api_only: bool = False,
    ) -> dict[str, Any]:
        """Create a new user in Fleet.

        Creates a new user with specified role and team assignments.

        Global roles: admin, maintainer, observer, observer_plus, gitops
        Team roles: admin, maintainer, observer, observer_plus, gitops

        Args:
            name: Full name of the user
            email: Email address (used for login)
            password: Password for the user (required if not SSO)
            global_role: Optional global role assignment
            teams: Optional list of team assignments with roles
            sso_enabled: Whether SSO is enabled for this user
            api_only: Whether this is an API-only user (no UI access)

        Returns:
            Dict containing the created user and optional API token.
        """
        try:
            async with client:
                payload: dict[str, Any] = {
                    "name": name,
                    "email": email,
                    "sso_enabled": sso_enabled,
                    "api_only": api_only,
                }
                if password is not None:
                    payload["password"] = password
                if global_role is not None:
                    payload["global_role"] = global_role
                if teams is not None:
                    payload["teams"] = teams

                response = await client.post(
                    "/api/latest/fleet/users/admin", json_data=payload
                )
                data = response.data or {}
                user = data.get("user", {})
                user_id = user.get("id", "unknown")
                return {
                    "success": True,
                    "message": f"Created user {name} (ID: {user_id})",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to create user {email}: {e}")
            return {
                "success": False,
                "message": f"Failed to create user: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_update_user(
        user_id: int,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        global_role: str | None = None,
        teams: list[dict[str, Any]] | None = None,
        sso_enabled: bool | None = None,
        api_only: bool | None = None,
    ) -> dict[str, Any]:
        """Update user information and roles.

        Updates an existing user's information, role assignments, or settings.

        Args:
            user_id: ID of the user to update
            name: New name for the user
            email: New email address
            password: New password
            global_role: New global role assignment
            teams: New team assignments with roles
            sso_enabled: Whether SSO is enabled
            api_only: Whether this is an API-only user

        Returns:
            Dict containing the updated user information.
        """
        try:
            async with client:
                payload: dict[str, Any] = {}
                if name is not None:
                    payload["name"] = name
                if email is not None:
                    payload["email"] = email
                if password is not None:
                    payload["password"] = password
                if global_role is not None:
                    payload["global_role"] = global_role
                if teams is not None:
                    payload["teams"] = teams
                if sso_enabled is not None:
                    payload["sso_enabled"] = sso_enabled
                if api_only is not None:
                    payload["api_only"] = api_only

                response = await client.patch(
                    f"/api/latest/fleet/users/{user_id}", json_data=payload
                )
                return {
                    "success": True,
                    "message": f"Updated user {user_id}",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to update user: {str(e)}",
                "data": None,
            }

    # TODO: Disabled for now as it is too dangerous. Revisit later if really needed.
    # @mcp.tool()
    # async def fleet_delete_user(user_id: int) -> dict[str, Any]:
    #     """Delete a user from Fleet.

    #     Permanently removes a user from the system.

    #     Args:
    #         user_id: ID of the user to delete

    #     Returns:
    #         Dict containing the result of the deletion.
    #     """
    #     try:
    #         async with client:
    #             await client.delete(f"/api/latest/fleet/users/{user_id}")
    #             return {
    #                 "success": True,
    #                 "message": f"Deleted user {user_id}",
    #                 "data": None,
    #             }
    #     except FleetAPIError as e:
    #         logger.error(f"Failed to delete user {user_id}: {e}")
    #         return {
    #             "success": False,
    #             "message": f"Failed to delete user: {str(e)}",
    #             "data": None,
    #         }

    @mcp.tool()
    async def fleet_delete_session(session_id: int) -> dict[str, Any]:
        """Delete/invalidate a specific session.

        Logs out a user by invalidating their session.

        Args:
            session_id: ID of the session to delete

        Returns:
            Dict containing the result of the deletion.
        """
        try:
            async with client:
                await client.delete(f"/api/latest/fleet/sessions/{session_id}")
                return {
                    "success": True,
                    "message": f"Deleted session {session_id}",
                    "data": None,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete session: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_delete_user_sessions(user_id: int) -> dict[str, Any]:
        """Delete all sessions for a specific user.

        Logs out a user from all devices by invalidating all their sessions.

        Args:
            user_id: ID of the user

        Returns:
            Dict containing the result of the deletion.
        """
        try:
            async with client:
                await client.delete(f"/api/latest/fleet/users/{user_id}/sessions")
                return {
                    "success": True,
                    "message": f"Deleted all sessions for user {user_id}",
                    "data": None,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to delete sessions for user {user_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete user sessions: {str(e)}",
                "data": None,
            }

    # TODO: Disabled for now as it is too dangerous. Revisit later if really needed.
    # @mcp.tool()
    # async def fleet_require_password_reset(
    #     user_id: int, require: bool = True
    # ) -> dict[str, Any]:
    #     """Require a user to reset their password on next login.

    #     This forces a user to change their password the next time they log in.

    #     Args:
    #         user_id: ID of the user
    #         require: Whether to require password reset (default: True)

    #     Returns:
    #         Dict indicating success or failure of the operation.

    #     Example:
    #         >>> result = await fleet_require_password_reset(user_id=10)
    #         >>> print(result["message"])
    #     """
    #     try:
    #         async with client:
    #             json_data = {"require": require}
    #             response = await client.post(
    #                 f"/users/{user_id}/require_password_reset", json_data=json_data
    #             )

    #             return {
    #                 "success": response.success,
    #                 "message": response.message
    #                 or f"Password reset {'required' if require else 'not required'} for user {user_id}",
    #                 "user_id": user_id,
    #                 "require": require,
    #             }

    #     except FleetAPIError as e:
    #         logger.error(f"Failed to require password reset for user {user_id}: {e}")
    #         return {
    #             "success": False,
    #             "message": f"Failed to require password reset: {str(e)}",
    #             "user_id": user_id,
    #             "require": require,
    #         }
