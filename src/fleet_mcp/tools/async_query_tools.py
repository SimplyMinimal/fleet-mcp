"""Async query management tools for Fleet MCP.

These tools provide asynchronous query execution to work around the 60-second
MCP client timeout limitation in TypeScript-based clients like LM Studio.
"""

import logging
import time
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ..async_query_manager import QueryStatus, get_async_query_manager
from ..client import FleetClient
from ..config import FleetConfig
from .common import format_error_response, format_success_response

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient, config: FleetConfig) -> None:
    """Register async query management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
        config: Fleet configuration
    """
    manager = get_async_query_manager(config)

    @mcp.tool()
    async def fleet_get_query_results(
        campaign_id: int,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Retrieve results from a previously started asynchronous query.

        This tool retrieves the current status and results of an async query
        that was started with fleet_run_live_query_with_results in async mode.

        Args:
            campaign_id: The campaign ID returned by fleet_run_live_query_with_results

        Returns:
            Dict containing:
            - success: Whether the request was successful
            - status: Current status (pending/running/completed/failed/cancelled)
            - campaign_id: The campaign ID
            - query: The SQL query that was executed
            - total_hosts: Total number of hosts targeted
            - results_count: Number of results received so far
            - results: List of query results (if completed or partial if running)
            - error: Error message if failed
            - created_at: Timestamp when query was created
            - started_at: Timestamp when query started running
            - completed_at: Timestamp when query completed
            - elapsed_time: Time elapsed since query started (seconds)

        Examples:
            # Get results for a completed query
            fleet_get_query_results(campaign_id=12345)

            # Check status of a running query
            fleet_get_query_results(campaign_id=12346)
        """

        try:
            job = await manager.get_job(campaign_id)

            if not job:
                return format_error_response(
                    f"Query job {campaign_id} not found",
                    campaign_id=campaign_id,
                )

            elapsed_time = None
            if job.started_at:
                if job.completed_at:
                    elapsed_time = job.completed_at - job.started_at
                else:
                    elapsed_time = time.time() - job.started_at

            response = format_success_response(
                f"Retrieved query results for campaign {campaign_id}",
                status=job.status.value,
                campaign_id=job.campaign_id,
                query=job.query,
                total_hosts=job.total_hosts,
                results_count=job.results_count,
                results=job.results,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                elapsed_time=elapsed_time,
                metadata=job.metadata,
            )

            if job.error:
                response["error"] = job.error

            # Provide user-friendly status message
            if ctx:
                if job.status == QueryStatus.COMPLETED:
                    await ctx.info(
                        f"Query completed: {job.results_count} results from "
                        f"{job.total_hosts} hosts in {elapsed_time:.1f}s"
                    )
                elif job.status == QueryStatus.RUNNING:
                    await ctx.info(
                        f"Query running: {job.results_count}/{job.total_hosts} results "
                        f"after {elapsed_time:.1f}s"
                    )
                elif job.status == QueryStatus.FAILED:
                    await ctx.warning(f"Query failed: {job.error}")
                elif job.status == QueryStatus.CANCELLED:
                    await ctx.info("Query was cancelled")
                elif job.status == QueryStatus.PENDING:
                    await ctx.info("Query is pending execution")

            return response

        except Exception as e:
            logger.error(f"Failed to get query results for {campaign_id}: {e}")
            return format_error_response(
                f"Failed to get query results: {str(e)}",
                campaign_id=campaign_id,
            )

    @mcp.tool()
    async def fleet_list_async_queries(
        status: str | None = None,
        limit: int = 50,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """List all asynchronous query jobs.

        This tool lists all async queries with their current status, allowing you
        to track running queries and retrieve completed results.

        Args:
            status: Optional status filter (pending/running/completed/failed/cancelled)
            limit: Maximum number of queries to return (default: 50)

        Returns:
            Dict containing:
            - success: Whether the request was successful
            - queries: List of query job summaries
            - count: Number of queries returned
            - total_count: Total number of queries (before limit)

        Examples:
            # List all queries
            fleet_list_async_queries()

            # List only running queries
            fleet_list_async_queries(status="running")

            # List last 10 queries
            fleet_list_async_queries(limit=10)
        """

        try:
            status_filter = None
            if status:
                try:
                    status_filter = QueryStatus(status.lower())
                except ValueError:
                    return format_error_response(
                        f"Invalid status: {status}. Must be one of: "
                        f"{', '.join(s.value for s in QueryStatus)}"
                    )

            jobs = await manager.list_jobs(status_filter=status_filter, limit=limit)

            # Get total count before limit
            all_jobs = await manager.list_jobs(status_filter=status_filter)
            total_count = len(all_jobs)

            queries = []
            for job in jobs:
                elapsed_time = None
                if job.started_at:
                    if job.completed_at:
                        elapsed_time = job.completed_at - job.started_at
                    else:
                        elapsed_time = time.time() - job.started_at

                query_summary = {
                    "campaign_id": job.campaign_id,
                    "status": job.status.value,
                    "query": (
                        job.query[:100] + "..." if len(job.query) > 100 else job.query
                    ),
                    "total_hosts": job.total_hosts,
                    "results_count": job.results_count,
                    "created_at": job.created_at,
                    "elapsed_time": elapsed_time,
                }

                if job.error:
                    query_summary["error"] = job.error

                queries.append(query_summary)

            if ctx:
                running_count = sum(
                    1 for j in all_jobs if j.status == QueryStatus.RUNNING
                )
                completed_count = sum(
                    1 for j in all_jobs if j.status == QueryStatus.COMPLETED
                )
                await ctx.info(
                    f"Found {total_count} queries ({running_count} running, "
                    f"{completed_count} completed)"
                )

            return format_success_response(
                f"Found {len(queries)} async queries",
                queries=queries,
                count=len(queries),
                total_count=total_count,
            )

        except Exception as e:
            logger.error(f"Failed to list async queries: {e}")
            return format_error_response(
                f"Failed to list async queries: {str(e)}",
                queries=[],
                count=0,
            )

    @mcp.tool()
    async def fleet_cancel_query(
        campaign_id: int,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Cancel a running asynchronous query.

        This tool cancels a running async query. Completed, failed, or already
        cancelled queries cannot be cancelled.

        Args:
            campaign_id: The campaign ID of the query to cancel

        Returns:
            Dict containing:
            - success: Whether the cancellation was successful
            - message: Status message
            - campaign_id: The campaign ID

        Examples:
            # Cancel a running query
            fleet_cancel_query(campaign_id=12345)
        """

        try:
            job = await manager.get_job(campaign_id)

            if not job:
                return format_error_response(
                    f"Query job {campaign_id} not found",
                    campaign_id=campaign_id,
                )

            if job.status in (
                QueryStatus.COMPLETED,
                QueryStatus.FAILED,
                QueryStatus.CANCELLED,
            ):
                return format_error_response(
                    f"Cannot cancel query with status: {job.status.value}",
                    campaign_id=campaign_id,
                    status=job.status.value,
                )

            cancelled = await manager.cancel_job(campaign_id)

            if cancelled:
                if ctx:
                    await ctx.info(f"Successfully cancelled query {campaign_id}")
                return format_success_response(
                    f"Query {campaign_id} cancelled successfully",
                    campaign_id=campaign_id,
                )
            else:
                return format_error_response(
                    f"Failed to cancel query {campaign_id}",
                    campaign_id=campaign_id,
                )

        except Exception as e:
            logger.error(f"Failed to cancel query {campaign_id}: {e}")
            return format_error_response(
                f"Failed to cancel query: {str(e)}",
                campaign_id=campaign_id,
            )
