"""Read-only query tools with SELECT validation for Fleet MCP.

This module provides query execution tools that validate queries are SELECT-only
before execution, allowing safe query execution in read-only mode.
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient
from ..utils.sql_validator import validate_select_query

logger = logging.getLogger(__name__)


def register_select_only_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register SELECT-only query tools with validation.

    These tools allow running queries in read-only mode, but validate that
    queries are SELECT-only before execution.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_run_live_query(
        query: str,
        host_ids: list[int] | None = None,
        label_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Execute a SELECT-only live query against specified hosts.

        This tool is available in read-only mode with allow_select_queries enabled.
        Only SELECT statements are allowed - any data modification operations
        (INSERT, UPDATE, DELETE, etc.) will be rejected.

        Args:
            query: SQL SELECT query string to execute
            host_ids: List of specific host IDs to target
            label_ids: List of label IDs to target hosts
            team_ids: List of team IDs to target hosts

        Returns:
            Dict containing campaign information and initial status.
        """
        # Validate query is SELECT-only
        is_valid, error_msg = validate_select_query(query)
        if not is_valid:
            return {
                "success": False,
                "message": f"Query validation failed: {error_msg}. Only SELECT queries are allowed in read-only mode.",
                "campaign": None,
                "query": query,
            }

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
                    return {
                        "success": True,
                        "campaign": campaign,
                        "campaign_id": campaign.get("id"),
                        "query": query,
                        "message": f"Started live query campaign {campaign.get('id')} (SELECT-only validated)",
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
    async def fleet_run_saved_query(
        query_id: int,
        host_ids: list[int] | None = None,
        label_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Run a saved query against specified hosts (SELECT-only validation).

        This tool is available in read-only mode with allow_select_queries enabled.
        The saved query will be validated to ensure it's SELECT-only before execution.

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
                # First, get the query to validate it
                query_response = await client.get(f"/queries/{query_id}")

                if not query_response.success or not query_response.data:
                    return {
                        "success": False,
                        "message": f"Failed to retrieve query {query_id}: {query_response.message}",
                        "campaign": None,
                        "query_id": query_id,
                    }

                query_data = query_response.data.get("query", {})
                query_sql = query_data.get("query", "")

                # Validate query is SELECT-only
                is_valid, error_msg = validate_select_query(query_sql)
                if not is_valid:
                    return {
                        "success": False,
                        "message": f"Saved query validation failed: {error_msg}. Only SELECT queries are allowed in read-only mode.",
                        "campaign": None,
                        "query_id": query_id,
                        "query_name": query_data.get("name", ""),
                    }

                # Run the query
                json_data: dict[str, Any] = {"query_id": query_id}

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
                    return {
                        "success": True,
                        "campaign": campaign,
                        "campaign_id": campaign.get("id"),
                        "query_id": query_id,
                        "query_name": query_data.get("name", ""),
                        "message": f"Started campaign {campaign.get('id')} for query '{query_data.get('name')}' (SELECT-only validated)",
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

    @mcp.tool()
    async def fleet_query_host(host_id: int, query: str) -> dict[str, Any]:
        """Run a SELECT-only ad-hoc query against a specific host and get results.

        This tool is available in read-only mode with allow_select_queries enabled.
        Only SELECT statements are allowed - any data modification operations will be rejected.

        The query runs immediately against a single host and waits for results.
        The query will timeout if the host doesn't respond within the configured
        FLEET_LIVE_QUERY_REST_PERIOD (default 25 seconds).

        Args:
            host_id: ID of the host to query
            query: SQL SELECT query string to execute

        Returns:
            Dict containing query results from the host.
        """
        # Validate query is SELECT-only
        is_valid, error_msg = validate_select_query(query)
        if not is_valid:
            return {
                "success": False,
                "message": f"Query validation failed: {error_msg}. Only SELECT queries are allowed in read-only mode.",
                "host_id": host_id,
                "query": query,
                "rows": [],
                "row_count": 0,
            }

        try:
            async with client:
                response = await client.post(
                    f"/hosts/{host_id}/query", json_data={"query": query}
                )

                if response.success and response.data:
                    rows = response.data.get("rows", [])
                    return {
                        "success": True,
                        "host_id": host_id,
                        "query": query,
                        "rows": rows,
                        "row_count": len(rows),
                        "message": f"Query executed successfully on host {host_id}, returned {len(rows)} rows (SELECT-only validated)",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "host_id": host_id,
                        "query": query,
                        "rows": [],
                        "row_count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to query host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to query host: {str(e)}",
                "host_id": host_id,
                "query": query,
                "rows": [],
                "row_count": 0,
            }

    @mcp.tool()
    async def fleet_query_host_by_identifier(
        identifier: str, query: str
    ) -> dict[str, Any]:
        """Run a SELECT-only ad-hoc query against a host identified by UUID/hostname/serial.

        This tool is available in read-only mode with allow_select_queries enabled.
        Only SELECT statements are allowed - any data modification operations will be rejected.

        The query runs immediately against a single host and waits for results.
        The query will timeout if the host doesn't respond within the configured
        FLEET_LIVE_QUERY_REST_PERIOD (default 25 seconds).

        Args:
            identifier: Host UUID, hostname, or hardware serial number
            query: SQL SELECT query string to execute

        Returns:
            Dict containing query results from the host.
        """
        # Validate query is SELECT-only
        is_valid, error_msg = validate_select_query(query)
        if not is_valid:
            return {
                "success": False,
                "message": f"Query validation failed: {error_msg}. Only SELECT queries are allowed in read-only mode.",
                "identifier": identifier,
                "query": query,
                "rows": [],
                "row_count": 0,
            }

        try:
            async with client:
                # First get the host to find its ID
                response = await client.get(f"/hosts/identifier/{identifier}")

                if not response.success or not response.data:
                    return {
                        "success": False,
                        "message": f"Host not found: {identifier}",
                        "identifier": identifier,
                        "query": query,
                        "rows": [],
                        "row_count": 0,
                    }

                host = response.data.get("host", {})
                host_id = host.get("id")

                # Now run the query
                query_response = await client.post(
                    f"/hosts/{host_id}/query", json_data={"query": query}
                )

                if query_response.success and query_response.data:
                    rows = query_response.data.get("rows", [])
                    return {
                        "success": True,
                        "identifier": identifier,
                        "host_id": host_id,
                        "hostname": host.get("hostname", ""),
                        "query": query,
                        "rows": rows,
                        "row_count": len(rows),
                        "message": f"Query executed successfully on {host.get('hostname', identifier)}, returned {len(rows)} rows (SELECT-only validated)",
                    }
                else:
                    return {
                        "success": False,
                        "message": query_response.message,
                        "identifier": identifier,
                        "host_id": host_id,
                        "query": query,
                        "rows": [],
                        "row_count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to query host {identifier}: {e}")
            return {
                "success": False,
                "message": f"Failed to query host: {str(e)}",
                "identifier": identifier,
                "query": query,
                "rows": [],
                "row_count": 0,
            }
