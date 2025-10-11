"""Team and user management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

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
    async def fleet_list_teams() -> dict[str, Any]:
        """List all teams in Fleet.
        
        Returns:
            Dict containing list of teams.
        """
        try:
            async with client:
                response = await client.get("/teams")

                if response.success and response.data:
                    teams = response.data.get("teams", [])
                    return {
                        "success": True,
                        "teams": teams,
                        "count": len(teams),
                        "message": f"Found {len(teams)} teams"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "teams": [],
                        "count": 0
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list teams: {e}")
            return {
                "success": False,
                "message": f"Failed to list teams: {str(e)}",
                "teams": [],
                "count": 0
            }

    @mcp.tool()
    async def fleet_get_team(team_id: int) -> dict[str, Any]:
        """Get details of a specific team.
        
        Args:
            team_id: ID of the team to retrieve
            
        Returns:
            Dict containing team details.
        """
        try:
            async with client:
                response = await client.get(f"/teams/{team_id}")

                if response.success and response.data:
                    team = response.data.get("team", {})
                    return {
                        "success": True,
                        "team": team,
                        "team_id": team_id,
                        "message": f"Retrieved team '{team.get('name', team_id)}'"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "team": None,
                        "team_id": team_id
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get team {team_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get team: {str(e)}",
                "team": None,
                "team_id": team_id
            }

    @mcp.tool()
    async def fleet_list_users(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "name",
        order_direction: str = "asc",
        query: str = "",
        team_id: int | None = None
    ) -> dict[str, Any]:
        """List all users in Fleet.
        
        Args:
            page: Page number for pagination (0-based)
            per_page: Number of users per page
            order_key: Field to order by (name, email, created_at)
            order_direction: Sort direction (asc, desc)
            query: Search query to filter users by name or email
            team_id: Filter users by team ID
            
        Returns:
            Dict containing list of users and pagination metadata.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                    "order_key": order_key,
                    "order_direction": order_direction
                }

                if query:
                    params["query"] = query
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get("/users", params=params)

                if response.success and response.data:
                    users = response.data.get("users", [])
                    return {
                        "success": True,
                        "users": users,
                        "count": len(users),
                        "page": page,
                        "per_page": per_page,
                        "message": f"Found {len(users)} users"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "users": [],
                        "count": 0
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list users: {e}")
            return {
                "success": False,
                "message": f"Failed to list users: {str(e)}",
                "users": [],
                "count": 0
            }

    @mcp.tool()
    async def fleet_get_user(user_id: int) -> dict[str, Any]:
        """Get details of a specific user.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            Dict containing user details.
        """
        try:
            async with client:
                response = await client.get(f"/users/{user_id}")

                if response.success and response.data:
                    user = response.data.get("user", {})
                    return {
                        "success": True,
                        "user": user,
                        "user_id": user_id,
                        "message": f"Retrieved user '{user.get('name', user_id)}'"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "user": None,
                        "user_id": user_id
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get user: {str(e)}",
                "user": None,
                "user_id": user_id
            }

    @mcp.tool()
    async def fleet_list_activities(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "created_at",
        order_direction: str = "desc"
    ) -> dict[str, Any]:
        """List Fleet activities and audit logs.
        
        Args:
            page: Page number for pagination (0-based)
            per_page: Number of activities per page
            order_key: Field to order by (created_at, type)
            order_direction: Sort direction (asc, desc)
            
        Returns:
            Dict containing list of activities and pagination metadata.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                    "order_key": order_key,
                    "order_direction": order_direction
                }

                response = await client.get("/activities", params=params)

                if response.success and response.data:
                    activities = response.data.get("activities", [])
                    return {
                        "success": True,
                        "activities": activities,
                        "count": len(activities),
                        "page": page,
                        "per_page": per_page,
                        "message": f"Found {len(activities)} activities"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "activities": [],
                        "count": 0
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list activities: {e}")
            return {
                "success": False,
                "message": f"Failed to list activities: {str(e)}",
                "activities": [],
                "count": 0
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write team and user management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_create_team(
        name: str,
        description: str | None = None
    ) -> dict[str, Any]:
        """Create a new team in Fleet.

        Args:
            name: Name for the team
            description: Optional description of the team

        Returns:
            Dict containing the created team information.
        """
        try:
            async with client:
                json_data = {"name": name}

                if description:
                    json_data["description"] = description

                response = await client.post("/teams", json_data=json_data)

                if response.success and response.data:
                    team = response.data.get("team", {})
                    return {
                        "success": True,
                        "team": team,
                        "message": f"Created team '{name}' with ID {team.get('id')}"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "team": None
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to create team: {e}")
            return {
                "success": False,
                "message": f"Failed to create team: {str(e)}",
                "team": None
            }
