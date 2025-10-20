"""Query management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all query management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only query management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_queries(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "name",
        order_direction: str = "asc",
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """List all saved queries in Fleet.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of queries per page
            order_key: Field to order by (name, updated_at, created_at)
            order_direction: Sort direction (asc, desc)
            team_id: Filter queries by team ID

        Returns:
            Dict containing list of queries and pagination metadata.
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

                response = await client.get("/queries", params=params)

                if response.success and response.data:
                    queries = response.data.get("queries", [])
                    return {
                        "success": True,
                        "queries": queries,
                        "count": len(queries),
                        "page": page,
                        "per_page": per_page,
                        "message": f"Found {len(queries)} queries",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "queries": [],
                        "count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list queries: {e}")
            return {
                "success": False,
                "message": f"Failed to list queries: {str(e)}",
                "queries": [],
                "count": 0,
            }

    @mcp.tool()
    async def fleet_get_query_report(
        query_id: int, team_id: int | None = None
    ) -> dict[str, Any]:
        """Get the latest stored results from a SCHEDULED query.

        IMPORTANT: This tool ONLY works for scheduled queries (queries with an
        'interval' set that run periodically). It retrieves the stored results
        from the last time the scheduled query ran.

        This tool does NOT work for:
        - Live query campaigns created by fleet_run_live_query()
        - Ad-hoc queries that haven't been saved and scheduled
        - Queries that don't have 'interval' configured

        For running ad-hoc queries and getting results, use:
        - fleet_query_host(host_id, query) - Run query on ONE host and get results
        - fleet_query_host_by_identifier(identifier, query) - Run query by hostname/UUID

        Args:
            query_id: ID of the saved SCHEDULED query
            team_id: Optional team ID to filter results to hosts in that team

        Returns:
            Dict containing stored query results from all hosts that ran the query.
        """
        try:
            async with client:
                params = {}
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get(
                    f"/queries/{query_id}/report", params=params
                )

                if response.success and response.data:
                    results = response.data.get("results", [])
                    report_clipped = response.data.get("report_clipped", False)
                    return {
                        "success": True,
                        "query_id": query_id,
                        "results": results,
                        "result_count": len(results),
                        "report_clipped": report_clipped,
                        "message": f"Retrieved {len(results)} query results"
                        + (" (report clipped)" if report_clipped else ""),
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "results": [],
                        "query_id": query_id,
                        "result_count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get query report: {e}")
            return {
                "success": False,
                "message": f"Failed to get query report: {str(e)}",
                "results": [],
                "query_id": query_id,
                "result_count": 0,
            }

    @mcp.tool()
    async def fleet_get_query(query_id: int) -> dict[str, Any]:
        """Get details of a specific saved query.

        Args:
            query_id: ID of the query to retrieve

        Returns:
            Dict containing query details.
        """
        try:
            async with client:
                response = await client.get(f"/queries/{query_id}")

                if response.success and response.data:
                    query_data = response.data.get("query", {})
                    return {
                        "success": True,
                        "query": query_data,
                        "query_id": query_id,
                        "message": f"Retrieved query '{query_data.get('name', query_id)}'",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "query": None,
                        "query_id": query_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get query {query_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get query: {str(e)}",
                "query": None,
                "query_id": query_id,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write query management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_create_query(
        name: str,
        query: str,
        description: str | None = None,
        team_id: int | None = None,
        observer_can_run: bool = False,
    ) -> dict[str, Any]:
        """Create a new saved query in Fleet.

        Args:
            name: Name for the query
            query: SQL query string (osquery syntax)
            description: Optional description of the query
            team_id: Team ID to associate the query with
            observer_can_run: Whether observers can run this query

        Returns:
            Dict containing the created query information.
        """
        try:
            async with client:
                json_data = {
                    "name": name,
                    "query": query,
                    "observer_can_run": observer_can_run,
                }

                if description:
                    json_data["description"] = description

                if team_id is not None:
                    json_data["team_id"] = team_id

                response = await client.post("/queries", json_data=json_data)

                if response.success and response.data:
                    query_data = response.data.get("query", {})
                    return {
                        "success": True,
                        "query": query_data,
                        "message": f"Created query '{name}' with ID {query_data.get('id')}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "query": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to create query: {e}")
            return {
                "success": False,
                "message": f"Failed to create query: {str(e)}",
                "query": None,
            }

    @mcp.tool()
    async def fleet_run_live_query(
        query: str,
        host_ids: list[int] | None = None,
        label_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Execute a live query campaign against specified hosts.

        IMPORTANT: This tool creates an asynchronous query campaign but does NOT
        wait for or return query results. The campaign runs in the background and
        results are streamed via WebSocket (not accessible through this tool).

        For getting query results, use one of these alternatives instead:
        - fleet_query_host(host_id, query) - Run query on ONE host and get results
        - fleet_query_host_by_identifier(identifier, query) - Run query by hostname/UUID
        - Create a scheduled query with fleet_create_query() and use
          fleet_get_query_report() to retrieve stored results later

        This tool is primarily useful for:
        - Triggering background query campaigns across many hosts
        - Getting campaign metadata (campaign_id, targeted hosts count)
        - Monitoring campaign status (online/offline hosts)

        Args:
            query: SQL query string to execute
            host_ids: List of specific host IDs to target
            label_ids: List of label IDs to target hosts
            team_ids: List of team IDs to target hosts

        Returns:
            Dict containing campaign information and initial status (NO RESULTS).
        """
        try:
            async with client:
                json_data: dict[str, Any] = {"query": query}

                # Add targeting parameters if provided
                if host_ids:
                    json_data["selected"] = {"hosts": host_ids}
                elif label_ids:
                    json_data["selected"] = {"labels": label_ids}
                elif team_ids:
                    json_data["selected"] = {"teams": team_ids}

                response = await client.post("/queries/run", json_data=json_data)

                if response.success and response.data:
                    campaign = response.data.get("campaign", {})
                    campaign_id = campaign.get("id")
                    metrics = campaign.get("Metrics", {})

                    return {
                        "success": True,
                        "campaign": campaign,
                        "campaign_id": campaign_id,
                        "query": query,
                        "message": (
                            f"Started live query campaign {campaign_id}. "
                            f"Targeted {metrics.get('TotalHosts', 0)} hosts "
                            f"({metrics.get('OnlineHosts', 0)} online, "
                            f"{metrics.get('OfflineHosts', 0)} offline). "
                            "NOTE: This tool does NOT return query results. "
                            "Use fleet_query_host() or fleet_query_host_by_identifier() "
                            "to run queries and get results."
                        ),
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "campaign": None,
                        "query": query,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to run live query: {e}")
            return {
                "success": False,
                "message": f"Failed to run live query: {str(e)}",
                "campaign": None,
                "query": query,
            }

    @mcp.tool()
    async def fleet_delete_query(query_id: int) -> dict[str, Any]:
        """Delete a saved query from Fleet.

        Args:
            query_id: ID of the query to delete

        Returns:
            Dict indicating success or failure of the deletion.
        """
        try:
            async with client:
                # Fleet API uses /queries/id/{id} for deletion
                response = await client.delete(f"/queries/id/{query_id}")

                return {
                    "success": response.success,
                    "message": response.message
                    or f"Query {query_id} deleted successfully",
                    "query_id": query_id,
                }

        except FleetAPIError as e:
            logger.error(f"Failed to delete query {query_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete query: {str(e)}",
                "query_id": query_id,
            }

    @mcp.tool()
    async def fleet_run_saved_query(
        query_id: int,
        host_ids: list[int] | None = None,
        label_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Run a saved query against specified hosts.

        Args:
            query_id: ID of the saved query to run
            host_ids: List of specific host IDs to target
            label_ids: List of label IDs to target hosts
            team_ids: List of team IDs to target hosts

        Returns:
            Dict containing query execution results and campaign information.
        """
        try:
            async with client:
                # Fleet API uses /queries/run with query_id in the body
                json_data = {
                    "query_id": query_id,
                    "selected": {
                        "hosts": host_ids or [],
                        "labels": label_ids or [],
                        "teams": team_ids or [],
                    },
                }

                response = await client.post("/queries/run", json_data=json_data)

                if response.success and response.data:
                    campaign = response.data.get("campaign", {})
                    return {
                        "success": True,
                        "campaign": campaign,
                        "campaign_id": campaign.get("id"),
                        "query_id": query_id,
                        "message": f"Started saved query campaign {campaign.get('id')}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "campaign": None,
                        "query_id": query_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to run saved query {query_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to run saved query: {str(e)}",
                "campaign": None,
                "query_id": query_id,
            }
