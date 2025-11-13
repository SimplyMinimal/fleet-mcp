"""Team and user management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetClient
from .common import (
    build_pagination_params,
    format_error_response,
    format_list_response,
    format_success_response,
    handle_fleet_api_errors,
)

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all team and user management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only team and user management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("list teams", {"teams": [], "count": 0})
    async def fleet_list_teams(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "name",
        order_direction: str = "asc",
        query: str = "",
    ) -> dict[str, Any]:
        """List all teams in Fleet with pagination and sorting.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of teams per page
            order_key: Field to order by (name, created_at)
            order_direction: Sort direction (asc, desc)
            query: Search query to filter teams by name

        Returns:
            Dict containing list of teams and pagination metadata.
        """
        async with client:
            params = build_pagination_params(
                page=page,
                per_page=min(per_page, 500),
                order_key=order_key,
                order_direction=order_direction,
                query=query if query else None,
            )

            response = await client.get("/teams", params=params)

            if response.success and response.data:
                teams = response.data.get("teams", [])

                return format_list_response(
                    items=teams,
                    item_name="teams",
                    page=page,
                    per_page=per_page,
                )
            else:

                return format_error_response(
                    response.message,
                    teams=[],
                    count=0,
                )

    @mcp.tool()
    @handle_fleet_api_errors("get team", {"team": None, "team_id": None})
    async def fleet_get_team(team_id: int) -> dict[str, Any]:
        """Get details of a specific team.

        Args:
            team_id: ID of the team to retrieve

        Returns:
            Dict containing team details.
        """
        async with client:
            response = await client.get(f"/teams/{team_id}")

            if response.success and response.data:
                team = response.data.get("team", {})

                return format_success_response(
                    f"Retrieved team '{team.get('name', team_id)}'",
                    team=team,
                    team_id=team_id,
                )
            else:

                return format_error_response(
                    response.message,
                    team=None,
                    team_id=team_id,
                )

    @mcp.tool()
    @handle_fleet_api_errors(
        "list team users", {"team_id": None, "users": [], "count": 0}
    )
    async def fleet_list_team_users(team_id: int) -> dict[str, Any]:
        """List all users that are members of a specific team.

        Args:
            team_id: ID of the team

        Returns:
            Dict containing list of users in the team.

        Example:
            >>> result = await fleet_list_team_users(team_id=1)
            >>> print(result["users"])
        """
        async with client:
            response = await client.get(f"/teams/{team_id}/users")

            if response.success and response.data:
                users = response.data.get("users", [])

                return format_success_response(
                    f"Found {len(users)} users in team {team_id}",
                    team_id=team_id,
                    users=users,
                    count=len(users),
                )
            else:

                return format_error_response(
                    response.message,
                    team_id=team_id,
                    users=[],
                    count=0,
                )

    @mcp.tool()
    @handle_fleet_api_errors(
        "get team secrets", {"team_id": None, "secrets": [], "count": 0}
    )
    async def fleet_get_team_secrets(team_id: int) -> dict[str, Any]:
        """List team-specific enroll secrets.

        Args:
            team_id: ID of the team

        Returns:
            Dict containing team enroll secrets.

        Example:
            >>> result = await fleet_get_team_secrets(team_id=1)
            >>> print(result["secrets"])
        """
        async with client:
            response = await client.get(f"/teams/{team_id}/secrets")

            if response.success and response.data:
                secrets = response.data.get("secrets", [])

                return format_success_response(
                    f"Found {len(secrets)} secrets for team {team_id}",
                    team_id=team_id,
                    secrets=secrets,
                    count=len(secrets),
                )
            else:

                return format_error_response(
                    response.message,
                    team_id=team_id,
                    secrets=[],
                    count=0,
                )


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write team and user management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("create team", {"team": None})
    async def fleet_create_team(
        name: str, description: str | None = None
    ) -> dict[str, Any]:
        """Create a new team in Fleet.

        Args:
            name: Name for the team
            description: Optional description of the team

        Returns:
            Dict containing the created team information.
        """
        async with client:
            json_data = {"name": name}

            if description:
                json_data["description"] = description

            response = await client.post("/teams", json_data=json_data)

            if response.success and response.data:
                team = response.data.get("team", {})

                return format_success_response(
                    f"Created team '{name}' with ID {team.get('id')}",
                    team=team,
                )
            else:

                return format_error_response(response.message, team=None)

    @mcp.tool()
    @handle_fleet_api_errors(
        "add team users", {"team_id": None, "user_ids": [], "users_added": 0}
    )
    async def fleet_add_team_users(team_id: int, user_ids: list[int]) -> dict[str, Any]:
        """Add one or more users to a specific team.

        Args:
            team_id: ID of the team
            user_ids: List of user IDs to add to the team

        Returns:
            Dict indicating success or failure of the operation.

        Example:
            >>> result = await fleet_add_team_users(team_id=1, user_ids=[10, 20])
            >>> print(result["message"])
        """
        async with client:
            json_data = {"users": [{"id": uid} for uid in user_ids]}
            response = await client.patch(
                f"/teams/{team_id}/users", json_data=json_data
            )

            return format_success_response(
                response.message or f"Added {len(user_ids)} users to team {team_id}",
                team_id=team_id,
                user_ids=user_ids,
                users_added=len(user_ids) if response.success else 0,
            )

    @mcp.tool()
    @handle_fleet_api_errors("remove team user", {"team_id": None, "user_id": None})
    async def fleet_remove_team_user(team_id: int, user_id: int) -> dict[str, Any]:
        """Remove a specific user from a team.

        Args:
            team_id: ID of the team
            user_id: ID of the user to remove

        Returns:
            Dict indicating success or failure of the operation.

        Example:
            >>> result = await fleet_remove_team_user(team_id=1, user_id=10)
            >>> print(result["message"])
        """
        async with client:
            json_data = {"users": [{"id": user_id}]}
            response = await client.delete(
                f"/teams/{team_id}/users", json_data=json_data
            )

            return format_success_response(
                response.message or f"Removed user {user_id} from team {team_id}",
                team_id=team_id,
                user_id=user_id,
            )
