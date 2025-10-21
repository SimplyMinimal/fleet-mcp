"""Fleet MCP - Model Context Protocol tool for Fleet DM integration.

This package provides MCP tools for interacting with Fleet DM instances,
enabling agentic AIs to manage devices, run queries, enforce policies,
and monitor security across fleets of computers.
"""

__version__ = "1.0.1"
__author__ = "Fleet MCP Contributors"
__email__ = "fleet-mcp@example.com"

from .client import FleetClient
from .config import FleetConfig
from .server import FleetMCPServer

__all__ = [
    "FleetClient",
    "FleetConfig",
    "FleetMCPServer",
]
