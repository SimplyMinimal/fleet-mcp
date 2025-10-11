"""Fleet MCP Server - Main MCP server implementation."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import FleetClient
from .config import FleetConfig, get_default_config_file, load_config
from .tools import host_tools, policy_tools, query_tools, software_tools, table_tools, team_tools
from .tools import query_tools_readonly

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

        self.config: FleetConfig = config
        self.client = FleetClient(config)

        # Initialize FastMCP server
        readonly_note = self._get_readonly_note()
        self.mcp = FastMCP(
            name=f"Fleet DM Server{readonly_note}",
            instructions=self._get_server_instructions()
        )

        # Register all tool categories
        self._register_tools()

    def _get_readonly_note(self) -> str:
        """Get the readonly mode note for server name."""
        if not self.config.readonly:
            return ""
        elif self.config.allow_select_queries:
            return " (READ-ONLY MODE - SELECT queries allowed)"
        else:
            return " (READ-ONLY MODE - no write operations available)"

    def _get_server_instructions(self) -> str:
        """Get server instructions based on configuration."""
        if not self.config.readonly:
            return """
            You are a Fleet DM management assistant. You can help with:

            - Managing hosts and devices in the fleet
            - Creating and running osquery queries
            - Managing compliance policies
            - Tracking software inventory and vulnerabilities
            - Managing teams and users
            - Monitoring fleet activities and security events

            Use the available tools to interact with the Fleet DM instance.
            Always provide clear, actionable information in your responses.
            """
        elif self.config.allow_select_queries:
            return """
            You are a Fleet DM management assistant (READ-ONLY MODE - SELECT queries allowed). You can help with:

            - Viewing hosts and devices in the fleet (read-only)
            - Running SELECT-only osquery queries for monitoring and investigation
            - Viewing compliance policies (read-only)
            - Tracking software inventory and vulnerabilities
            - Viewing teams and users (read-only)
            - Monitoring fleet activities and security events

            Note: This server is in READ-ONLY mode with SELECT queries enabled.
            - You can run SELECT queries to read data from hosts
            - All queries are validated to ensure they are SELECT-only
            - No create, update, or delete operations are available

            Use the available tools to interact with the Fleet DM instance.
            Always provide clear, actionable information in your responses.
            """
        else:
            return """
            You are a Fleet DM management assistant (READ-ONLY MODE). You can help with:

            - Viewing hosts and devices in the fleet (read-only)
            - Viewing saved osquery queries (read-only)
            - Viewing compliance policies (read-only)
            - Tracking software inventory and vulnerabilities
            - Viewing teams and users (read-only)
            - Monitoring fleet activities and security events

            Note: This server is in READ-ONLY mode. No create, update, delete, or query execution operations are available.

            Use the available tools to interact with the Fleet DM instance.
            Always provide clear, actionable information in your responses.
            """

    def _register_tools(self) -> None:
        """Register MCP tools with the server based on configuration."""
        # Always register read-only tools
        host_tools.register_read_tools(self.mcp, self.client)
        query_tools.register_read_tools(self.mcp, self.client)
        policy_tools.register_read_tools(self.mcp, self.client)
        software_tools.register_tools(self.mcp, self.client)  # Software tools are all read-only
        table_tools.register_tools(self.mcp, self.client)  # Table tools are all read-only
        team_tools.register_read_tools(self.mcp, self.client)

        # Register SELECT-only query tools if in readonly mode with allow_select_queries
        if self.config.readonly and self.config.allow_select_queries:
            query_tools_readonly.register_select_only_tools(self.mcp, self.client)

        # Only register full write tools if not in readonly mode
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
