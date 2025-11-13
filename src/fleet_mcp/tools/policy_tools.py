"""Policy management tools for Fleet MCP."""

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
    """Register all policy management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only policy management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("list policies", {"policies": [], "count": 0})
    async def fleet_list_policies(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "name",
        order_direction: str = "asc",
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """List all policies in Fleet with pagination and sorting.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of policies per page
            order_key: Field to order by (name, critical, created_at, updated_at)
            order_direction: Sort direction (asc, desc)
            team_id: Filter policies by team ID

        Returns:
            Dict containing list of policies and pagination metadata.
        """
        async with client:
            params = build_pagination_params(
                page=page,
                per_page=min(per_page, 500),
                order_key=order_key,
                order_direction=order_direction,
                team_id=team_id,
            )

            response = await client.get("/policies", params=params)

            if response.success and response.data:
                policies = response.data.get("policies", [])
                return format_list_response(policies, "policies", page, per_page)
            else:
                return format_error_response(response.message, policies=[], count=0)

    @mcp.tool()
    @handle_fleet_api_errors("get policy results", {"policy": None, "policy_id": None})
    async def fleet_get_policy_results(
        policy_id: int, team_id: int | None = None
    ) -> dict[str, Any]:
        """Get compliance results for a specific policy.

        Args:
            policy_id: ID of the policy to get results for
            team_id: Filter results by team ID

        Returns:
            Dict containing policy compliance results.
        """
        async with client:
            params = {}
            if team_id is not None:
                params["team_id"] = team_id

            response = await client.get(f"/policies/{policy_id}", params=params)

            if response.success and response.data:
                policy = response.data.get("policy", {})
                return {
                    "success": True,
                    "policy": policy,
                    "policy_id": policy_id,
                    "passing_host_count": policy.get("passing_host_count", 0),
                    "failing_host_count": policy.get("failing_host_count", 0),
                    "message": f"Policy '{policy.get('name')}' results retrieved",
                }
            else:
                return format_error_response(
                    response.message,
                    policy=None,
                    policy_id=policy_id,
                )


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write policy management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    @handle_fleet_api_errors("create policy", {"policy": None})
    async def fleet_create_policy(
        name: str,
        query: str,
        description: str | None = None,
        resolution: str | None = None,
        team_id: int | None = None,
        critical: bool = False,
    ) -> dict[str, Any]:
        """Create a new compliance policy in Fleet.

        Args:
            name: Name for the policy
            query: SQL query that defines the policy check
            description: Optional description of the policy
            resolution: Optional resolution steps for policy failures
            team_id: Team ID to associate the policy with
            critical: Whether this is a critical policy

        Returns:
            Dict containing the created policy information.
        """
        async with client:
            json_data = {"name": name, "query": query, "critical": critical}

            if description:
                json_data["description"] = description
            if resolution:
                json_data["resolution"] = resolution
            if team_id is not None:
                json_data["team_id"] = team_id

            response = await client.post("/policies", json_data=json_data)

            if response.success and response.data:
                policy = response.data.get("policy", {})
                return format_success_response(
                    f"Created policy '{name}' with ID {policy.get('id')}",
                    policy=policy,
                )
            else:
                return format_error_response(response.message, policy=None)

    @mcp.tool()
    @handle_fleet_api_errors("update policy", {"policy": None, "policy_id": None})
    async def fleet_update_policy(
        policy_id: int,
        name: str | None = None,
        query: str | None = None,
        description: str | None = None,
        resolution: str | None = None,
        critical: bool | None = None,
    ) -> dict[str, Any]:
        """Update an existing policy in Fleet.

        Args:
            policy_id: ID of the policy to update
            name: New name for the policy
            query: New SQL query for the policy
            description: New description for the policy
            resolution: New resolution steps for the policy
            critical: Whether this is a critical policy

        Returns:
            Dict containing the updated policy information.
        """
        async with client:
            json_data: dict[str, Any] = {}

            if name is not None:
                json_data["name"] = name
            if query is not None:
                json_data["query"] = query
            if description is not None:
                json_data["description"] = description
            if resolution is not None:
                json_data["resolution"] = resolution
            if critical is not None:
                json_data["critical"] = critical

            if not json_data:
                return format_error_response(
                    "No fields provided to update",
                    policy=None,
                    policy_id=policy_id,
                )

            response = await client.patch(f"/policies/{policy_id}", json_data=json_data)

            if response.success and response.data:
                policy = response.data.get("policy", {})
                return format_success_response(
                    f"Updated policy '{policy.get('name')}'",
                    policy=policy,
                    policy_id=policy_id,
                )
            else:
                return format_error_response(
                    response.message,
                    policy=None,
                    policy_id=policy_id,
                )

    @mcp.tool()
    @handle_fleet_api_errors("delete policy", {"policy_id": None})
    async def fleet_delete_policy(policy_id: int) -> dict[str, Any]:
        """Delete a policy from Fleet.

        Args:
            policy_id: ID of the policy to delete

        Returns:
            Dict indicating success or failure of the deletion.
        """
        async with client:
            # Fleet API uses POST to /policies/delete with JSON body containing policy IDs
            json_data = {"ids": [policy_id]}
            response = await client.post("/policies/delete", json_data=json_data)

            return {
                "success": response.success,
                "message": response.message
                or f"Policy {policy_id} deleted successfully",
                "policy_id": policy_id,
            }
