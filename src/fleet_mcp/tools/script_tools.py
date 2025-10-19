"""Script management tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetAPIError, FleetClient, FleetValidationError

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all script management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)
    register_write_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only script management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_scripts(
        team_id: int | None = None,
        page: int = 0,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """List all scripts available in Fleet.

        Args:
            team_id: Filter scripts by team ID (Premium feature)
            page: Page number for pagination (0-based)
            per_page: Number of scripts per page

        Returns:
            Dict containing list of scripts and pagination metadata.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": min(per_page, 500),
                }

                if team_id is not None:
                    params["team_id"] = team_id

                response = await client.get("/api/v1/fleet/scripts", params=params)

                if response.success and response.data:
                    scripts = response.data.get("scripts", [])
                    return {
                        "success": True,
                        "scripts": scripts,
                        "count": len(scripts),
                        "message": f"Found {len(scripts)} scripts",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "scripts": [],
                        "count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list scripts: {e}")
            return {
                "success": False,
                "message": f"Failed to list scripts: {str(e)}",
                "scripts": [],
                "count": 0,
            }

    @mcp.tool()
    async def fleet_get_script(script_id: int) -> dict[str, Any]:
        """Get details of a specific script.

        Args:
            script_id: ID of the script to retrieve

        Returns:
            Dict containing script details.
        """
        try:
            async with client:
                response = await client.get(f"/api/v1/fleet/scripts/{script_id}")

                if response.success and response.data:
                    script = response.data.get("script", response.data)
                    return {
                        "success": True,
                        "script": script,
                        "message": f"Retrieved script {script_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "script": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get script {script_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get script: {str(e)}",
                "script": None,
            }

    @mcp.tool()
    async def fleet_get_script_result(execution_id: str) -> dict[str, Any]:
        """Get the result of a script execution.

        Args:
            execution_id: The execution ID of the script run

        Returns:
            Dict containing script execution result.
        """
        try:
            async with client:
                response = await client.get(f"/api/v1/fleet/scripts/results/{execution_id}")

                if response.success and response.data:
                    result = response.data
                    return {
                        "success": True,
                        "result": result,
                        "message": f"Retrieved script result for execution {execution_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "result": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get script result {execution_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get script result: {str(e)}",
                "result": None,
            }

    @mcp.tool()
    async def fleet_list_batch_scripts(
        team_id: int | None = None,
        status: str | None = None,
        page: int = 0,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """List batch script executions.

        Args:
            team_id: Filter by team ID (Premium feature)
            status: Filter by status (started, scheduled, finished)
            page: Page number for pagination (0-based)
            per_page: Number of results per page

        Returns:
            Dict containing list of batch script executions.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": min(per_page, 500),
                }

                if team_id is not None:
                    params["team_id"] = team_id
                if status:
                    params["status"] = status

                response = await client.get("/api/v1/fleet/scripts/batch", params=params)

                if response.success and response.data:
                    executions = response.data.get("batch_executions", [])
                    return {
                        "success": True,
                        "batch_executions": executions,
                        "count": len(executions),
                        "message": f"Found {len(executions)} batch script executions",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "batch_executions": [],
                        "count": 0,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list batch scripts: {e}")
            return {
                "success": False,
                "message": f"Failed to list batch scripts: {str(e)}",
                "batch_executions": [],
                "count": 0,
            }

    @mcp.tool()
    async def fleet_get_batch_script(batch_execution_id: str) -> dict[str, Any]:
        """Get details of a batch script execution.

        Args:
            batch_execution_id: The batch execution ID

        Returns:
            Dict containing batch script execution details.
        """
        try:
            async with client:
                response = await client.get(f"/api/v1/fleet/scripts/batch/{batch_execution_id}")

                if response.success and response.data:
                    batch = response.data
                    return {
                        "success": True,
                        "batch": batch,
                        "message": f"Retrieved batch script {batch_execution_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "batch": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to get batch script {batch_execution_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get batch script: {str(e)}",
                "batch": None,
            }

    @mcp.tool()
    async def fleet_list_batch_script_hosts(
        batch_execution_id: str,
        status: str | None = None,
        page: int = 0,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """List hosts targeted in a batch script execution.

        Args:
            batch_execution_id: The batch execution ID
            status: Filter by host status (ran, pending, errored, incompatible, canceled)
            page: Page number for pagination (0-based)
            per_page: Number of results per page

        Returns:
            Dict containing list of hosts and their script execution status.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": min(per_page, 500),
                }

                if status:
                    params["status"] = status

                response = await client.get(
                    f"/api/v1/fleet/scripts/batch/{batch_execution_id}/host-results",
                    params=params,
                )

                if response.success and response.data:
                    hosts = response.data.get("hosts", [])
                    return {
                        "success": True,
                        "hosts": hosts,
                        "count": len(hosts),
                        "message": f"Found {len(hosts)} hosts in batch script",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "hosts": [],
                        "count": 0,
                    }

        except FleetAPIError as e:
            logger.error(
                f"Failed to list batch script hosts {batch_execution_id}: {e}"
            )
            return {
                "success": False,
                "message": f"Failed to list batch script hosts: {str(e)}",
                "hosts": [],
                "count": 0,
            }

    @mcp.tool()
    async def fleet_list_host_scripts(
        host_id: int,
        page: int = 0,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """List scripts available for a specific host.

        Args:
            host_id: ID of the host
            page: Page number for pagination (0-based)
            per_page: Number of results per page

        Returns:
            Dict containing list of scripts available for the host.
        """
        try:
            async with client:
                params = {
                    "page": page,
                    "per_page": min(per_page, 500),
                }

                response = await client.get(f"/hosts/{host_id}/scripts", params=params)

                if response.success and response.data:
                    scripts = response.data.get("scripts", [])
                    return {
                        "success": True,
                        "scripts": scripts,
                        "count": len(scripts),
                        "host_id": host_id,
                        "message": f"Found {len(scripts)} scripts for host {host_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "scripts": [],
                        "count": 0,
                        "host_id": host_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to list host scripts for host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to list host scripts: {str(e)}",
                "scripts": [],
                "count": 0,
                "host_id": host_id,
            }


def register_write_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register write script management tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_run_script(
        host_id: int,
        script_id: int | None = None,
        script_contents: str | None = None,
        script_name: str | None = None,
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Run a script on a specific host.

        Only one of script_id, script_contents, or script_name should be provided.

        Args:
            host_id: ID of the host to run the script on
            script_id: ID of an existing saved script
            script_contents: Contents of the script to run (max 10,000 characters)
            script_name: Name of an existing saved script (requires team_id)
            team_id: Team ID (required if using script_name)

        Returns:
            Dict containing execution ID and host ID.
        """
        try:
            async with client:
                json_data = {"host_id": host_id}

                # Validate only one script source is provided
                provided_count = sum(
                    [
                        script_id is not None,
                        script_contents is not None,
                        script_name is not None,
                    ]
                )
                if provided_count != 1:
                    return {
                        "success": False,
                        "message": "Exactly one of script_id, script_contents, or script_name must be provided",
                        "host_id": host_id,
                        "execution_id": None,
                    }

                if script_id is not None:
                    json_data["script_id"] = script_id
                elif script_contents is not None:
                    if len(script_contents) > 10000:
                        return {
                            "success": False,
                            "message": "Script contents must be less than 10,000 characters",
                            "host_id": host_id,
                            "execution_id": None,
                        }
                    json_data["script_contents"] = script_contents
                elif script_name is not None:
                    if team_id is None:
                        return {
                            "success": False,
                            "message": "team_id is required when using script_name",
                            "host_id": host_id,
                            "execution_id": None,
                        }
                    json_data["script_name"] = script_name
                    json_data["team_id"] = team_id

                response = await client.post("/api/v1/fleet/scripts/run", json_data=json_data)

                if response.success and response.data:
                    return {
                        "success": True,
                        "host_id": response.data.get("host_id"),
                        "execution_id": response.data.get("execution_id"),
                        "message": f"Script execution started on host {host_id}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "host_id": host_id,
                        "execution_id": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to run script on host {host_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to run script: {str(e)}",
                "host_id": host_id,
                "execution_id": None,
            }

    @mcp.tool()
    async def fleet_run_batch_script(
        script_id: int,
        host_ids: list[int] | None = None,
        filters: dict[str, Any] | None = None,
        not_before: str | None = None,
    ) -> dict[str, Any]:
        """Run a script on multiple hosts in a batch.

        Either host_ids or filters must be provided, but not both.

        Args:
            script_id: ID of the saved script to run
            host_ids: List of host IDs to target
            filters: Filter object with query, status, label_id, team_id
            not_before: UTC time when batch should start (ISO 8601 format)

        Returns:
            Dict containing batch execution ID.
        """
        try:
            async with client:
                json_data = {"script_id": script_id}

                # Validate either host_ids or filters is provided
                if (host_ids is None and filters is None) or (
                    host_ids is not None and filters is not None
                ):
                    return {
                        "success": False,
                        "message": "Exactly one of host_ids or filters must be provided",
                        "batch_execution_id": None,
                    }

                if host_ids is not None:
                    json_data["host_ids"] = host_ids
                else:
                    json_data["filters"] = filters

                if not_before:
                    json_data["not_before"] = not_before

                response = await client.post("/api/v1/fleet/scripts/run/batch", json_data=json_data)

                if response.success and response.data:
                    return {
                        "success": True,
                        "batch_execution_id": response.data.get("batch_execution_id"),
                        "message": f"Batch script execution started",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "batch_execution_id": None,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to run batch script: {e}")
            return {
                "success": False,
                "message": f"Failed to run batch script: {str(e)}",
                "batch_execution_id": None,
            }

    @mcp.tool()
    async def fleet_cancel_batch_script(batch_execution_id: str) -> dict[str, Any]:
        """Cancel a batch script execution.

        Args:
            batch_execution_id: The batch execution ID to cancel

        Returns:
            Dict indicating success or failure.
        """
        try:
            async with client:
                response = await client.post(
                    f"/scripts/batch/{batch_execution_id}/cancel"
                )

                if response.success:
                    return {
                        "success": True,
                        "batch_execution_id": batch_execution_id,
                        "message": f"Batch script {batch_execution_id} canceled",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "batch_execution_id": batch_execution_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to cancel batch script {batch_execution_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to cancel batch script: {str(e)}",
                "batch_execution_id": batch_execution_id,
            }

    @mcp.tool()
    async def fleet_create_script(
        script_name: str,
        script_contents: str,
        team_id: int | None = None,
    ) -> dict[str, Any]:
        """Create and upload a new script.

        Args:
            script_name: Name of the script (e.g., 'my_script.sh' or 'deploy.ps1').
                        The file extension determines the script type:
                        - .sh files MUST have a shebang line (e.g., #!/bin/bash)
                        - .ps1 files can be uploaded as-is
            script_contents: The contents of the script
            team_id: Team ID to associate the script with (Premium feature)

        Returns:
            Dict containing the created script ID and status.

        Raises:
            ValueError: If .sh script is missing a shebang line
        """
        try:
            # Validate script based on file extension
            file_ext = script_name.lower().split('.')[-1] if '.' in script_name else ''

            if file_ext == 'sh':
                # Validate that .sh scripts have a shebang
                if not script_contents.strip().startswith('#!'):
                    return {
                        "success": False,
                        "message": "Shell scripts (.sh) must start with a shebang line (e.g., #!/bin/bash)",
                        "script_id": None,
                    }
            elif file_ext == 'ps1':
                # PowerShell scripts don't require shebang, upload as-is
                pass
            # Other file types are allowed without specific validation

            async with client:
                # For file uploads, we need to use multipart form data
                files = {"script": (script_name, script_contents)}
                data = {}
                if team_id is not None:
                    # Pass team_id as integer, not string
                    data["team_id"] = team_id

                response = await client.post_multipart("/api/v1/fleet/scripts", files=files, data=data)

                if response.success and response.data:
                    return {
                        "success": True,
                        "script_id": response.data.get("script_id"),
                        "script_name": script_name,
                        "message": f"Script '{script_name}' created with ID {response.data.get('script_id')}",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "script_id": None,
                    }

        except FleetValidationError as e:
            logger.error(f"Failed to create script - validation error: {e}")
            logger.error(f"Response data: {e.response_data}")
            return {
                "success": False,
                "message": f"Failed to create script: {str(e)}",
                "script_id": None,
            }
        except FleetAPIError as e:
            logger.error(f"Failed to create script: {e}")
            return {
                "success": False,
                "message": f"Failed to create script: {str(e)}",
                "script_id": None,
            }

    @mcp.tool()
    async def fleet_modify_script(
        script_id: int,
        script_contents: str,
        script_name: str | None = None,
    ) -> dict[str, Any]:
        """Modify an existing script.

        Args:
            script_id: ID of the script to modify
            script_contents: New contents of the script
            script_name: Optional name of the script to validate file type.
                        If provided, the file extension determines validation:
                        - .sh files MUST have a shebang line (e.g., #!/bin/bash)
                        - .ps1 files can be uploaded as-is

        Returns:
            Dict containing updated script information.

        Raises:
            ValueError: If .sh script is missing a shebang line
        """
        try:
            # Validate script based on file extension if script_name is provided
            if script_name:
                file_ext = script_name.lower().split('.')[-1] if '.' in script_name else ''

                if file_ext == 'sh':
                    # Validate that .sh scripts have a shebang
                    if not script_contents.strip().startswith('#!'):
                        return {
                            "success": False,
                            "message": "Shell scripts (.sh) must start with a shebang line (e.g., #!/bin/bash)",
                            "script": None,
                        }

            async with client:
                files = {"script": ("script", script_contents)}

                response = await client.patch_multipart(
                    f"/api/v1/fleet/scripts/{script_id}", files=files
                )

                if response.success and response.data:
                    script = response.data.get("script", response.data)
                    return {
                        "success": True,
                        "script": script,
                        "message": f"Script {script_id} modified successfully",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "script": None,
                    }

        except FleetValidationError as e:
            logger.error(f"Failed to modify script {script_id} - validation error: {e}")
            logger.error(f"Response data: {e.response_data}")
            return {
                "success": False,
                "message": f"Failed to modify script: {str(e)}",
                "script": None,
            }
        except FleetAPIError as e:
            logger.error(f"Failed to modify script {script_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to modify script: {str(e)}",
                "script": None,
            }

    @mcp.tool()
    async def fleet_delete_script(script_id: int) -> dict[str, Any]:
        """Delete a script.

        Args:
            script_id: ID of the script to delete

        Returns:
            Dict indicating success or failure.
        """
        try:
            async with client:
                response = await client.delete(f"/api/v1/fleet/scripts/{script_id}")

                if response.success:
                    return {
                        "success": True,
                        "script_id": script_id,
                        "message": f"Script {script_id} deleted successfully",
                    }
                else:
                    return {
                        "success": False,
                        "message": response.message,
                        "script_id": script_id,
                    }

        except FleetAPIError as e:
            logger.error(f"Failed to delete script {script_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete script: {str(e)}",
                "script_id": script_id,
            }

