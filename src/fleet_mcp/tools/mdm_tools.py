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

    @mcp.tool()
    async def fleet_get_bootstrap_metadata(
        team_id: int,
    ) -> dict[str, Any]:
        """Get metadata about a bootstrap package for a team.

        Returns information about the bootstrap package configured for a team,
        including name, SHA256 hash, and upload timestamp. Does not return the
        actual package bytes.

        Args:
            team_id: Team ID to get bootstrap package metadata for (0 for no team)

        Returns:
            Dict containing bootstrap package metadata.

        Example:
            >>> result = await fleet_get_bootstrap_metadata(team_id=0)
            >>> print(result)
            {
                "success": True,
                "message": "Retrieved bootstrap package metadata for team 0",
                "data": {
                    "name": "bootstrap.pkg",
                    "sha256": "abc123...",
                    "created_at": "2025-10-20T10:00:00Z",
                    "team_id": 0
                }
            }
        """
        try:
            async with client:
                response = await client.get(
                    f"/api/latest/fleet/bootstrap/{team_id}/metadata"
                )
                return {
                    "success": True,
                    "message": f"Retrieved bootstrap package metadata for team {team_id}",
                    "data": response.data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get bootstrap metadata for team {team_id}: {e}")
            # Check if it's a 404 (no bootstrap package)
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "message": f"No bootstrap package found for team {team_id}",
                    "data": None,
                }
            return {
                "success": False,
                "message": f"Failed to get bootstrap metadata: {error_msg}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_bootstrap_summary(
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Get aggregated summary about bootstrap package deployment.

        Returns statistics about bootstrap package deployment status across
        hosts, including counts of installed, pending, and failed installations.

        Args:
            team_id: Optional team ID to scope the summary (None for all teams)

        Returns:
            Dict containing bootstrap package deployment summary.
        """
        try:
            async with client:
                params = {}
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get(
                    "/api/latest/fleet/bootstrap/summary",
                    params=params if params else None,
                )
                return {
                    "success": True,
                    "message": "Retrieved bootstrap package summary",
                    "data": response.data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get bootstrap summary: {e}")
            return {
                "success": False,
                "message": f"Failed to get bootstrap summary: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_get_setup_assistant(
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Get the MDM Apple Setup Assistant configuration.

        Returns the Setup Assistant profile configured for automatic enrollment
        (DEP/ADE). The Setup Assistant customizes the out-of-box experience for
        devices enrolled via Apple Business Manager.

        Args:
            team_id: Optional team ID (None for no team/global)

        Returns:
            Dict containing Setup Assistant configuration.
        """
        try:
            async with client:
                params = {}
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get(
                    "/api/latest/fleet/enrollment_profiles/automatic",
                    params=params if params else None,
                )
                return {
                    "success": True,
                    "message": "Retrieved Setup Assistant configuration",
                    "data": response.data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to get Setup Assistant: {e}")
            # Check if it's a 404 (no setup assistant)
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "message": "No Setup Assistant configured",
                    "data": None,
                }
            return {
                "success": False,
                "message": f"Failed to get Setup Assistant: {error_msg}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_list_mdm_apple_installers(
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """List all Apple MDM installers.

        Args:
            team_id: Optional team ID to filter installers

        Returns:
            Dict containing list of Apple MDM installers.

        Example:
            >>> result = await fleet_list_mdm_apple_installers()
            >>> print(result["installers"])
        """
        try:
            async with client:
                params = {}
                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get("/mdm/apple/installers", params=params)

                if response.success and response.data:
                    installers = response.data.get("installers", [])
                    return {
                        "success": True,
                        "installers": installers,
                        "count": len(installers),
                        "message": f"Found {len(installers)} Apple MDM installers",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "installers": [],
                        "count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list Apple MDM installers: {e}")
            return {
                "success": False,
                "message": f"Failed to list Apple MDM installers: {str(e)}",
                "installers": [],
                "count": 0,
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

    @mcp.tool()
    async def fleet_upload_bootstrap_package(
        package_content: str,
        team_id: int,
    ) -> dict[str, Any]:
        """Upload a bootstrap package for MDM enrollment.

        Uploads a bootstrap package (.pkg file) that will be installed on
        devices during MDM enrollment. The package is deployed to devices
        enrolled via Apple Business Manager (DEP/ADE).

        Note: The package_content should be base64-encoded package data.
        Fleet expects multipart/form-data upload, but for MCP we accept
        base64-encoded content.

        Args:
            package_content: Base64-encoded bootstrap package (.pkg) content
            team_id: Team ID to assign the package to (0 for no team)

        Returns:
            Dict indicating success or failure of the upload.

        Example:
            >>> import base64
            >>> with open("bootstrap.pkg", "rb") as f:
            ...     pkg_data = base64.b64encode(f.read()).decode()
            >>> result = await fleet_upload_bootstrap_package(
            ...     package_content=pkg_data,
            ...     team_id=0
            ... )
            >>> print(result)
            {
                "success": True,
                "message": "Bootstrap package uploaded successfully for team 0",
                "data": None
            }
        """
        try:
            async with client:
                # Note: Fleet API expects multipart/form-data with a file upload.
                # For MCP, we'll need to send the base64 content as a file.
                import base64

                # Decode base64 content to validate it
                try:
                    base64.b64decode(package_content)
                except Exception as decode_err:
                    return {
                        "success": False,
                        "message": f"Invalid base64 content: {str(decode_err)}",
                        "data": None,
                    }

                # Fleet API expects multipart/form-data upload
                # Convert bytes to string for post_multipart
                files = {"package": ("bootstrap.pkg", package_content)}
                data = {"team_id": str(team_id)}

                response = await client.post_multipart(
                    "/api/latest/fleet/bootstrap",
                    files=files,
                    data=data,
                )
                return {
                    "success": True,
                    "message": f"Bootstrap package uploaded successfully for team {team_id}",
                    "data": response.data if hasattr(response, "data") else None,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to upload bootstrap package: {e}")
            return {
                "success": False,
                "message": f"Failed to upload bootstrap package: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_delete_bootstrap_package(
        team_id: int,
    ) -> dict[str, Any]:
        """Delete a bootstrap package for a team.

        Removes the bootstrap package configured for a team. This will prevent
        the package from being installed on newly enrolled devices.

        Args:
            team_id: Team ID to delete the bootstrap package from (0 for no team)

        Returns:
            Dict indicating success or failure of the deletion.
        """
        try:
            async with client:
                await client.delete(f"/api/latest/fleet/bootstrap/{team_id}")
                return {
                    "success": True,
                    "message": f"Bootstrap package deleted successfully for team {team_id}",
                    "data": None,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to delete bootstrap package for team {team_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete bootstrap package: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_create_setup_assistant(
        name: str,
        enrollment_profile: str,
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Create or update an MDM Apple Setup Assistant.

        Creates or updates the Setup Assistant profile for automatic enrollment
        (DEP/ADE). The Setup Assistant customizes the out-of-box experience for
        devices enrolled via Apple Business Manager.

        Args:
            name: Name for the Setup Assistant configuration
            enrollment_profile: JSON string containing the Setup Assistant profile
            team_id: Optional team ID (None for no team/global)

        Returns:
            Dict containing the created/updated Setup Assistant configuration.

        Example:
            >>> import json
            >>> profile = {
            ...     "skip_setup_items": {
            ...         "Location": True,
            ...         "Privacy": True,
            ...         "Restore": True,
            ...         "Appearance": False,
            ...         "Biometric": False
            ...     }
            ... }
            >>> result = await fleet_create_setup_assistant(
            ...     name="Corporate Setup",
            ...     enrollment_profile=json.dumps(profile),
            ...     team_id=None
            ... )
            >>> print(result)
            {
                "success": True,
                "message": "Setup Assistant created/updated successfully",
                "data": {
                    "name": "Corporate Setup",
                    "enrollment_profile": {...},
                    "team_id": None
                }
            }
        """
        try:
            async with client:
                import json

                # Parse enrollment_profile if it's a JSON string
                try:
                    profile_data = json.loads(enrollment_profile)
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "message": "Invalid JSON in enrollment_profile parameter",
                        "data": None,
                    }

                payload: dict[str, Any] = {
                    "name": name,
                    "enrollment_profile": profile_data,
                }
                if team_id is not None:
                    payload["team_id"] = team_id

                response = await client.post(
                    "/api/latest/fleet/enrollment_profiles/automatic",
                    json_data=payload,
                )
                return {
                    "success": True,
                    "message": "Setup Assistant created/updated successfully",
                    "data": response.data,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to create Setup Assistant: {e}")
            return {
                "success": False,
                "message": f"Failed to create Setup Assistant: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_delete_setup_assistant(
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Delete the MDM Apple Setup Assistant.

        Removes the Setup Assistant profile for automatic enrollment. This will
        revert to the default Apple setup experience for newly enrolled devices.

        Args:
            team_id: Optional team ID (None for no team/global)

        Returns:
            Dict indicating success or failure of the deletion.
        """
        try:
            async with client:
                # Build endpoint with query parameter if team_id is provided
                endpoint = "/api/latest/fleet/enrollment_profiles/automatic"
                if team_id is not None:
                    endpoint += f"?team_id={team_id}"

                await client.delete(endpoint)
                return {
                    "success": True,
                    "message": "Setup Assistant deleted successfully",
                    "data": None,
                }
        except FleetAPIError as e:
            logger.error(f"Failed to delete Setup Assistant: {e}")
            return {
                "success": False,
                "message": f"Failed to delete Setup Assistant: {str(e)}",
                "data": None,
            }

    @mcp.tool()
    async def fleet_upload_mdm_apple_installer(
        installer_filename: str,
        installer_content: str,
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Upload a new Apple MDM installer package.

        Args:
            installer_filename: Name of the installer file (e.g., "installer.pkg")
            installer_content: Content of the installer file (base64 or raw)
            team_id: Optional team ID to associate with the installer

        Returns:
            Dict containing the uploaded installer details.

        Example:
            >>> result = await fleet_upload_mdm_apple_installer(
            ...     installer_filename="installer.pkg",
            ...     installer_content="<file content>",
            ...     team_id=1
            ... )
            >>> print(result["installer"])
        """
        try:
            async with client:
                files = {"installer": (installer_filename, installer_content)}
                data = {}
                if team_id is not None:
                    data["team_id"] = str(team_id)

                response = await client.post_multipart(
                    "/mdm/apple/installers", files=files, data=data
                )

                if response.success and response.data:
                    installer = response.data.get("installer", {})
                    return {
                        "success": True,
                        "installer": installer,
                        "message": "Uploaded Apple MDM installer successfully",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "installer": {},
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to upload Apple MDM installer: {e}")
            return {
                "success": False,
                "message": f"Failed to upload Apple MDM installer: {str(e)}",
                "installer": {},
            }
