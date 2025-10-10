"""Query management tools for Fleet MCP."""

import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from ..client import FleetClient, FleetAPIError

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register query management tools with the MCP server.
    
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
        team_id: Optional[int] = None
    ) -> Dict[str, Any]:
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
                    "order_direction": order_direction
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
                        "message": f"Found {len(queries)} queries"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "queries": [],
                        "count": 0
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to list queries: {e}")
            return {
                "success": False,
                "message": f"Failed to list queries: {str(e)}",
                "queries": [],
                "count": 0
            }
    
    @mcp.tool()
    async def fleet_create_query(
        name: str,
        query: str,
        description: Optional[str] = None,
        team_id: Optional[int] = None,
        observer_can_run: bool = False
    ) -> Dict[str, Any]:
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
                    "observer_can_run": observer_can_run
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
                        "message": f"Created query '{name}' with ID {query_data.get('id')}"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "query": None
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to create query: {e}")
            return {
                "success": False,
                "message": f"Failed to create query: {str(e)}",
                "query": None
            }
    
    @mcp.tool()
    async def fleet_run_live_query(
        query: str,
        host_ids: Optional[List[int]] = None,
        label_ids: Optional[List[int]] = None,
        team_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Run a live query against specified hosts.
        
        Args:
            query: SQL query string to execute
            host_ids: List of specific host IDs to target
            label_ids: List of label IDs to target hosts
            team_ids: List of team IDs to target hosts
            
        Returns:
            Dict containing query execution results and campaign information.
        """
        try:
            async with client:
                json_data = {
                    "query": query,
                    "selected": {
                        "hosts": host_ids or [],
                        "labels": label_ids or [],
                        "teams": team_ids or []
                    }
                }
                
                response = await client.post("/queries/run", json_data=json_data)
                
                if response.success and response.data:
                    campaign = response.data.get("campaign", {})
                    return {
                        "success": True,
                        "campaign": campaign,
                        "campaign_id": campaign.get("id"),
                        "query": query,
                        "message": f"Started live query campaign {campaign.get('id')}"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "campaign": None,
                        "query": query
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to run live query: {e}")
            return {
                "success": False,
                "message": f"Failed to run live query: {str(e)}",
                "campaign": None,
                "query": query
            }
    
    @mcp.tool()
    async def fleet_get_query_results(campaign_id: int) -> Dict[str, Any]:
        """Get results from a live query campaign.
        
        Args:
            campaign_id: ID of the query campaign
            
        Returns:
            Dict containing query results from all targeted hosts.
        """
        try:
            async with client:
                response = await client.get(f"/queries/{campaign_id}/results")
                
                if response.success and response.data:
                    results = response.data.get("results", [])
                    return {
                        "success": True,
                        "results": results,
                        "campaign_id": campaign_id,
                        "result_count": len(results),
                        "message": f"Retrieved {len(results)} query results"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "results": [],
                        "campaign_id": campaign_id,
                        "result_count": 0
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to get query results: {e}")
            return {
                "success": False,
                "message": f"Failed to get query results: {str(e)}",
                "results": [],
                "campaign_id": campaign_id,
                "result_count": 0
            }
    
    @mcp.tool()
    async def fleet_get_query(query_id: int) -> Dict[str, Any]:
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
                        "message": f"Retrieved query '{query_data.get('name', query_id)}'"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "query": None,
                        "query_id": query_id
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to get query {query_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get query: {str(e)}",
                "query": None,
                "query_id": query_id
            }
    
    @mcp.tool()
    async def fleet_delete_query(query_id: int) -> Dict[str, Any]:
        """Delete a saved query from Fleet.
        
        Args:
            query_id: ID of the query to delete
            
        Returns:
            Dict indicating success or failure of the deletion.
        """
        try:
            async with client:
                response = await client.delete(f"/queries/{query_id}")
                
                return {
                    "success": response.success,
                    "message": response.message or f"Query {query_id} deleted successfully",
                    "query_id": query_id
                }
        
        except FleetAPIError as e:
            logger.error(f"Failed to delete query {query_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete query: {str(e)}",
                "query_id": query_id
            }
    
    @mcp.tool()
    async def fleet_run_saved_query(
        query_id: int,
        host_ids: Optional[List[int]] = None,
        label_ids: Optional[List[int]] = None,
        team_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
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
                json_data = {
                    "selected": {
                        "hosts": host_ids or [],
                        "labels": label_ids or [],
                        "teams": team_ids or []
                    }
                }
                
                response = await client.post(f"/queries/{query_id}/run", json_data=json_data)
                
                if response.success and response.data:
                    campaign = response.data.get("campaign", {})
                    return {
                        "success": True,
                        "campaign": campaign,
                        "campaign_id": campaign.get("id"),
                        "query_id": query_id,
                        "message": f"Started saved query campaign {campaign.get('id')}"
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "campaign": None,
                        "query_id": query_id
                    }
        
        except FleetAPIError as e:
            logger.error(f"Failed to run saved query {query_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to run saved query: {str(e)}",
                "campaign": None,
                "query_id": query_id
            }
