"""Host management tools for Fleet MCP."""

import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from ..client import FleetClient, FleetAPIError

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register host management tools with the MCP server.
    
    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    
    @mcp.tool()
    async def fleet_list_hosts(
        page: int = 0,
        per_page: int = 100,
        query: str = "",
        team_id: Optional[int] = None,
        status: Optional[str] = None,
        order_key: str = "hostname",
        order_direction: str = "asc"
    ) -> Dict[str, Any]:
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
                    "order_direction": order_direction
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
                        "message": f"Found {len(hosts)} hosts"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "hosts": [],
                        "count": 0
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to list hosts: {e}")
            return {
                "success": False,
                "message": f"Failed to list hosts: {str(e)}",
                "hosts": [],
                "count": 0
            }
    
    @mcp.tool()
    async def fleet_get_host(host_id: int) -> Dict[str, Any]:
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
                        "message": f"Retrieved host {host.get('hostname', host_id)}"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "host": None
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to get host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get host: {str(e)}",
                "host": None
            }
    
    @mcp.tool()
    async def fleet_search_hosts(
        query: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search for hosts by hostname, UUID, hardware serial, or IP address.
        
        Args:
            query: Search term (hostname, UUID, serial number, or IP)
            limit: Maximum number of results to return
            
        Returns:
            Dict containing matching hosts.
        """
        try:
            async with client:
                params = {
                    "query": query,
                    "per_page": min(limit, 500)
                }
                
                response = await client.get("/hosts", params=params)
                
                if response.success and response.data:
                    hosts = response.data.get("hosts", [])
                    return {
                        "success": True,
                        "hosts": hosts,
                        "count": len(hosts),
                        "query": query,
                        "message": f"Found {len(hosts)} hosts matching '{query}'"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "hosts": [],
                        "count": 0,
                        "query": query
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to search hosts: {e}")
            return {
                "success": False,
                "message": f"Failed to search hosts: {str(e)}",
                "hosts": [],
                "count": 0,
                "query": query
            }
    
    @mcp.tool()
    async def fleet_get_host_by_identifier(identifier: str) -> Dict[str, Any]:
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
                        "message": f"Found host with identifier '{identifier}'"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "host": None,
                        "identifier": identifier
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to get host by identifier {identifier}: {e}")
            return {
                "success": False,
                "message": f"Failed to get host: {str(e)}",
                "host": None,
                "identifier": identifier
            }
    
    @mcp.tool()
    async def fleet_delete_host(host_id: int) -> Dict[str, Any]:
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
                    "message": response.message or f"Host {host_id} deleted successfully",
                    "host_id": host_id
                }
        
        except FleetAPIError as e:
            logger.error(f"Failed to delete host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete host: {str(e)}",
                "host_id": host_id
            }
    
    @mcp.tool()
    async def fleet_transfer_hosts(
        team_id: int,
        host_ids: List[int]
    ) -> Dict[str, Any]:
        """Transfer hosts to a different team.
        
        Args:
            team_id: Target team ID (use 0 for "No team")
            host_ids: List of host IDs to transfer
            
        Returns:
            Dict indicating success or failure of the transfer.
        """
        try:
            async with client:
                json_data = {
                    "team_id": team_id,
                    "hosts": host_ids
                }
                
                response = await client.post("/hosts/transfer", json_data=json_data)
                
                return {
                    "success": response.success,
                    "message": response.message or f"Transferred {len(host_ids)} hosts to team {team_id}",
                    "team_id": team_id,
                    "host_ids": host_ids,
                    "transferred_count": len(host_ids) if response.success else 0
                }
        
        except FleetAPIError as e:
            logger.error(f"Failed to transfer hosts: {e}")
            return {
                "success": False,
                "message": f"Failed to transfer hosts: {str(e)}",
                "team_id": team_id,
                "host_ids": host_ids,
                "transferred_count": 0
            }
