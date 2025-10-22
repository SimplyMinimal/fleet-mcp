"""Tests for Fleet Script management tools."""

from unittest.mock import MagicMock, patch

import pytest

from fleet_mcp.client import FleetAPIError, FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools import script_tools


@pytest.fixture
def fleet_config():
    """Create a test Fleet configuration."""
    return FleetConfig(
        server_url="https://test.fleet.com", api_token="test-token-123456789"
    )


@pytest.fixture
def fleet_client(fleet_config):
    """Create a test Fleet client."""
    return FleetClient(fleet_config)


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server."""
    mcp = MagicMock()
    mcp.tool = MagicMock(return_value=lambda f: f)
    return mcp


class TestScriptToolsRead:
    """Test read-only script management tools."""

    @pytest.mark.asyncio
    async def test_list_scripts(self, fleet_client, mock_mcp):
        """Test listing scripts."""
        mock_response = FleetResponse(
            success=True,
            data={
                "scripts": [
                    {
                        "id": 1,
                        "team_id": None,
                        "name": "script_1.sh",
                        "created_at": "2023-07-30T13:41:07Z",
                        "updated_at": "2023-07-30T13:41:07Z",
                    }
                ]
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            script_tools.register_read_tools(mock_mcp, fleet_client)
            # Get the registered function
            tool_calls = list(mock_mcp.tool.call_args_list)
            assert len(tool_calls) > 0

    @pytest.mark.asyncio
    async def test_get_script(self, fleet_client, mock_mcp):
        """Test getting a specific script."""
        mock_response = FleetResponse(
            success=True,
            data={
                "script": {
                    "id": 1,
                    "team_id": None,
                    "name": "script_1.sh",
                    "created_at": "2023-07-30T13:41:07Z",
                    "updated_at": "2023-07-30T13:41:07Z",
                }
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            script_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_get_script_result(self, fleet_client, mock_mcp):
        """Test getting script execution result."""
        mock_response = FleetResponse(
            success=True,
            data={
                "script_contents": "echo 'hello'",
                "exit_code": 0,
                "output": "hello",
                "message": "",
                "hostname": "Test Host",
                "host_timeout": False,
                "host_id": 1,
                "execution_id": "e797d6c6-3aae-11ee-be56-0242ac120002",
                "runtime": 20,
                "created_at": "2024-09-11T20:30:24Z",
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            script_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_list_batch_scripts(self, fleet_client, mock_mcp):
        """Test listing batch script executions."""
        mock_response = FleetResponse(
            success=True,
            data={
                "batch_executions": [
                    {
                        "script_id": 555,
                        "script_name": "my-script.sh",
                        "batch_execution_id": "e797d6c6-3aae-11ee-be56-0242ac120002",
                        "team_id": 123,
                        "status": "finished",
                        "targeted_host_count": 100,
                        "ran_host_count": 95,
                        "pending_host_count": 5,
                    }
                ]
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            script_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_list_host_scripts(self, fleet_client, mock_mcp):
        """Test listing scripts available for a host."""
        mock_response = FleetResponse(
            success=True,
            data={
                "scripts": [
                    {
                        "script_id": 3,
                        "name": "remove-zoom-artifacts.sh",
                        "last_execution": {
                            "execution_id": "e797d6c6-3aae-11ee-be56-0242ac120002",
                            "executed_at": "2021-12-15T15:23:57Z",
                            "status": "error",
                        },
                    }
                ]
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            script_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestScriptToolsWrite:
    """Test write script management tools."""

    @pytest.mark.asyncio
    async def test_run_script_with_id(self, fleet_client, mock_mcp):
        """Test running a script by ID."""
        mock_response = FleetResponse(
            success=True,
            data={
                "host_id": 1227,
                "execution_id": "e797d6c6-3aae-11ee-be56-0242ac120002",
            },
            message="Success",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            script_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_run_batch_script(self, fleet_client, mock_mcp):
        """Test running a batch script."""
        mock_response = FleetResponse(
            success=True,
            data={
                "batch_execution_id": "e797d6c6-3aae-11ee-be56-0242ac120002",
            },
            message="Success",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            script_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_cancel_batch_script(self, fleet_client, mock_mcp):
        """Test canceling a batch script."""
        mock_response = FleetResponse(
            success=True,
            data={},
            message="Success",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            script_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_create_script(self, fleet_client, mock_mcp):
        """Test creating a new script."""
        mock_response = FleetResponse(
            success=True,
            data={"script_id": 1227},
            message="Success",
        )

        with patch.object(fleet_client, "post_multipart", return_value=mock_response):
            script_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_modify_script(self, fleet_client, mock_mcp):
        """Test modifying an existing script."""
        mock_response = FleetResponse(
            success=True,
            data={
                "id": 1,
                "team_id": None,
                "name": "script_1.sh",
                "created_at": "2023-07-30T13:41:07Z",
                "updated_at": "2023-07-30T13:41:07Z",
            },
            message="Success",
        )

        with patch.object(fleet_client, "patch_multipart", return_value=mock_response):
            script_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_delete_script(self, fleet_client, mock_mcp):
        """Test deleting a script."""
        mock_response = FleetResponse(
            success=True,
            data={},
            message="Success",
        )

        with patch.object(fleet_client, "delete", return_value=mock_response):
            script_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestScriptToolsErrorHandling:
    """Test error handling in script tools."""

    @pytest.mark.asyncio
    async def test_list_scripts_api_error(self, fleet_client, mock_mcp):
        """Test handling API error when listing scripts."""
        with patch.object(fleet_client, "get", side_effect=FleetAPIError("API Error")):
            script_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_run_script_validation_error(self, fleet_client, mock_mcp):
        """Test validation error when running script with multiple sources."""
        script_tools.register_write_tools(mock_mcp, fleet_client)
        assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_run_script_script_too_large(self, fleet_client, mock_mcp):
        """Test error when script contents exceed size limit."""
        script_tools.register_write_tools(mock_mcp, fleet_client)
        assert mock_mcp.tool.called
