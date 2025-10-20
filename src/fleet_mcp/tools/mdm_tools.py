"""MDM (Mobile Device Management) tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all MDM management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only MDM management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_mdm_commands(
        page: int = 0,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """List MDM commands that have been executed.

        Returns a list of MDM commands (Apple and Windows) that have been
        sent to devices, including their status and results.

        Args:
            page: Page number for pagination (0-based)
            per_page: Number of commands per page

        Returns:
            Dict containing list of MDM commands with their status.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": per_page,
                }
                response = await client.get(
                    "/api/latest/fleet/mdm/apple/commands", params=params
                )
                data = response.data or {}
                results = data.get("results", [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(results)} MDM commands",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to list MDM commands: {e}")
            return {
                "success": False,
                "message": f"Failed to list MDM commands: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_mdm_command_results(
        command_uuid: str | None = None,
    ) -> dict[str, Any]:
        """Get results of MDM commands.

        Retrieves the results of MDM commands. If command_uuid is provided,
        returns results for that specific command. Otherwise returns all results.

        Args:
            command_uuid: Optional UUID of a specific command to get results for

        Returns:
            Dict containing MDM command results.
        """
        try:
            async with client:
                params = {}
                if command_uuid:
                    params["command_uuid"] = command_uuid

                response = await client.get(
                    "/api/latest/fleet/mdm/apple/commandresults",
                    params=params if params else None,
                )
                data = response.data or {}
                results = data.get("results", [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(results)} command results",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get MDM command results: {e}")
            return {
                "success": False,
                "message": f"Failed to get command results: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_list_mdm_profiles(
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """List MDM configuration profiles.

        Lists all MDM configuration profiles for Apple devices.
        Can be filtered by team.

        Args:
            team_id: Optional team ID to filter profiles

        Returns:
            Dict containing list of MDM configuration profiles.
        """
        try:
            async with client:
                params = {}
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get(
                    "/api/latest/fleet/mdm/apple/profiles",
                    params=params if params else None,
                )
                data = response.data or {}
                profiles = data.get("profiles", [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(profiles)} MDM profiles",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to list MDM profiles: {e}")
            return {
                "success": False,
                "message": f"Failed to list MDM profiles: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_host_mdm_profiles(host_id: int) -> dict[str, Any]:
        """Get MDM profiles installed on a specific host.

        Returns the list of MDM configuration profiles that are installed
        or pending installation on a specific host.

        Args:
            host_id: ID of the host

        Returns:
            Dict containing the host's MDM profiles and their status.
        """
        try:
            async with client:
                response = await client.get(
                    f"/api/latest/fleet/hosts/{host_id}/configuration_profiles"
                )
                data = response.data or {}
                profiles = data.get("profiles", [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(profiles)} profiles for host {host_id}",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get host MDM profiles: {e}")
            return {
                "success": False,
                "message": f"Failed to get host profiles: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_mdm_profiles_summary(
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Get summary of MDM profile deployment status.

        Returns aggregated statistics about MDM profile deployment across
        the fleet, including counts of verified, pending, and failed profiles.

        Args:
            team_id: Optional team ID to scope the summary

        Returns:
            Dict containing MDM profiles deployment summary.
        """
        try:
            async with client:
                params = {}
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get(
                    "/api/latest/fleet/mdm/apple/profiles/summary",
                    params=params if params else None,
                )
                return {
                    "success": True,
                    "message": "Retrieved MDM profiles summary",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get MDM profiles summary: {e}")
            return {
                "success": False,
                "message": f"Failed to get profiles summary: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_filevault_summary(
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Get FileVault encryption summary.

        Returns aggregated statistics about FileVault disk encryption
        status across macOS hosts.

        Args:
            team_id: Optional team ID to scope the summary

        Returns:
            Dict containing FileVault encryption summary.
        """
        try:
            async with client:
                params = {}
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get(
                    "/api/latest/fleet/mdm/apple/filevault/summary",
                    params=params if params else None,
                )
                return {
                    "success": True,
                    "message": "Retrieved FileVault summary",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get FileVault summary: {e}")
            return {
                "success": False,
                "message": f"Failed to get FileVault summary: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_list_mdm_devices() -> dict[str, Any]:
        """List all MDM-enrolled Apple devices.

        Returns a list of all Apple devices that are enrolled in MDM,
        including their serial numbers and enrollment status.

        Returns:
            Dict containing list of MDM-enrolled devices.
        """
        try:
            async with client:
                response = await client.get("/api/latest/fleet/mdm/apple/devices")
                data = response.data or {}
                devices = data.get("devices", [])
                return {
                    "success": True,
                    "message": f"Retrieved {len(devices)} MDM devices",
                    "data": data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to list MDM devices: {e}")
            return {
                "success": False,
                "message": f"Failed to list MDM devices: {str(e)}",
                "data": None,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write MDM management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_upload_mdm_profile(
        profile_content: str,
        team_id: int | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Upload a new MDM configuration profile.

        Uploads a custom MDM configuration profile (.mobileconfig for Apple,
        .xml for Windows) to Fleet. The profile will be deployed to devices
        based on team assignment and optional label filters.

        Args:
            profile_content: The profile content (XML/plist format)
            team_id: Optional team ID to assign the profile to
            labels: Optional list of label names to filter deployment

        Returns:
            Dict containing the created profile information.
        """
        try:
            async with client:
                payload: dict[str, Any] = {
                    "profile": profile_content,
                }
                if team_id is not None:
                    payload["team_id"] = team_id
                if labels is not None:
                    payload["labels"] = labels

                response = await client.post(
                    "/api/latest/fleet/configuration_profiles", json_data=payload
                )
                return {
                    "success": True,
                    "message": "MDM profile uploaded successfully",
                    "data": response,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to upload MDM profile: {e}")
            return {
                "success": False,
                "message": f"Failed to upload profile: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_delete_mdm_profile(profile_uuid: str) -> dict[str, Any]:
        """Delete an MDM configuration profile.

        Removes a custom MDM configuration profile from Fleet. This will
        also remove the profile from all devices where it's installed.

        Note: Fleet-managed profiles (FileVault, etc.) cannot be deleted
        using this endpoint.

        Args:
            profile_uuid: UUID of the profile to delete

        Returns:
            Dict containing the result of the deletion.
        """
        try:
            async with client:
                await client.delete(
                    f"/api/latest/fleet/configuration_profiles/{profile_uuid}"
                )
                return {
                    "success": True,
                    "message": f"MDM profile {profile_uuid} deleted successfully",
                    "data": None,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to delete MDM profile {profile_uuid}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete profile: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_lock_device(host_id: int) -> dict[str, Any]:
        """Lock an MDM-enrolled device remotely.

        Sends a DeviceLock command to an MDM-enrolled Apple device,
        which will lock the device and require a PIN to unlock.

        Args:
            host_id: ID of the host to lock

        Returns:
            Dict containing the result of the lock command.
        """
        try:
            async with client:
                await client.post(f"/api/latest/fleet/hosts/{host_id}/lock")
                return {
                    "success": True,
                    "message": f"Device lock command sent to host {host_id}",
                    "data": None,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to lock device {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to lock device: {str(e)}",
                "data": None,
            }

    # TODO: Keep this disabled as it is highly dangerous. Revisit later if really needed.
    # @mcp.tool()
    # async def fleet_wipe_device(host_id: int) -> dict[str, Any]:
    #     return {
    #         "success": False,
    #         "message": "Wipe device tool not allowed",
    #         "data": None,
    #     }
    #     """Wipe an MDM-enrolled device remotely.

    #     Sends an EraseDevice command to an MDM-enrolled Apple device,
    #     which will erase all data on the device. This action is irreversible.

    #     Args:
    #         host_id: ID of the host to wipe

    #     Returns:
    #         Dict containing the result of the wipe command.
    #     """
    #     try:
    #         async with client:
    #             await client.post(f"/api/latest/fleet/hosts/{host_id}/wipe")
    #             return {
    #                 "success": True,
    #                 "message": f"Device wipe command sent to host {host_id}",
    #                 "data": None,
    #             }
    #     except FleetAPIError as e:
    #         logger.error(f"Failed to wipe device {host_id}: {e}")
    #         return {
    #             "success": False,
    #             "message": f"Failed to wipe device: {str(e)}",
    #             "data": None,
    #         }

