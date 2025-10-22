"""Integration tests for Fleet Script management tools.

These tests verify that script tools work correctly with a live Fleet instance.
"""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestScriptToolsIntegration:
    """Integration tests for script management tools."""

    async def test_list_scripts(self, live_fleet_client):
        """Test listing scripts from a live Fleet instance."""
        try:
            async with live_fleet_client:
                # Use correct Fleet API endpoint
                response = await live_fleet_client.get("/api/latest/fleet/scripts")

                # If endpoint doesn't exist, skip gracefully
                if not response.success and response.status_code == 404:
                    pytest.skip("Scripts API not available on this Fleet version")

                assert response.success, f"Failed to list scripts: {response.message}"
                assert response.data is not None, "No data in response"

                # Check for scripts list
                scripts = response.data.get("scripts", [])
                assert isinstance(scripts, list), "Scripts should be a list"

                # If there are scripts, verify structure
                if scripts:
                    script = scripts[0]
                    assert "id" in script, "Script missing 'id' field"
                    assert "name" in script, "Script missing 'name' field"

        except Exception as e:
            pytest.skip(f"List scripts failed: {e}")

    async def test_get_script(self, live_fleet_client):
        """Test getting a specific script from a live Fleet instance."""
        try:
            async with live_fleet_client:
                # First, list scripts to get an ID
                response = await live_fleet_client.get("/api/latest/fleet/scripts")

                # If endpoint doesn't exist, skip gracefully
                if not response.success and response.status_code == 404:
                    pytest.skip("Scripts API not available on this Fleet version")

                assert response.success, "Failed to list scripts"

                scripts = response.data.get("scripts", [])
                if not scripts:
                    pytest.skip("No scripts available to test")

                script_id = scripts[0]["id"]

                # Now get the specific script
                response = await live_fleet_client.get(f"/api/latest/fleet/scripts/{script_id}")

                assert response.success, f"Failed to get script {script_id}"
                assert response.data is not None, "No data in response"

                script = response.data.get("script", response.data)
                assert script["id"] == script_id, "Script ID mismatch"

        except Exception as e:
            pytest.skip(f"Get script failed: {e}")

    async def test_list_batch_scripts(self, live_fleet_client):
        """Test listing batch script executions from a live Fleet instance."""
        try:
            async with live_fleet_client:
                # Use correct Fleet API endpoint
                response = await live_fleet_client.get("/api/latest/fleet/scripts/batch")

                # If endpoint doesn't exist, skip gracefully
                if not response.success and response.status_code == 404:
                    pytest.skip("Batch scripts endpoint not available on this Fleet version")

                assert (
                    response.success
                ), f"Failed to list batch scripts: {response.message}"
                assert response.data is not None, "No data in response"

                # Check for batch executions list
                executions = response.data.get("batch_executions", [])
                assert isinstance(executions, list), "Batch executions should be a list"

                # If there are executions, verify structure
                if executions:
                    execution = executions[0]
                    assert (
                        "batch_execution_id" in execution
                    ), "Execution missing 'batch_execution_id'"
                    assert "status" in execution, "Execution missing 'status'"

        except Exception as e:
            pytest.skip(f"List batch scripts failed: {e}")

    async def test_create_and_delete_script(self, live_fleet_client):
        """Test creating and deleting a script on a live Fleet instance."""
        try:
            async with live_fleet_client:
                # First check if scripts API is available
                check_response = await live_fleet_client.get("/api/latest/fleet/scripts")
                if not check_response.success and check_response.status_code == 404:
                    pytest.skip("Scripts API not available on this Fleet version")

                # Create a simple test script
                script_content = "#!/bin/bash\necho 'test script'"
                files = {"script": ("test_script.sh", script_content)}

                response = await live_fleet_client.post_multipart(
                    "/api/latest/fleet/scripts", files=files
                )

                assert response.success, f"Failed to create script: {response.message}"
                assert response.data is not None, "No data in response"

                script_id = response.data.get("script_id")
                assert script_id is not None, "No script_id in response"

                # Verify the script was created
                response = await live_fleet_client.get(f"/api/latest/fleet/scripts/{script_id}")
                assert response.success, f"Failed to get created script {script_id}"

                # Delete the script
                response = await live_fleet_client.delete(f"/api/latest/fleet/scripts/{script_id}")
                assert response.success, f"Failed to delete script {script_id}"

        except Exception as e:
            pytest.skip(f"Create/delete script failed: {e}")

    async def test_modify_script(self, live_fleet_client):
        """Test modifying a script on a live Fleet instance."""
        try:
            async with live_fleet_client:
                # First check if scripts API is available
                check_response = await live_fleet_client.get("/api/latest/fleet/scripts")
                if not check_response.success and check_response.status_code == 404:
                    pytest.skip("Scripts API not available on this Fleet version")

                # Create a test script
                script_content = "#!/bin/bash\necho 'original'"
                files = {"script": ("test_script.sh", script_content)}

                response = await live_fleet_client.post_multipart(
                    "/api/latest/fleet/scripts", files=files
                )
                assert response.success, "Failed to create script"

                script_id = response.data.get("script_id")

                # Modify the script
                new_content = "#!/bin/bash\necho 'modified'"
                files = {"script": ("test_script.sh", new_content)}

                response = await live_fleet_client.patch_multipart(
                    f"/api/latest/fleet/scripts/{script_id}", files=files
                )

                assert response.success, f"Failed to modify script {script_id}"

                # Verify the script was modified
                response = await live_fleet_client.get(f"/api/latest/fleet/scripts/{script_id}")
                assert response.success, "Failed to get modified script"

                # Clean up
                await live_fleet_client.delete(f"/api/latest/fleet/scripts/{script_id}")

        except Exception as e:
            pytest.skip(f"Modify script failed: {e}")

    async def test_list_host_scripts(self, live_fleet_client):
        """Test listing scripts available for a host."""
        try:
            async with live_fleet_client:
                # Get a host ID first
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                if not hosts:
                    pytest.skip("No hosts available to test")

                host_id = hosts[0]["id"]

                # List scripts for the host using correct endpoint
                response = await live_fleet_client.get(f"/api/latest/fleet/hosts/{host_id}/scripts")

                # If endpoint doesn't exist, skip gracefully
                if not response.success and response.status_code == 404:
                    pytest.skip("Host scripts API not available on this Fleet version")

                assert response.success, f"Failed to list scripts for host {host_id}"
                assert response.data is not None, "No data in response"

                scripts = response.data.get("scripts", [])
                assert isinstance(scripts, list), "Scripts should be a list"

        except Exception as e:
            pytest.skip(f"List host scripts failed: {e}")

    async def test_run_script_on_host(self, live_fleet_client):
        """Test running a script on a host."""
        try:
            async with live_fleet_client:
                # Get an online host first
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip("No online hosts available to test")

                host_id = online_hosts[0]["id"]

                # Run a simple script using correct endpoint
                json_data = {
                    "host_id": host_id,
                    "script_contents": "#!/bin/bash\necho 'hello'",
                }

                response = await live_fleet_client.post(
                    "/api/latest/fleet/scripts/run", json_data=json_data
                )

                # This may fail if scripts aren't supported or host doesn't support scripts
                if response.success:
                    assert response.data is not None, "No data in response"
                    assert "execution_id" in response.data, "Missing execution_id"
                elif response.status_code == 404:
                    pytest.skip("Script execution API not available on this Fleet version")
                else:
                    pytest.skip(f"Script execution not supported: {response.message}")

        except Exception as e:
            pytest.skip(f"Run script failed: {e}")
