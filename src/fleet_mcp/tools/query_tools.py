"""Query management tools for Fleet MCP."""

import asyncio
import logging
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ..client import FleetAPIError, FleetClient
from ..config import FleetConfig

logger = logging.getLogger(__name__)


def register_tools(
    mcp: FastMCP, client: FleetClient, config: FleetConfig | None = None
) -> None:
    """Register all query management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
        config: Fleet configuration (optional, for async query mode)
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client, config)


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
        - Ad-hoc queries that haven't been saved and scheduled
        - Queries that don't have 'interval' configured

        For running ad-hoc queries and getting results, use:
        - fleet_query_host(host_id, query) - Run query on ONE host and get results
        - fleet_query_host_by_identifier(identifier, query) - Run query by hostname/UUID
        - fleet_run_live_query_with_results(query, ...) - Run query across multiple hosts and collect results

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


def register_write_tools(
    mcp: FastMCP, client: FleetClient, config: FleetConfig | None = None
) -> None:
    """Register write query management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
        config: Fleet configuration (optional, for async query mode)
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
        """Execute a live query and wait for results via WebSocket.

        This tool runs a live query campaign and collects results in real-time
        via WebSocket. It creates a campaign, connects to Fleet's WebSocket API,
        and streams results back as they arrive. Progress notifications are sent
        as results arrive.

        ⚠️  IMPORTANT NOTES:
        1. This tool BLOCKS until timeout or all results are collected
        2. You will see progress updates as hosts respond
        3. Not all hosts may respond within the timeout period
        4. Results are collected in real-time as they stream in

        🔄 ASYNC MODE (when FLEET_USE_ASYNC_QUERY_MODE=true):
        - Query starts in the background and returns immediately with a campaign_id
        - Use fleet_get_query_results(campaign_id) to retrieve results later
        - Use fleet_list_async_queries() to see all running/completed queries
        - Use fleet_cancel_query(campaign_id) to cancel a running query
        - This mode works around the 60-second MCP client timeout limitation

        TARGETING REQUIREMENTS:
        At least ONE of the following targeting parameters is REQUIRED:
        - host_ids: List of specific host IDs
        - label_ids: List of label IDs
        - team_ids: List of team IDs
        - target_all_online_hosts: Set to True to target all online hosts

        Args:
            query: SQL query string to execute on target hosts
            host_ids: List of specific host IDs to target
            label_ids: List of label IDs to target hosts with those labels
            team_ids: List of team IDs to target hosts in those teams (use 0 for "No team")
            target_all_online_hosts: If True, automatically targets all online hosts
            timeout: Maximum seconds to wait for results (default: 60)
            ctx: MCP context for progress reporting (auto-injected)

        Returns:
            Dict containing query results from all responding hosts.
            In async mode, returns campaign_id and status instead of results.

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

        # Check if async mode is enabled
        use_async_mode = config and config.use_async_query_mode

        # Step 1: Validate targeting parameters
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
                # Step 2: Handle target_all_online_hosts
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

                # Step 3: Build selected targets
                json_data: dict[str, Any] = {"query": query}

                if host_ids:
                    json_data["selected"] = {"hosts": host_ids}
                elif label_ids:
                    json_data["selected"] = {"labels": label_ids}
                elif team_ids:
                    json_data["selected"] = {"teams": team_ids}

                # Step 4: Create live query campaign
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

                # Step 5: Handle async mode if enabled
                if use_async_mode:
                    from ..async_query_manager import get_async_query_manager

                    manager = get_async_query_manager(config)

                    # Create async job
                    await manager.create_job(
                        campaign_id=campaign_id,
                        query=query,
                        metadata={
                            "host_ids": host_ids,
                            "label_ids": label_ids,
                            "team_ids": team_ids,
                            "target_all_online_hosts": target_all_online_hosts,
                            "timeout": timeout,
                        },
                    )

                    await manager.set_total_hosts(campaign_id, total_hosts)

                    # Start background task to collect results
                    async def collect_results_background() -> None:
                        """Background task to collect query results."""
                        try:
                            await manager.update_job_status(
                                campaign_id, QueryStatus.RUNNING
                            )

                            async with FleetWebSocketClient(client.config) as ws_client:
                                await ws_client.subscribe_to_campaign(campaign_id)

                                async for message in ws_client.stream_messages(timeout):
                                    msg_type = message.get("type")
                                    data = message.get("data", {})

                                    if msg_type == "result":
                                        await manager.add_result(campaign_id, data)
                                    elif msg_type == "totals":
                                        new_total = data.get("count", total_hosts)
                                        await manager.set_total_hosts(
                                            campaign_id, new_total
                                        )
                                    elif msg_type == "status":
                                        status = data.get("status")
                                        if status == "finished":
                                            break
                                    elif msg_type == "error":
                                        error = data.get("error", "Unknown error")
                                        await manager.update_job_status(
                                            campaign_id, QueryStatus.FAILED, error=error
                                        )
                                        return

                            # Mark as completed
                            await manager.update_job_status(
                                campaign_id, QueryStatus.COMPLETED
                            )

                        except Exception as e:
                            logger.error(f"Background query {campaign_id} failed: {e}")
                            await manager.update_job_status(
                                campaign_id, QueryStatus.FAILED, error=str(e)
                            )

                    # Import QueryStatus for background task
                    from ..async_query_manager import QueryStatus

                    # Start background task
                    task = asyncio.create_task(collect_results_background())
                    manager.register_background_task(campaign_id, task)

                    if ctx:
                        await ctx.info(
                            f"Query started in background mode. "
                            f"Use fleet_get_query_results(campaign_id={campaign_id}) to retrieve results."
                        )

                    return {
                        "success": True,
                        "async_mode": True,
                        "campaign_id": campaign_id,
                        "query": query,
                        "total_hosts": total_hosts,
                        "status": "running",
                        "message": (
                            f"Query started in background (campaign {campaign_id}). "
                            f"Use fleet_get_query_results({campaign_id}) to retrieve results."
                        ),
                    }

                # Step 6: Connect WebSocket and collect results (sync mode)
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
                            "message": f"Collected {len(results)} results from {total_hosts} targeted hosts",
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
