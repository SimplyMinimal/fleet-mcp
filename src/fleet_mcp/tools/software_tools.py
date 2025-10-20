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
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only software management tools with the MCP server.

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
        vulnerable: bool | None = None,
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
                    "order_direction": order_direction,
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
                        "message": f"Found {len(software)} software items",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "software": [],
                        "count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list software: {e}")
            return {
                "success": False,
                "message": f"Failed to list software: {str(e)}",
                "software": [],
                "count": 0,
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
                        "message": f"Retrieved software '{software.get('name', software_id)}'",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "software": None,
                        "software_id": software_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get software {software_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get software: {str(e)}",
                "software": None,
                "software_id": software_id,
            }

    @mcp.tool()
    async def fleet_get_host_software(
        host_id: int, query: str = "", vulnerable: bool | None = None
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
                        if (
                            query
                            and query.lower() not in software.get("name", "").lower()
                        ):
                            continue

                        # Apply vulnerable filter
                        if vulnerable is not None:
                            software_vulnerable = (
                                len(software.get("vulnerabilities", [])) > 0
                            )
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
                        "message": f"Found {len(filtered_software)} software items on host {host.get('hostname', host_id)}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "software": [],
                        "count": 0,
                        "total_software": 0,
                        "host_id": host_id,
                        "hostname": "Unknown",
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
                "hostname": "Unknown",
            }

    @mcp.tool()
    async def fleet_get_vulnerabilities(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "cve",
        order_direction: str = "asc",
        team_id: int | None = None,
        known_exploit: bool | None = None,
        cve_search: str = "",
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
                    "order_direction": order_direction,
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
                        "message": f"Found {len(vulnerabilities)} vulnerabilities",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "vulnerabilities": [],
                        "count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list vulnerabilities: {e}")
            return {
                "success": False,
                "message": f"Failed to list vulnerabilities: {str(e)}",
                "vulnerabilities": [],
                "count": 0,
            }

    @mcp.tool()
    async def fleet_get_cve(cve: str, team_id: int | None = None) -> dict[str, Any]:
        """Get detailed information about a specific CVE.

        Returns comprehensive information about a CVE including affected
        software, OS versions, and hosts.

        Args:
            cve: CVE identifier (e.g., CVE-2021-44228)
            team_id: Optional team ID to filter results

        Returns:
            Dict containing CVE details, affected software, and OS versions.

        Note:
            If the CVE is known to Fleet but doesn't affect any hosts, the API
            returns HTTP 204 (No Content) and this tool will return success=True
            with empty software/os_versions lists.
        """
        try:
            async with client:
                params = {}
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get(
                    f"/api/latest/fleet/vulnerabilities/{cve}",
                    params=params if params else None,
                )

                # Handle empty response (HTTP 204 - CVE known but no affected hosts)
                if response.data is None or not response.data:
                    return {
                        "success": True,
                        "message": f"CVE {cve} is known to Fleet but does not affect any hosts",
                        "data": {
                            "vulnerability": None,
                            "software": [],
                            "os_versions": [],
                            "affected_software_count": 0,
                            "affected_os_count": 0,
                        },
                    }

                data = response.data
                vulnerability = data.get("vulnerability")
                software = data.get("software") or []
                os_versions = data.get("os_versions") or []

                return {
                    "success": True,
                    "message": f"Retrieved CVE {cve}",
                    "data": {
                        "vulnerability": vulnerability,
                        "software": software,
                        "os_versions": os_versions,
                        "affected_software_count": len(software),
                        "affected_os_count": len(os_versions),
                    },
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get CVE {cve}: {e}")
            # Check if it's a 404 (CVE not found)
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "message": f"CVE not found: {cve}",
                    "data": None,
                }
            return {
                "success": False,
                "message": f"Failed to get CVE: {error_msg}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_search_software(
        query: str,
        limit: int = 50,
        team_id: int | None = None,
        vulnerable: bool | None = None,
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
                params = {"query": query, "per_page": min(limit, 500)}

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
                        "message": f"Found {len(software_titles)} software titles matching '{query}'",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "software_titles": [],
                        "count": 0,
                        "query": query,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to search software: {e}")
            return {
                "success": False,
                "message": f"Failed to search software: {str(e)}",
                "software_titles": [],
                "count": 0,
                "query": query,
            }

    @mcp.tool()
    async def fleet_find_software_on_host(
        hostname: str, software_name: str
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
                        "software": [],
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
                        "similar_hosts": [
                            h.get("hostname", "Unknown") for h in hosts[:5]
                        ],
                    }

                # Get software for the host
                host_id = target_host.get("id")
                software_response = await fleet_get_host_software(
                    host_id, query=software_name
                )

                if software_response.get("success"):
                    matching_software = software_response.get("software", [])
                    return {
                        "success": True,
                        "hostname": target_host.get("hostname"),
                        "host_id": host_id,
                        "software_name": software_name,
                        "software": matching_software,
                        "count": len(matching_software),
                        "message": f"Found {len(matching_software)} software items matching '{software_name}' on host '{hostname}'",
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to get software for host '{hostname}': {software_response.get('message')}",
                        "hostname": hostname,
                        "software_name": software_name,
                        "software": [],
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to find software on host: {e}")
            return {
                "success": False,
                "message": f"Failed to find software on host: {str(e)}",
                "hostname": hostname,
                "software_name": software_name,
                "software": [],
            }

    @mcp.tool()
    async def fleet_get_software_install_result(install_uuid: str) -> dict[str, Any]:
        """Get the result of a software installation request.

        Args:
            install_uuid: UUID of the software installation request

        Returns:
            Dict containing the installation result including status and output.
        """
        try:
            async with client:
                response = await client.get(
                    f"/api/latest/fleet/software/install/{install_uuid}/results"
                )
                return {
                    "success": True,
                    "message": f"Retrieved install result for {install_uuid}",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get software install result: {e}")
            return {
                "success": False,
                "message": f"Failed to get install result: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_list_software_titles(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "name",
        order_direction: str = "asc",
        query: str = "",
        team_id: int | None = None,
        available_for_install: bool | None = None,
    ) -> dict[str, Any]:
        """List software titles in Fleet.

        Software titles represent unique software products that may have
        multiple versions installed across hosts. This is different from
        fleet_list_software which lists individual software versions.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of titles per page
            order_key: Field to order by (name, hosts_count)
            order_direction: Sort direction (asc, desc)
            query: Search query to filter titles by name
            team_id: Filter titles by team ID
            available_for_install: Filter to titles available for installation

        Returns:
            Dict containing list of software titles with aggregated information.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                    "order_key": order_key,
                    "order_direction": order_direction,
                }
                if query:
                    params["query"] = query
                if team_id is not None:
                    params["team_id"] = team_id
                if available_for_install is not None:
                    params["available_for_install"] = str(available_for_install).lower()

                response = await client.get(
                    "/api/latest/fleet/software/titles", params=params
                )
                data = response.data or {}
                titles = data.get("software_titles", [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(titles)} software titles",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to list software titles: {e}")
            return {
                "success": False,
                "message": f"Failed to list software titles: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_software_title(
        title_id: int,
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Get detailed information about a specific software title.

        Args:
            title_id: ID of the software title
            team_id: Optional team ID to scope the query

        Returns:
            Dict containing detailed software title information including
            versions, hosts, and installation options.
        """
        try:
            async with client:
                params = {}
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get(
                    f"/api/latest/fleet/software/titles/{title_id}",
                    params=params if params else None,
                )
                return {
                    "success": True,
                    "message": f"Retrieved software title {title_id}",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get software title {title_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get software title: {str(e)}",
                "data": None,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write software management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_install_software(
        host_id: int,
        software_title_id: int,
    ) -> dict[str, Any]:
        """Install software on a specific host.

        This triggers a software installation (VPP app or software package)
        on the specified host. The installation is asynchronous - use
        fleet_get_software_install_result to check the status.

        Args:
            host_id: ID of the host to install software on
            software_title_id: ID of the software title to install

        Returns:
            Dict containing the installation request details including install_uuid.
        """
        try:
            async with client:
                response = await client.post(
                    f"/api/latest/fleet/hosts/{host_id}/software/{software_title_id}/install"
                )
                return {
                    "success": True,
                    "message": f"Software installation initiated on host {host_id}",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(
                f"Failed to install software {software_title_id} on host {host_id}: {e}"
            )
            return {
                "success": False,
                "message": f"Failed to install software: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_batch_set_software(
        team_id: int | None,
        software: list[dict[str, Any]],
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Batch upload/set software installers for a team.

        This endpoint is asynchronous - it starts the process of downloading and
        uploading software installers in the background and returns a request UUID
        to query the status.

        Args:
            team_id: ID of the team (None for no team)
            software: List of software items with url, install_script, etc.
            dry_run: If True, validate without making changes

        Returns:
            Dict containing the request UUID to check status.

        Example:
            >>> software = [
            ...     {
            ...         "url": "https://example.com/app.pkg",
            ...         "install_script": "installer -pkg app.pkg -target /",
            ...         "pre_install_query": "SELECT 1 FROM apps WHERE name = 'App';",
            ...         "post_install_script": "echo 'Installed'",
            ...         "self_service": False
            ...     }
            ... ]
            >>> result = await fleet_batch_set_software(team_id=1, software=software)
            >>> request_uuid = result["request_uuid"]
        """
        try:
            async with client:
                json_data: dict[str, Any] = {"software": software}
                if team_id is not None:
                    json_data["team_id"] = team_id
                if dry_run:
                    json_data["dry_run"] = dry_run

                response = await client.post("/software/batch", json_data=json_data)

                if response.success and response.data:
                    return {
                        "success": True,
                        "request_uuid": response.data.get("request_uuid"),
                        "message": "Batch software upload initiated. Use request_uuid to check status.",
                        "team_id": team_id,
                        "software_count": len(software),
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "request_uuid": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to batch set software: {e}")
            return {
                "success": False,
                "message": f"Failed to batch set software: {str(e)}",
                "request_uuid": None,
            }
