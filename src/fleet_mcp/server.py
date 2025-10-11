"""Fleet MCP Server - Main MCP server implementation."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import FleetClient
from .config import FleetConfig, get_default_config_file, load_config
from .tools import host_tools, policy_tools, query_tools, software_tools, team_tools

logger = logging.getLogger(__name__)


class FleetMCPServer:
    """Fleet MCP Server for handling Fleet DM interactions."""

    def __init__(self, config: FleetConfig | None = None):
        """Initialize Fleet MCP Server.
        
        Args:
            config: Optional Fleet configuration. If not provided, will load from environment/file.
        """
        if config is None:
            config_file = get_default_config_file()
            config = load_config(config_file if config_file.exists() else None)

        self.config = config
        self.client = FleetClient(config)

        # Initialize FastMCP server
        readonly_note = " (READ-ONLY MODE - no write operations available)" if self.config.readonly else ""
        self.mcp = FastMCP(
            name=f"Fleet DM Server{readonly_note}",
            instructions=f"""
            You are a Fleet DM management assistant{readonly_note}. You can help with:

            - Managing hosts and devices in the fleet{"" if not self.config.readonly else " (read-only)"}
            - {"Viewing" if self.config.readonly else "Creating and running"} osquery queries
            - {"Viewing" if self.config.readonly else "Managing"} compliance policies
            - Tracking software inventory and vulnerabilities
            - {"Viewing" if self.config.readonly else "Managing"} teams and users
            - Monitoring fleet activities and security events

            {"Note: This server is in READ-ONLY mode. No create, update, or delete operations are available." if self.config.readonly else ""}

            Use the available tools to interact with the Fleet DM instance.
            Always provide clear, actionable information in your responses.
            """
        )

        # Register all tool categories
        self._register_tools()

    def _register_tools(self) -> None:
        """Register MCP tools with the server based on configuration."""
        # Always register read-only tools
        host_tools.register_read_tools(self.mcp, self.client)
        query_tools.register_read_tools(self.mcp, self.client)
        policy_tools.register_read_tools(self.mcp, self.client)
        software_tools.register_tools(self.mcp, self.client)  # Software tools are all read-only
        team_tools.register_read_tools(self.mcp, self.client)

        # Only register write tools if not in readonly mode
        if not self.config.readonly:
            host_tools.register_write_tools(self.mcp, self.client)
            query_tools.register_write_tools(self.mcp, self.client)
            policy_tools.register_write_tools(self.mcp, self.client)
            team_tools.register_write_tools(self.mcp, self.client)

        # Register server health check tool (always available)
        self._register_health_check()

    def _register_health_check(self) -> None:
        """Register health check tool."""

        @self.mcp.tool()
        async def fleet_health_check() -> dict[str, Any]:
            """Check Fleet server connectivity and authentication.
            
            Returns:
                Dict containing health check results and server information.
            """
            try:
                async with self.client:
                    response = await self.client.health_check()

                    return {
                        "success": response.success,
                        "message": response.message,
                        "server_url": self.config.server_url,
                        "status": "healthy" if response.success else "unhealthy",
                        "details": response.data or {}
                    }

            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return {
                    "success": False,
                    "message": f"Health check failed: {str(e)}",
                    "server_url": self.config.server_url,
                    "status": "error"
                }

    def run(self) -> None:
        """Run the MCP server."""
        logger.info(f"Starting Fleet MCP Server for {self.config.server_url}")
        self.mcp.run()


def create_server(config: FleetConfig | None = None) -> FleetMCPServer:
    """Create and configure Fleet MCP Server.
    
    Args:
        config: Optional Fleet configuration
        
    Returns:
        Configured FleetMCPServer instance
    """
    return FleetMCPServer(config)


def main() -> None:
    """Main entry point for Fleet MCP Server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        server = create_server()
        server.run()
    except Exception as e:
        logger.error(f"Failed to start Fleet MCP Server: {e}")
        raise
