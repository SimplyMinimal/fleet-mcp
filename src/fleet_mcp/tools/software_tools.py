"""Software and vulnerability management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register software and vulnerability management tools with the MCP server.
    
    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_software(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "name",
        order_direction: str = "asc",
        query: str = "",
        team_id: int | None = None,
        vulnerable: bool | None = None
    ) -> dict[str, Any]:
        """List software inventory across the fleet.
        
        Args:
            page: Page number for pagination (0-based)
            per_page: Number of software items per page
            order_key: Field to order by (name, hosts_count, vulnerabilities_count)
            order_direction: Sort direction (asc, desc)
            query: Search query to filter software by name
            team_id: Filter software by team ID
            vulnerable: Filter to only vulnerable software (true) or non-vulnerable (false)
            
        Returns:
            Dict containing list of software and pagination metadata.
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
                if vulnerable is not None:
                    params["vulnerable"] = str(vulnerable).lower()

                response = await client.get("/software", params=params)

                if response.success and response.data:
                    software = response.data.get("software", [])
                    return {
                        "success": True,
                        "software": software,
                        "count": len(software),
                        "total_count": response.data.get("count", len(software)),
                        "page": page,
                        "per_page": per_page,
                        "message": f"Found {len(software)} software items"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "software": [],
                        "count": 0
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list software: {e}")
            return {
                "success": False,
                "message": f"Failed to list software: {str(e)}",
                "software": [],
                "count": 0
            }

    @mcp.tool()
    async def fleet_get_software(software_id: int) -> dict[str, Any]:
        """Get detailed information about a specific software item.
        
        Args:
            software_id: ID of the software item to retrieve
            
        Returns:
            Dict containing detailed software information including vulnerabilities.
        """
        try:
            async with client:
                response = await client.get(f"/software/{software_id}")

                if response.success and response.data:
                    software = response.data.get("software", {})
                    return {
                        "success": True,
                        "software": software,
                        "software_id": software_id,
                        "vulnerabilities": software.get("vulnerabilities", []),
                        "hosts_count": software.get("hosts_count", 0),
                        "message": f"Retrieved software '{software.get('name', software_id)}'"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "software": None,
                        "software_id": software_id
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get software {software_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get software: {str(e)}",
                "software": None,
                "software_id": software_id
            }

    @mcp.tool()
    async def fleet_get_host_software(
        host_id: int,
        query: str = "",
        vulnerable: bool | None = None
    ) -> dict[str, Any]:
        """Get software installed on a specific host.

        Args:
            host_id: ID of the host to get software for
            query: Search query to filter software by name (case-insensitive)
            vulnerable: Filter to only vulnerable software (true) or non-vulnerable (false)

        Returns:
            Dict containing software installed on the host.
        """
        try:
            async with client:
                # Use the standard host endpoint which includes software by default
                response = await client.get(f"/hosts/{host_id}")

                if response.success and response.data:
                    host = response.data.get("host", {})
                    all_software = host.get("software", [])

                    # Filter software based on query and vulnerable parameters
                    filtered_software = []
                    for software in all_software:
                        # Apply query filter (case-insensitive search in name)
                        if query and query.lower() not in software.get("name", "").lower():
                            continue

                        # Apply vulnerable filter
                        if vulnerable is not None:
                            software_vulnerable = len(software.get("vulnerabilities", [])) > 0
                            if vulnerable != software_vulnerable:
                                continue

                        filtered_software.append(software)

                    return {
                        "success": True,
                        "software": filtered_software,
                        "count": len(filtered_software),
                        "total_software": len(all_software),
                        "host_id": host_id,
                        "hostname": host.get("hostname", "Unknown"),
                        "message": f"Found {len(filtered_software)} software items on host {host.get('hostname', host_id)}"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "software": [],
                        "count": 0,
                        "total_software": 0,
                        "host_id": host_id,
                        "hostname": "Unknown"
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get host software: {e}")
            return {
                "success": False,
                "message": f"Failed to get host software: {str(e)}",
                "software": [],
                "count": 0,
                "total_software": 0,
                "host_id": host_id,
                "hostname": "Unknown"
            }

    @mcp.tool()
    async def fleet_get_vulnerabilities(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "cve",
        order_direction: str = "asc",
        team_id: int | None = None,
        known_exploit: bool | None = None,
        cve_search: str = ""
    ) -> dict[str, Any]:
        """List known vulnerabilities across the fleet.
        
        Args:
            page: Page number for pagination (0-based)
            per_page: Number of vulnerabilities per page
            order_key: Field to order by (cve, created_at, hosts_count)
            order_direction: Sort direction (asc, desc)
            team_id: Filter vulnerabilities by team ID
            known_exploit: Filter to vulnerabilities with known exploits
            cve_search: Search for specific CVE IDs
            
        Returns:
            Dict containing list of vulnerabilities and pagination metadata.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                    "order_key": order_key,
                    "order_direction": order_direction
                }

                if team_id is not None:
                    params["team_id"] = team_id
                if known_exploit is not None:
                    params["exploit"] = str(known_exploit).lower()
                if cve_search:
                    params["cve"] = cve_search

                response = await client.get("/vulnerabilities", params=params)

                if response.success and response.data:
                    vulnerabilities = response.data.get("vulnerabilities", [])
                    return {
                        "success": True,
                        "vulnerabilities": vulnerabilities,
                        "count": len(vulnerabilities),
                        "total_count": response.data.get("count", len(vulnerabilities)),
                        "page": page,
                        "per_page": per_page,
                        "message": f"Found {len(vulnerabilities)} vulnerabilities"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "vulnerabilities": [],
                        "count": 0
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list vulnerabilities: {e}")
            return {
                "success": False,
                "message": f"Failed to list vulnerabilities: {str(e)}",
                "vulnerabilities": [],
                "count": 0
            }

    @mcp.tool()
    async def fleet_search_software(
        query: str,
        limit: int = 50,
        team_id: int | None = None,
        vulnerable: bool | None = None
    ) -> dict[str, Any]:
        """Search for software by name across the fleet.

        Args:
            query: Search term for software name
            limit: Maximum number of results to return
            team_id: Filter search by team ID
            vulnerable: Filter to only vulnerable software (true) or non-vulnerable (false)

        Returns:
            Dict containing matching software titles.
        """
        try:
            async with client:
                params = {
                    "query": query,
                    "per_page": min(limit, 500)
                }

                if team_id is not None:
                    params["team_id"] = team_id

                if vulnerable is not None:
                    params["vulnerable"] = str(vulnerable).lower()

                # Use the correct software titles endpoint
                response = await client.get("/software/titles", params=params)

                if response.success and response.data:
                    software_titles = response.data.get("software_titles", [])
                    return {
                        "success": True,
                        "software_titles": software_titles,
                        "count": len(software_titles),
                        "query": query,
                        "message": f"Found {len(software_titles)} software titles matching '{query}'"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "software_titles": [],
                        "count": 0,
                        "query": query
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to search software: {e}")
            return {
                "success": False,
                "message": f"Failed to search software: {str(e)}",
                "software_titles": [],
                "count": 0,
                "query": query
            }

    @mcp.tool()
    async def fleet_find_software_on_host(
        hostname: str,
        software_name: str
    ) -> dict[str, Any]:
        """Find specific software on a host by hostname.

        This is useful for answering questions like "What version of Firefox is XYZ-Machine using?"

        Args:
            hostname: The hostname of the host to search
            software_name: The name of the software to find (case-insensitive)

        Returns:
            Dict containing the software information if found.
        """
        try:
            async with client:
                # First, find the host by hostname
                host_response = await client.get("/hosts", params={"query": hostname})

                if not host_response.success or not host_response.data:
                    return {
                        "success": False,
                        "message": f"Failed to find host with hostname '{hostname}': {host_response.message}",
                        "hostname": hostname,
                        "software_name": software_name,
                        "software": []
                    }

                hosts = host_response.data.get("hosts", [])
                target_host = None

                # Find exact hostname match
                for host in hosts:
                    if host.get("hostname", "").lower() == hostname.lower():
                        target_host = host
                        break

                if not target_host:
                    return {
                        "success": False,
                        "message": f"No host found with exact hostname '{hostname}'. Found {len(hosts)} hosts matching the search.",
                        "hostname": hostname,
                        "software_name": software_name,
                        "software": [],
                        "similar_hosts": [h.get("hostname", "Unknown") for h in hosts[:5]]
                    }

                # Get software for the host
                host_id = target_host.get("id")
                software_response = await fleet_get_host_software(host_id, query=software_name)

                if software_response.get("success"):
                    matching_software = software_response.get("software", [])
                    return {
                        "success": True,
                        "hostname": target_host.get("hostname"),
                        "host_id": host_id,
                        "software_name": software_name,
                        "software": matching_software,
                        "count": len(matching_software),
                        "message": f"Found {len(matching_software)} software items matching '{software_name}' on host '{hostname}'"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to get software for host '{hostname}': {software_response.get('message')}",
                        "hostname": hostname,
                        "software_name": software_name,
                        "software": []
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to find software on host: {e}")
            return {
                "success": False,
                "message": f"Failed to find software on host: {str(e)}",
                "hostname": hostname,
                "software_name": software_name,
                "software": []
            }
