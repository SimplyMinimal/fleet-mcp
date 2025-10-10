"""Software and vulnerability management tools for Fleet MCP."""

import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from ..client import FleetClient, FleetAPIError

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
        team_id: Optional[int] = None,
        vulnerable: Optional[bool] = None
    ) -> Dict[str, Any]:
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
    async def fleet_get_software(software_id: int) -> Dict[str, Any]:
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
        page: int = 0,
        per_page: int = 100,
        query: str = "",
        vulnerable: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get software installed on a specific host.
        
        Args:
            host_id: ID of the host to get software for
            page: Page number for pagination (0-based)
            per_page: Number of software items per page
            query: Search query to filter software by name
            vulnerable: Filter to only vulnerable software (true) or non-vulnerable (false)
            
        Returns:
            Dict containing software installed on the host.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page
                }
                
                if query:
                    params["query"] = query
                if vulnerable is not None:
                    params["vulnerable"] = str(vulnerable).lower()
                
                response = await client.get(f"/hosts/{host_id}/software", params=params)
                
                if response.success and response.data:
                    software = response.data.get("software", [])
                    return {
                        "success": True,
                        "software": software,
                        "count": len(software),
                        "host_id": host_id,
                        "page": page,
                        "per_page": per_page,
                        "message": f"Found {len(software)} software items on host {host_id}"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "software": [],
                        "count": 0,
                        "host_id": host_id
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to get host software: {e}")
            return {
                "success": False,
                "message": f"Failed to get host software: {str(e)}",
                "software": [],
                "count": 0,
                "host_id": host_id
            }
    
    @mcp.tool()
    async def fleet_get_vulnerabilities(
        page: int = 0,
        per_page: int = 100,
        order_key: str = "cve",
        order_direction: str = "asc",
        team_id: Optional[int] = None,
        known_exploit: Optional[bool] = None,
        cve_search: str = ""
    ) -> Dict[str, Any]:
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
        team_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Search for software by name across the fleet.
        
        Args:
            query: Search term for software name
            limit: Maximum number of results to return
            team_id: Filter search by team ID
            
        Returns:
            Dict containing matching software items.
        """
        try:
            async with client:
                params = {
                    "query": query,
                    "per_page": min(limit, 500)
                }
                
                if team_id is not None:
                    params["team_id"] = team_id
                
                response = await client.get("/software", params=params)
                
                if response.success and response.data:
                    software = response.data.get("software", [])
                    return {
                        "success": True,
                        "software": software,
                        "count": len(software),
                        "query": query,
                        "message": f"Found {len(software)} software items matching '{query}'"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "software": [],
                        "count": 0,
                        "query": query
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to search software: {e}")
            return {
                "success": False,
                "message": f"Failed to search software: {str(e)}",
                "software": [],
                "count": 0,
                "query": query
            }
