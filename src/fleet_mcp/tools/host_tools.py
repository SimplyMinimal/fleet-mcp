"""Host management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all host management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only host management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_hosts(
        page: int = 0,
        per_page: int = 100,
        query: str = "",
        team_id: int | None = None,
        status: str | None = None,
        order_key: str = "hostname",
        order_direction: str = "asc",
    ) -> dict[str, Any]:
        """List hosts in Fleet with optional filtering and pagination.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of hosts per page (max 500)
            query: Search query to filter hosts by hostname, UUID, hardware serial, or IPv4
            team_id: Filter hosts by team ID
            status: Filter by host status (online, offline, mia)
            order_key: Field to order by (hostname, computer_name, platform, status)
            order_direction: Sort direction (asc, desc)

        Returns:
            Dict containing list of hosts and pagination metadata.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": min(per_page, 500),  # Fleet API limit
                    "order_key": order_key,
                    "order_direction": order_direction,
                }

                if query:
                    params["query"] = query
                if team_id is not None:
                    params["team_id"] = team_id
                if status:
                    params["status"] = status

                response = await client.get("/hosts", params=params)

                if response.success and response.data:
                    hosts = response.data.get("hosts", [])
                    return {
                        "success": True,
                        "hosts": hosts,
                        "count": len(hosts),
                        "total_count": response.data.get("count", len(hosts)),
                        "page": page,
                        "per_page": per_page,
                        "message": f"Found {len(hosts)} hosts",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "hosts": [],
                        "count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list hosts: {e}")
            return {
                "success": False,
                "message": f"Failed to list hosts: {str(e)}",
                "hosts": [],
                "count": 0,
            }

    @mcp.tool()
    async def fleet_get_host(host_id: int) -> dict[str, Any]:
        """Get detailed information about a specific host.

        Args:
            host_id: The ID of the host to retrieve

        Returns:
            Dict containing detailed host information.
        """
        try:
            async with client:
                response = await client.get(f"/hosts/{host_id}")

                if response.success and response.data:
                    host = response.data.get("host", {})
                    return {
                        "success": True,
                        "host": host,
                        "message": f"Retrieved host {host.get('hostname', host_id)}",
                    }
                else:
                    return {"success": False, "message": response.message, "host": None}

        except FleetAPIError as e:
            logger.error(f"Failed to get host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get host: {str(e)}",
                "host": None,
            }

    @mcp.tool()
    async def fleet_search_hosts(query: str, limit: int = 50) -> dict[str, Any]:
        """Search for hosts by hostname, UUID, hardware serial, or IP address.

        Args:
            query: Search term (hostname, UUID, serial number, or IP)
            limit: Maximum number of results to return

        Returns:
            Dict containing matching hosts.
        """
        try:
            async with client:
                params = {"query": query, "per_page": min(limit, 500)}

                response = await client.get("/hosts", params=params)

                if response.success and response.data:
                    hosts = response.data.get("hosts", [])
                    return {
                        "success": True,
                        "hosts": hosts,
                        "count": len(hosts),
                        "query": query,
                        "message": f"Found {len(hosts)} hosts matching '{query}'",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "hosts": [],
                        "count": 0,
                        "query": query,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to search hosts: {e}")
            return {
                "success": False,
                "message": f"Failed to search hosts: {str(e)}",
                "hosts": [],
                "count": 0,
                "query": query,
            }

    @mcp.tool()
    async def fleet_get_host_by_identifier(identifier: str) -> dict[str, Any]:
        """Get host by hostname, UUID, or hardware serial number.

        Args:
            identifier: Host identifier (hostname, UUID, or hardware serial)

        Returns:
            Dict containing host information if found.
        """
        try:
            async with client:
                response = await client.get(f"/hosts/identifier/{identifier}")

                if response.success and response.data:
                    host = response.data.get("host", {})
                    return {
                        "success": True,
                        "host": host,
                        "identifier": identifier,
                        "message": f"Found host with identifier '{identifier}'",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "host": None,
                        "identifier": identifier,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get host by identifier {identifier}: {e}")
            return {
                "success": False,
                "message": f"Failed to get host: {str(e)}",
                "host": None,
                "identifier": identifier,
            }

    @mcp.tool()
    async def fleet_list_host_upcoming_activities(
        host_id: int,
        page: int = 0,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """List upcoming activities for a specific host.

        Args:
            host_id: ID of the host to get upcoming activities for
            page: Page number for pagination (0-based)
            per_page: Number of activities per page

        Returns:
            Dict containing list of upcoming activities and pagination metadata.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                }

                response = await client.get(
                    f"/hosts/{host_id}/activities/upcoming", params=params
                )

                if response.success and response.data:
                    activities = response.data.get("activities", [])
                    return {
                        "success": True,
                        "activities": activities,
                        "count": len(activities),
                        "host_id": host_id,
                        "page": page,
                        "per_page": per_page,
                        "message": f"Found {len(activities)} upcoming activities for host {host_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "activities": [],
                        "count": 0,
                        "host_id": host_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list upcoming activities for host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to list upcoming activities: {str(e)}",
                "activities": [],
                "count": 0,
                "host_id": host_id,
            }

    @mcp.tool()
    async def fleet_list_host_past_activities(
        host_id: int,
        page: int = 0,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """List past activities for a specific host.

        Args:
            host_id: ID of the host to get past activities for
            page: Page number for pagination (0-based)
            per_page: Number of activities per page

        Returns:
            Dict containing list of past activities and pagination metadata.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                }

                response = await client.get(
                    f"/hosts/{host_id}/activities", params=params
                )

                if response.success and response.data:
                    activities = response.data.get("activities", [])
                    return {
                        "success": True,
                        "activities": activities,
                        "count": len(activities),
                        "host_id": host_id,
                        "page": page,
                        "per_page": per_page,
                        "message": f"Found {len(activities)} past activities for host {host_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "activities": [],
                        "count": 0,
                        "host_id": host_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list past activities for host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to list past activities: {str(e)}",
                "activities": [],
                "count": 0,
                "host_id": host_id,
            }

    @mcp.tool()
    async def fleet_get_host_mdm(host_id: int) -> dict[str, Any]:
        """Get MDM information for a specific host.

        Args:
            host_id: ID of the host to get MDM information for

        Returns:
            Dict containing MDM information for the host.
        """
        try:
            async with client:
                response = await client.get(f"/hosts/{host_id}/mdm")

                if response.success and response.data:
                    return {
                        "success": True,
                        "mdm": response.data,
                        "host_id": host_id,
                        "message": f"Retrieved MDM information for host {host_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "mdm": None,
                        "host_id": host_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get MDM information for host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get MDM information: {str(e)}",
                "mdm": None,
                "host_id": host_id,
            }

    @mcp.tool()
    async def fleet_list_host_certificates(host_id: int) -> dict[str, Any]:
        """List certificates for a specific host.

        Args:
            host_id: ID of the host to get certificates for

        Returns:
            Dict containing list of certificates for the host.
        """
        try:
            async with client:
                response = await client.get(f"/hosts/{host_id}/certificates")

                if response.success and response.data:
                    certificates = response.data.get("certificates", [])
                    return {
                        "success": True,
                        "certificates": certificates,
                        "count": len(certificates),
                        "host_id": host_id,
                        "message": f"Found {len(certificates)} certificates for host {host_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "certificates": [],
                        "count": 0,
                        "host_id": host_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list certificates for host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to list certificates: {str(e)}",
                "certificates": [],
                "count": 0,
                "host_id": host_id,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write host management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_delete_host(host_id: int) -> dict[str, Any]:
        """Delete a host from Fleet.

        Note: A deleted host will fail authentication and may attempt to re-enroll
        if it still has a valid enroll secret.

        Args:
            host_id: The ID of the host to delete

        Returns:
            Dict indicating success or failure of the deletion.
        """
        try:
            async with client:
                response = await client.delete(f"/hosts/{host_id}")

                return {
                    "success": response.success,
                    "message": response.message
                    or f"Host {host_id} deleted successfully",
                    "host_id": host_id,
                }

        except FleetAPIError as e:
            logger.error(f"Failed to delete host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete host: {str(e)}",
                "host_id": host_id,
            }

    @mcp.tool()
    async def fleet_transfer_hosts(team_id: int, host_ids: list[int]) -> dict[str, Any]:
        """Transfer hosts to a different team.

        Args:
            team_id: Target team ID (use 0 for "No team")
            host_ids: List of host IDs to transfer

        Returns:
            Dict indicating success or failure of the transfer.
        """
        try:
            async with client:
                # Convert team_id=0 to null for "No team"
                json_data = {
                    "team_id": None if team_id == 0 else team_id,
                    "hosts": host_ids,
                }

                response = await client.post("/hosts/transfer", json_data=json_data)

                return {
                    "success": response.success,
                    "message": response.message
                    or f"Transferred {len(host_ids)} hosts to team {team_id}",
                    "team_id": team_id,
                    "host_ids": host_ids,
                    "transferred_count": len(host_ids) if response.success else 0,
                }

        except FleetAPIError as e:
            logger.error(f"Failed to transfer hosts: {e}")
            return {
                "success": False,
                "message": f"Failed to transfer hosts: {str(e)}",
                "team_id": team_id,
                "host_ids": host_ids,
                "transferred_count": 0,
            }

    @mcp.tool()
    async def fleet_query_host(host_id: int, query: str) -> dict[str, Any]:
        """Run an ad-hoc live query against a specific host and get results.

        This runs a query immediately against a single host and waits for results.
        The query will timeout if the host doesn't respond within the configured
        FLEET_LIVE_QUERY_REST_PERIOD (default 25 seconds).

        Args:
            host_id: ID of the host to query
            query: SQL query string to execute

        Returns:
            Dict containing query results from the host.
        """
        try:
            async with client:
                json_data = {"query": query}
                response = await client.post(
                    f"/hosts/{host_id}/query", json_data=json_data
                )

                if response.success and response.data:
                    return {
                        "success": True,
                        "host_id": host_id,
                        "query": query,
                        "status": response.data.get("status"),
                        "error": response.data.get("error"),
                        "rows": response.data.get("rows", []),
                        "row_count": len(response.data.get("rows", [])),
                        "message": f"Query executed on host {host_id}",
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
        """Run an ad-hoc live query against a host identified by UUID/hostname/serial.

        This runs a query immediately against a single host and waits for results.
        The query will timeout if the host doesn't respond within the configured
        FLEET_LIVE_QUERY_REST_PERIOD (default 25 seconds).

        Args:
            identifier: Host UUID, hostname, or hardware serial number
            query: SQL query string to execute

        Returns:
            Dict containing query results from the host.
        """
        try:
            async with client:
                json_data = {"query": query}
                response = await client.post(
                    f"/hosts/identifier/{identifier}/query", json_data=json_data
                )

                if response.success and response.data:
                    return {
                        "success": True,
                        "identifier": identifier,
                        "query": query,
                        "status": response.data.get("status"),
                        "error": response.data.get("error"),
                        "rows": response.data.get("rows", []),
                        "row_count": len(response.data.get("rows", [])),
                        "message": f"Query executed on host {identifier}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "identifier": identifier,
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

    @mcp.tool()
    async def fleet_cancel_host_activity(
        host_id: int, activity_id: str
    ) -> dict[str, Any]:
        """Cancel an upcoming activity for a specific host.

        Args:
            host_id: ID of the host
            activity_id: ID of the activity to cancel

        Returns:
            Dict indicating success or failure of the cancellation.
        """
        try:
            async with client:
                response = await client.delete(
                    f"/hosts/{host_id}/activities/upcoming/{activity_id}"
                )

                return {
                    "success": response.success,
                    "message": response.message
                    or f"Activity {activity_id} cancelled successfully for host {host_id}",
                    "host_id": host_id,
                    "activity_id": activity_id,
                }

        except FleetAPIError as e:
            logger.error(
                f"Failed to cancel activity {activity_id} for host {host_id}: {e}"
            )
            return {
                "success": False,
                "message": f"Failed to cancel activity: {str(e)}",
                "host_id": host_id,
                "activity_id": activity_id,
            }

    @mcp.tool()
    async def fleet_lock_host(host_id: int) -> dict[str, Any]:
        """Lock a host device remotely.

        This sends a lock command to the host device. The device will be locked
        and require authentication to unlock.

        Args:
            host_id: ID of the host to lock

        Returns:
            Dict containing lock status and any unlock PIN if applicable.
        """
        try:
            async with client:
                response = await client.post(f"/hosts/{host_id}/lock")

                if response.success and response.data:
                    return {
                        "success": True,
                        "host_id": host_id,
                        "device_status": response.data.get("device_status"),
                        "pending_action": response.data.get("pending_action"),
                        "unlock_pin": response.data.get("unlock_pin"),
                        "message": f"Lock command sent to host {host_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "host_id": host_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to lock host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to lock host: {str(e)}",
                "host_id": host_id,
            }

    @mcp.tool()
    async def fleet_unlock_host(host_id: int) -> dict[str, Any]:
        """Unlock a host device remotely.

        This sends an unlock command to the host device. For some platforms,
        this may return an unlock PIN that needs to be entered on the device.

        Args:
            host_id: ID of the host to unlock

        Returns:
            Dict containing unlock status and any unlock PIN if applicable.
        """
        try:
            async with client:
                response = await client.post(f"/hosts/{host_id}/unlock")

                if response.success and response.data:
                    return {
                        "success": True,
                        "host_id": host_id,
                        "device_status": response.data.get("device_status"),
                        "pending_action": response.data.get("pending_action"),
                        "unlock_pin": response.data.get("unlock_pin"),
                        "message": f"Unlock command sent to host {host_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "host_id": host_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to unlock host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to unlock host: {str(e)}",
                "host_id": host_id,
            }

    @mcp.tool()
    async def fleet_unenroll_host_mdm(host_id: int) -> dict[str, Any]:
        """Unenroll a host from MDM.

        This removes the host from MDM management. The host will no longer
        receive MDM profiles or commands.

        Args:
            host_id: ID of the host to unenroll from MDM

        Returns:
            Dict indicating success or failure of the unenrollment.
        """
        try:
            async with client:
                response = await client.delete(f"/hosts/{host_id}/mdm")

                return {
                    "success": response.success,
                    "message": response.message
                    or f"Host {host_id} unenrolled from MDM successfully",
                    "host_id": host_id,
                }

        except FleetAPIError as e:
            logger.error(f"Failed to unenroll host {host_id} from MDM: {e}")
            return {
                "success": False,
                "message": f"Failed to unenroll host from MDM: {str(e)}",
                "host_id": host_id,
            }
