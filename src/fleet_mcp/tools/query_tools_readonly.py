"""Read-only query tools with SELECT validation for Fleet MCP.

This module provides query execution tools that validate queries are SELECT-only
before execution, allowing safe query execution in read-only mode.
"""

import asyncio
import logging
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

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

    async def _execute_host_query_validated(
        host_id: int,
        query: str,
        identifier: str | None = None,
        hostname: str | None = None,
    ) -> dict[str, Any]:
        """Internal helper to execute a SELECT-validated query against a specific host.

        This function contains the shared logic for executing SELECT-validated queries
        via the Fleet API's /hosts/{id}/query endpoint and parsing the response.

        Args:
            host_id: ID of the host to query
            query: SQL query string to execute (already validated as SELECT-only)
            identifier: Optional original identifier used for lookup (for error messages)
            hostname: Optional hostname of the host (for success messages)

        Returns:
            Dict containing query results or error information.
        """
        try:
            response = await client.post(
                f"/hosts/{host_id}/query", json_data={"query": query}
            )

            if response.success and response.data:
                rows = response.data.get("rows", [])
                result: dict[str, Any] = {
                    "success": True,
                    "host_id": host_id,
                    "query": query,
                    "rows": rows,
                    "row_count": len(rows),
                }

                # Add optional fields if provided
                if identifier is not None:
                    result["identifier"] = identifier
                if hostname is not None:
                    result["hostname"] = hostname
                    result["message"] = (
                        f"Query executed successfully on {hostname}, "
                        f"returned {len(rows)} rows (SELECT-only validated)"
                    )
                else:
                    result["message"] = (
                        f"Query executed successfully on host {host_id}, "
                        f"returned {len(rows)} rows (SELECT-only validated)"
                    )

                return result
            else:
                error_result: dict[str, Any] = {
                    "success": False,
                    "message": response.message,
                    "host_id": host_id,
                    "query": query,
                    "rows": [],
                    "row_count": 0,
                }

                # Add optional fields if provided
                if identifier is not None:
                    error_result["identifier"] = identifier

                return error_result

        except FleetAPIError as e:
            error_context = identifier if identifier else str(host_id)
            logger.error(f"Failed to query host {error_context}: {e}")

            error_result = {
                "success": False,
                "message": f"Failed to query host: {str(e)}",
                "host_id": host_id,
                "query": query,
                "rows": [],
                "row_count": 0,
            }

            # Add optional fields if provided
            if identifier is not None:
                error_result["identifier"] = identifier

            return error_result

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

        async with client:
            return await _execute_host_query_validated(host_id, query)

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

        The tool automatically handles partial hostname matching - if you provide
        a short hostname like 'host-abc123', it will find the full hostname
        'host-abc123.example.com' automatically.

        Args:
            identifier: Host UUID, hostname (full or partial), or hardware serial number
            query: SQL SELECT query string to execute

        Returns:
            Dict containing query results from the host.
        """
        from ..utils import resolve_host_identifier

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

        async with client:
            # Resolve the identifier to a host
            result = await resolve_host_identifier(client, identifier)

            if not result.success or result.host_id is None:
                return {
                    "success": False,
                    "message": result.error_message or f"Host not found: {identifier}",
                    "identifier": identifier,
                    "query": query,
                    "rows": [],
                    "row_count": 0,
                }

            # Execute query using shared helper
            return await _execute_host_query_validated(
                host_id=result.host_id,
                query=query,
                identifier=identifier,
                hostname=result.hostname,
            )

    @mcp.tool()
    async def fleet_run_live_query_with_results(
        query: str,
        host_ids: list[int] | None = None,
        label_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
        target_all_online_hosts: bool = False,
        timeout: float = 60.0,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Execute a SELECT-only live query and wait for results via WebSocket.

        This tool is available in read-only mode with allow_select_queries enabled.
        Only SELECT statements are allowed - any data modification operations will be rejected.

        This tool runs a live query campaign and collects results in real-time
        via WebSocket. It creates a campaign, connects to Fleet's WebSocket API,
        and streams results back as they arrive. Progress notifications are sent
        as results arrive.

        ⚠️  IMPORTANT NOTES:
        1. This tool BLOCKS until timeout or all results are collected
        2. You will see progress updates as hosts respond
        3. Not all hosts may respond within the timeout period
        4. Results are collected in real-time as they stream in

        TARGETING REQUIREMENTS:
        At least ONE of the following targeting parameters is REQUIRED:
        - host_ids: List of specific host IDs
        - label_ids: List of label IDs
        - team_ids: List of team IDs
        - target_all_online_hosts: Set to True to target all online hosts

        Args:
            query: SQL SELECT query string to execute on target hosts
            host_ids: List of specific host IDs to target
            label_ids: List of label IDs to target hosts with those labels
            team_ids: List of team IDs to target hosts in those teams (use 0 for "No team")
            target_all_online_hosts: If True, automatically targets all online hosts
            timeout: Maximum seconds to wait for results (default: 60)
            ctx: MCP context for progress reporting (auto-injected)

        Returns:
            Dict containing query results from all responding hosts.

        Examples:
            # Query all online hosts with 30s timeout
            fleet_run_live_query_with_results(
                query="SELECT * FROM uptime",
                target_all_online_hosts=True,
                timeout=30.0
            )

            # Query specific hosts
            fleet_run_live_query_with_results(
                query="SELECT * FROM system_info",
                host_ids=[1, 2, 3],
                timeout=45.0
            )

            # Query hosts in "No team"
            fleet_run_live_query_with_results(
                query="SELECT * FROM users",
                team_ids=[0]
            )
        """
        import time

        from ..websocket_client import FleetWebSocketClient

        # Step 1: Validate query is SELECT-only
        is_valid, error_message = validate_select_query(query)
        if not is_valid:
            if ctx:
                await ctx.error(f"Query validation failed: {error_message}")
            return {
                "success": False,
                "message": f"Query validation failed: {error_message}",
                "results": [],
                "result_count": 0,
            }

        # Step 2: Validate targeting parameters
        if not any([host_ids, label_ids, team_ids, target_all_online_hosts]):
            error_msg = (
                "At least one targeting parameter is required. "
                "The Fleet API does not support querying without specifying targets. "
                "\n\nOptions to target all hosts:\n"
                "1. Use target_all_online_hosts=True (fetches all online hosts automatically)\n"
                "2. Use team_ids=[0] to target all hosts in 'No team'\n"
                "3. Fetch host IDs first with fleet_list_hosts(status='online') and pass to host_ids\n"
                "4. Use label_ids with a label that includes all hosts (e.g., 'All Hosts' label)\n"
                "\nExample: fleet_run_live_query_with_results(query='SELECT * FROM uptime', team_ids=[0])"
            )
            if ctx:
                await ctx.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "results": [],
                "result_count": 0,
            }

        try:
            async with client:
                # Step 3: Handle target_all_online_hosts
                if target_all_online_hosts and not host_ids:
                    if ctx:
                        await ctx.info("Fetching all online hosts...")

                    response = await client.get(
                        "/hosts", params={"status": "online", "per_page": 500}
                    )

                    if response.success and response.data:
                        hosts = response.data.get("hosts", [])
                        host_ids = [h["id"] for h in hosts]

                        if not host_ids:
                            error_msg = "No online hosts found"
                            if ctx:
                                await ctx.warning(error_msg)
                            return {
                                "success": False,
                                "message": error_msg,
                                "results": [],
                                "result_count": 0,
                            }

                        if ctx:
                            await ctx.info(f"Targeting {len(host_ids)} online hosts")
                    else:
                        error_msg = f"Failed to fetch online hosts: {response.message}"
                        if ctx:
                            await ctx.error(error_msg)
                        return {
                            "success": False,
                            "message": error_msg,
                            "results": [],
                            "result_count": 0,
                        }

                # Step 4: Build selected targets
                json_data: dict[str, Any] = {"query": query}

                if host_ids:
                    json_data["selected"] = {"hosts": host_ids}
                elif label_ids:
                    json_data["selected"] = {"labels": label_ids}
                elif team_ids:
                    json_data["selected"] = {"teams": team_ids}

                # Step 5: Create live query campaign
                if ctx:
                    await ctx.info("Creating live query campaign...")

                response = await client.post("/queries/run", json_data=json_data)

                if not response.success or not response.data:
                    error_msg = f"Failed to create campaign: {response.message}"
                    if ctx:
                        await ctx.error(error_msg)
                    return {
                        "success": False,
                        "message": error_msg,
                        "results": [],
                        "result_count": 0,
                    }

                campaign = response.data.get("campaign", {})
                campaign_id = campaign.get("id")

                if not campaign_id:
                    error_msg = "Failed to get campaign ID from response"
                    if ctx:
                        await ctx.error(error_msg)
                    return {
                        "success": False,
                        "message": error_msg,
                        "results": [],
                        "result_count": 0,
                    }

                # Get total hosts from campaign metrics
                metrics = campaign.get("Metrics", {})
                total_hosts = metrics.get("TotalHosts", len(host_ids or []))

                if ctx:
                    await ctx.info(
                        f"Campaign {campaign_id} created for {total_hosts} hosts "
                        f"({metrics.get('OnlineHosts', 0)} online, "
                        f"{metrics.get('OfflineHosts', 0)} offline)"
                    )

                # Step 6: Connect WebSocket and collect results
                if ctx:
                    await ctx.info("Connecting to WebSocket for real-time results...")

                try:
                    async with FleetWebSocketClient(client.config) as ws_client:
                        await ws_client.subscribe_to_campaign(campaign_id)

                        if ctx:
                            await ctx.info(
                                f"Subscribed to campaign {campaign_id}, collecting results..."
                            )

                        results: list[dict[str, Any]] = []
                        start_time = time.time()
                        last_progress_report = 0.0
                        heartbeat_task = None
                        stream_active = True

                        # Background heartbeat task to prevent MCP timeout
                        # This runs independently of WebSocket message arrival
                        async def heartbeat_loop() -> None:
                            """Send periodic progress updates every 5 seconds."""
                            last_heartbeat = 0.0
                            while stream_active:
                                await asyncio.sleep(1.0)  # Check every second
                                current_time = time.time()
                                if ctx and current_time - last_heartbeat >= 5.0:
                                    await ctx.report_progress(
                                        progress=len(results), total=total_hosts
                                    )
                                    last_heartbeat = current_time
                                    elapsed = current_time - start_time
                                    logger.debug(
                                        f"Heartbeat: {len(results)}/{total_hosts} results "
                                        f"after {elapsed:.1f}s"
                                    )

                        # Start background heartbeat task
                        if ctx:
                            heartbeat_task = asyncio.create_task(heartbeat_loop())

                        try:
                            async for message in ws_client.stream_messages(timeout):
                                msg_type = message.get("type")
                                data = message.get("data", {})
                                current_time = time.time()

                                if msg_type == "result":
                                    results.append(data)

                                    # Report progress when results arrive (throttle to every 0.5 seconds)
                                    if (
                                        ctx
                                        and current_time - last_progress_report >= 0.5
                                    ):
                                        await ctx.report_progress(
                                            progress=len(results), total=total_hosts
                                        )
                                        last_progress_report = current_time

                                    # Log progress
                                    elapsed = current_time - start_time
                                    if ctx and len(results) % 10 == 0:
                                        await ctx.info(
                                            f"Received {len(results)}/{total_hosts} results "
                                            f"({elapsed:.1f}s elapsed)"
                                        )

                                elif msg_type == "totals":
                                    # Update total if it changes
                                    new_total = data.get("count", total_hosts)
                                    if new_total != total_hosts:
                                        total_hosts = new_total
                                        if ctx:
                                            await ctx.info(
                                                f"Updated target count: {total_hosts} hosts"
                                            )

                                elif msg_type == "status":
                                    status = data.get("status")
                                    if status == "finished":
                                        if ctx:
                                            await ctx.info("Campaign completed")
                                        break

                                elif msg_type == "error":
                                    error = data.get("error", "Unknown error")
                                    if ctx:
                                        await ctx.warning(f"WebSocket error: {error}")

                        finally:
                            # Stop heartbeat task
                            stream_active = False
                            if heartbeat_task:
                                heartbeat_task.cancel()
                                try:
                                    await heartbeat_task
                                except asyncio.CancelledError:
                                    pass

                        # Final progress report
                        if ctx:
                            await ctx.report_progress(
                                progress=len(results), total=total_hosts
                            )
                            elapsed = time.time() - start_time
                            await ctx.info(
                                f"Collected {len(results)}/{total_hosts} results in {elapsed:.1f}s"
                            )

                        return {
                            "success": True,
                            "campaign_id": campaign_id,
                            "query": query,
                            "results": results,
                            "result_count": len(results),
                            "total_hosts": total_hosts,
                            "elapsed_seconds": time.time() - start_time,
                            "message": f"Collected {len(results)} results from {total_hosts} targeted hosts (SELECT-only validated)",
                        }

                except Exception as ws_error:
                    error_msg = f"WebSocket error: {str(ws_error)}"
                    if ctx:
                        await ctx.error(error_msg)
                    logger.error(f"WebSocket connection failed: {ws_error}")
                    return {
                        "success": False,
                        "message": error_msg,
                        "campaign_id": campaign_id,
                        "results": [],
                        "result_count": 0,
                    }

        except FleetAPIError as e:
            error_msg = f"Failed to run live query: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            logger.error(f"Failed to run live query with results: {e}")
            return {
                "success": False,
                "message": error_msg,
                "results": [],
                "result_count": 0,
            }
