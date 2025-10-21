"""Configuration management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all configuration management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only configuration management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_get_config() -> dict[str, Any]:
        """Get the current Fleet application configuration.

        Returns the complete Fleet configuration including server settings,
        integrations, MDM settings, and more. Sensitive values are obfuscated.

        Returns:
            Dict containing the complete Fleet configuration.

        Example:
            >>> result = await fleet_get_config()
            >>> print(result)
            {
                "success": True,
                "message": "Retrieved Fleet configuration",
                "data": {
                    "org_info": {
                        "org_name": "Acme Corp",
                        "org_logo_url": "https://example.com/logo.png"
                    },
                    "server_settings": {
                        "server_url": "https://fleet.example.com",
                        "live_query_disabled": False
                    },
                    "integrations": {...},
                    "mdm": {...}
                }
            }
        """
        try:
            async with client:
                response = await client.get("/api/latest/fleet/config")
                return {
                    "success": True,
                    "message": "Retrieved Fleet configuration",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get Fleet config: {e}")
            return {
                "success": False,
                "message": f"Failed to get config: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_enroll_secrets() -> dict[str, Any]:
        """Get the enrollment secrets configuration.

        Returns the enrollment secrets used for enrolling new hosts to Fleet.
        These secrets are used by osquery agents to authenticate with Fleet.

        Returns:
            Dict containing enrollment secrets for global and team-specific enrollment.
        """
        try:
            async with client:
                response = await client.get("/api/latest/fleet/spec/enroll_secret")
                return {
                    "success": True,
                    "message": "Retrieved enrollment secrets",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get enrollment secrets: {e}")
            return {
                "success": False,
                "message": f"Failed to get enrollment secrets: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_certificate() -> dict[str, Any]:
        """Get the Fleet server certificate chain.

        Returns the PEM-encoded certificate chain used for osqueryd TLS termination.

        Returns:
            Dict containing the certificate chain.
        """
        try:
            async with client:
                response = await client.get("/api/latest/fleet/config/certificate")
                return {
                    "success": True,
                    "message": "Retrieved certificate chain",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get certificate: {e}")
            return {
                "success": False,
                "message": f"Failed to get certificate: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_version() -> dict[str, Any]:
        """Get the Fleet server version information.

        Returns version information about the Fleet server including
        version number, branch, revision, and build date.

        Returns:
            Dict containing Fleet server version information.
        """
        try:
            async with client:
                response = await client.get("/api/latest/fleet/version")
                return {
                    "success": True,
                    "message": "Retrieved Fleet version",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get Fleet version: {e}")
            return {
                "success": False,
                "message": f"Failed to get version: {str(e)}",
                "data": None,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write configuration management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_update_config(
        config: dict[str, Any],
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Update the Fleet application configuration.

        Updates Fleet's configuration settings. Use dry_run=True to validate
        changes without applying them.

        Args:
            config: Configuration object with settings to update
            force: Bypass strict JSON validation
            dry_run: Validate changes without applying them

        Returns:
            Dict containing the updated configuration.
        """
        try:
            async with client:
                # Build query string
                query_params = []
                if force:
                    query_params.append("force=true")
                if dry_run:
                    query_params.append("dry_run=true")

                endpoint = "/api/latest/fleet/config"
                if query_params:
                    endpoint += "?" + "&".join(query_params)

                response = await client.patch(
                    endpoint,
                    json_data=config,
                )
                return {
                    "success": True,
                    "message": (
                        "Updated Fleet configuration"
                        if not dry_run
                        else "Configuration validation passed"
                    ),
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to update Fleet config: {e}")
            return {
                "success": False,
                "message": f"Failed to update config: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_update_enroll_secrets(
        secrets: list[str],
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Update the enrollment secrets configuration.

        Updates the enrollment secrets used for enrolling new hosts.

        Args:
            secrets: List of enrollment secret strings
            dry_run: Validate changes without applying them

        Returns:
            Dict containing the result of the update.
        """
        try:
            async with client:
                payload = {"spec": {"secrets": [{"secret": s} for s in secrets]}}

                endpoint = "/api/latest/fleet/spec/enroll_secret"
                if dry_run:
                    endpoint += "?dry_run=true"

                await client.post(
                    endpoint,
                    json_data=payload,
                )
                return {
                    "success": True,
                    "message": (
                        "Updated enrollment secrets"
                        if not dry_run
                        else "Enrollment secrets validation passed"
                    ),
                    "data": None,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to update enrollment secrets: {e}")
            return {
                "success": False,
                "message": f"Failed to update enrollment secrets: {str(e)}",
                "data": None,
            }
