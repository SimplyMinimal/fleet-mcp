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

# Common English stop words to filter out from keyword searches
# These words are too common and create too many false matches
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "will",
    "with",
}


def _calculate_keyword_relevance(
    policy_name: str, keywords: list[str]
) -> tuple[int, int]:
    """Calculate relevance score for a policy based on keyword matching.

    Args:
        policy_name: The name of the policy to score
        keywords: List of keywords to match against

    Returns:
        Tuple of (matched_keywords_count, earliest_match_position)
        Higher matched_keywords_count is better, lower earliest_match_position is better
    """
    policy_name_lower = policy_name.lower()
    matched_count = 0
    earliest_position = len(policy_name)

    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in policy_name_lower:
            matched_count += 1
            position = policy_name_lower.index(keyword_lower)
            earliest_position = min(earliest_position, position)

    return (matched_count, -earliest_position)  # Negative position for sorting


def _filter_and_rank_policies(
    policies: list[dict[str, Any]], query: str
) -> list[dict[str, Any]]:
    """Filter and rank policies based on keyword matching.

    Splits the query into keywords and ranks policies by:
    1. Number of matching keywords (more is better)
    2. Position of first match (earlier is better)

    Stop words (common words like 'in', 'to', 'the') are filtered out to reduce
    false matches.

    Args:
        policies: List of policy dictionaries
        query: Search query string with keywords

    Returns:
        Filtered and sorted list of policies
    """
    if not query or not query.strip():
        return policies

    # Split query into keywords and filter out stop words
    keywords = [
        k.strip()
        for k in query.split()
        if k.strip() and k.strip().lower() not in STOP_WORDS
    ]

    if not keywords:
        return policies

    # Score each policy
    scored_policies: list[dict[str, Any]] = []
    for policy in policies:
        policy_name = policy.get("name", "")
        matched_count, position_score = _calculate_keyword_relevance(
            policy_name, keywords
        )

        # Only include policies that match at least one keyword
        if matched_count > 0:
            scored_policies.append(
                {
                    "policy": policy,
                    "score": (matched_count, position_score),
                }
            )

    # Sort by score (descending matched_count, then descending position_score)
    scored_policies.sort(key=lambda x: x["score"], reverse=True)

    # Return just the policies
    return [item["policy"] for item in scored_policies]


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
        query: str = "",
        search_all_teams: bool = False,
    ) -> dict[str, Any]:
        """List policies with optional filtering by team and name.

        Search modes (automatic based on query):
        - Single word: Fast substring search (e.g., "firewall" finds "Firewall Enabled")
        - Multiple words: Keyword search with ranking (e.g., "Logged System" matches policies
          containing "Logged" OR "System", ranked by relevance)

        Tips for efficient use:
        - Use single-word queries for fastest results
        - Use team_id to narrow scope and see both team-specific and inherited policies
        - Use search_all_teams=True to search across all teams when you don't know which team
        - Multi-word queries automatically filter stop words ("in", "to", "the", etc.)

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of policies per page (max 500)
            order_key: Field to order by (name, critical, created_at, updated_at)
            order_direction: Sort direction (asc, desc)
            team_id: Filter by team ID (returns team-specific + inherited policies)
            query: Search by policy name (empty = all policies)
            search_all_teams: Search across all teams (mutually exclusive with team_id)

        Returns:
            Dict containing list of policies and pagination metadata.
        """
        async with client:
            # Validate mutually exclusive parameters
            if team_id is not None and search_all_teams:
                return format_error_response(
                    "Parameters 'team_id' and 'search_all_teams' cannot be used together. "
                    "Use 'team_id' to search a specific team, or 'search_all_teams=True' to search all teams.",
                    policies=[],
                    count=0,
                )

            # Handle search_all_teams mode
            if search_all_teams:
                # Fetch all teams first
                teams_response = await client.get("/teams", params={"per_page": 500})

                if not teams_response.success or not teams_response.data:
                    return format_error_response(
                        f"Failed to fetch teams: {teams_response.message}",
                        policies=[],
                        count=0,
                    )

                teams = teams_response.data.get("teams", [])
                all_policies = []
                seen_policy_ids = set()  # Track unique policies to avoid duplicates

                # Fetch policies from each team
                for team in teams:
                    team_id_current = team.get("id")
                    if team_id_current is None:
                        continue

                    team_response = await client.get(
                        f"/teams/{team_id_current}/policies", params={"per_page": 500}
                    )

                    if team_response.success and team_response.data:
                        # Get both team-specific and inherited policies
                        team_policies = team_response.data.get("policies", [])
                        inherited_policies = team_response.data.get(
                            "inherited_policies", []
                        )

                        # Add team-specific policies (avoid duplicates)
                        for policy in team_policies:
                            policy_id = policy.get("id")
                            if policy_id and policy_id not in seen_policy_ids:
                                seen_policy_ids.add(policy_id)
                                all_policies.append(policy)

                        # Add inherited policies (avoid duplicates)
                        for policy in inherited_policies:
                            policy_id = policy.get("id")
                            if policy_id and policy_id not in seen_policy_ids:
                                seen_policy_ids.add(policy_id)
                                all_policies.append(policy)

                # Apply query filtering if provided
                if query:
                    keywords = [k.strip() for k in query.split() if k.strip()]
                    if len(keywords) > 1:
                        # Multi-word: use keyword-based ranking
                        filtered_policies = _filter_and_rank_policies(
                            all_policies, query
                        )
                    else:
                        # Single-word: simple case-insensitive substring match
                        query_lower = query.lower()
                        filtered_policies = [
                            p
                            for p in all_policies
                            if query_lower in p.get("name", "").lower()
                        ]
                else:
                    filtered_policies = all_policies

                # Sort the results
                reverse = order_direction.lower() == "desc"
                if order_key in ["name", "critical", "created_at", "updated_at"]:
                    filtered_policies.sort(
                        key=lambda p: p.get(order_key, ""), reverse=reverse
                    )

                # Apply pagination
                start_idx = page * per_page
                end_idx = start_idx + per_page
                paginated_policies = filtered_policies[start_idx:end_idx]

                return format_list_response(
                    paginated_policies,
                    "policies",
                    page,
                    per_page,
                    total_count=len(filtered_policies),
                )

            # Determine if we should use client-side filtering
            keywords = [k.strip() for k in query.split() if k.strip()] if query else []
            use_keyword_search = len(keywords) > 1

            # Use client-side filtering when:
            # 1. Multi-word query (keyword search with ranking)
            # 2. Single-word query + team_id (to ensure we search all team policies)
            use_client_side_filtering = use_keyword_search or (
                query and team_id is not None
            )

            if use_client_side_filtering:
                # For client-side filtering, fetch all policies and filter/rank locally
                # This ensures we don't miss results due to API pagination limits
                params = build_pagination_params(
                    page=0,  # Fetch from beginning
                    per_page=500,  # Fetch maximum allowed
                    order_key=order_key,
                    order_direction=order_direction,
                    team_id=None,  # Don't pass team_id in params when using team endpoint
                    query=None,  # Don't filter on API side for client-side filtering
                )

                # Use correct endpoint based on whether team_id is specified
                if team_id is not None:
                    # Use team-specific endpoint which returns both team and inherited policies
                    endpoint = f"/teams/{team_id}/policies"
                else:
                    # Use global endpoint
                    endpoint = "/policies"

                response = await client.get(endpoint, params=params)

                if response.success:
                    # Fleet API returns success=True even when no data/empty results
                    if team_id is not None and response.data:
                        # Team endpoint returns both 'policies' and 'inherited_policies'
                        team_policies = response.data.get("policies", [])
                        inherited_policies = response.data.get("inherited_policies", [])
                        all_policies = team_policies + inherited_policies
                    else:
                        all_policies = (
                            response.data.get("policies", []) if response.data else []
                        )

                    # Apply filtering and ranking
                    if use_keyword_search:
                        # Multi-word: use keyword-based ranking
                        filtered_policies = _filter_and_rank_policies(
                            all_policies, query
                        )
                    else:
                        # Single-word with team_id: simple case-insensitive substring match
                        query_lower = query.lower()
                        filtered_policies = [
                            p
                            for p in all_policies
                            if query_lower in p.get("name", "").lower()
                        ]

                    # Apply pagination to filtered results
                    start_idx = page * per_page
                    end_idx = start_idx + per_page
                    paginated_policies = filtered_policies[start_idx:end_idx]

                    return format_list_response(
                        paginated_policies,
                        "policies",
                        page,
                        per_page,
                        total_count=len(filtered_policies),
                    )
                else:
                    return format_error_response(response.message, policies=[], count=0)
            else:
                # For queries without client-side filtering, use Fleet API directly
                params = build_pagination_params(
                    page=page,
                    per_page=min(per_page, 500),
                    order_key=order_key,
                    order_direction=order_direction,
                    team_id=None,  # Don't pass team_id in params when using team endpoint
                    query=query if query else None,
                )

                # Use correct endpoint based on whether team_id is specified
                if team_id is not None:
                    # Use team-specific endpoint which returns both team and inherited policies
                    endpoint = f"/teams/{team_id}/policies"
                else:
                    # Use global endpoint
                    endpoint = "/policies"

                response = await client.get(endpoint, params=params)

                if response.success:
                    # Fleet API returns success=True even when no data/empty results
                    if team_id is not None and response.data:
                        # Team endpoint returns both 'policies' and 'inherited_policies'
                        team_policies = response.data.get("policies", [])
                        inherited_policies = response.data.get("inherited_policies", [])
                        policies = team_policies + inherited_policies
                    else:
                        policies = (
                            response.data.get("policies", []) if response.data else []
                        )
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
            team_id: Team ID to associate the policy with (if None, creates a global policy)
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

            # Use team-specific endpoint if team_id is provided
            if team_id is not None:
                endpoint = f"/api/latest/fleet/teams/{team_id}/policies"
            else:
                endpoint = "/policies"

            response = await client.post(endpoint, json_data=json_data)

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
