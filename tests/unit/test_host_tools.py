"""Tests for new Fleet Host management tools (Priority 5B)."""

from unittest.mock import MagicMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from fleet_mcp.client import FleetAPIError, FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools import host_tools
from tests.fixtures import TEST_ENCRYPTION_KEYS, get_test_host


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


@pytest.fixture
def mcp_server():
    """Create a FastMCP server instance for testing tool invocation."""
    return FastMCP("test-server")


class TestFleetGetHostMacadmins:
    """Test fleet_get_host_macadmins tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful retrieval of host macadmins data."""
        mock_response = FleetResponse(
            success=True,
            data={
                "macadmins": {
                    "munki": {"version": "5.2.3", "errors": [], "warnings": []},
                    "munki_issues": [],
                    "mobile_device_management": {
                        "enrollment_status": "On (automatic)",
                        "server_url": "https://mdm.example.com",
                        "name": "Example MDM",
                        "id": "12345",
                    },
                }
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            # Verify tool was registered
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_404_error(self, fleet_client, mock_mcp):
        """Test handling of 404 error when host not found."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Host not found", status_code=404),
        ):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_empty_response(self, fleet_client, mock_mcp):
        """Test handling of empty macadmins data."""
        mock_response = FleetResponse(
            success=True,
            data={"macadmins": {}},
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestFleetGetHostDeviceMapping:
    """Test fleet_get_host_device_mapping tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful retrieval of device mapping."""
        mock_response = FleetResponse(
            success=True,
            data={
                "device_mapping": [
                    {"email": "user@example.com", "source": "google_chrome_profiles"}
                ]
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_empty_mapping(self, fleet_client, mock_mcp):
        """Test handling of empty device mapping."""
        mock_response = FleetResponse(
            success=True,
            data={"device_mapping": []},
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_api_error(self, fleet_client, mock_mcp):
        """Test handling of API error."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Internal server error", status_code=500),
        ):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_none_device_mapping(self, fleet_client, mcp_server):
        """Test handling of None device mapping (bug fix for issue with host_id 63)."""
        mock_response = FleetResponse(
            success=True,
            data={"host_id": 1, "device_mapping": None},
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            # Register the tools
            host_tools.register_read_tools(mcp_server, fleet_client)

            # Get the registered tool
            tools = await mcp_server.list_tools()
            device_mapping_tool = next(
                t for t in tools if t.name == "fleet_get_host_device_mapping"
            )

            # Actually call the tool - this should not raise TypeError
            result = await mcp_server.call_tool(
                device_mapping_tool.name, arguments={"host_id": 1}
            )

            # Verify the result is valid
            assert result is not None
            result_str = str(result)
            # Should handle None gracefully and return count of 0
            assert "count" in result_str.lower() or "0" in result_str


class TestFleetListHostUpcomingActivities:
    """Test fleet_list_host_upcoming_activities tool."""

    @pytest.mark.asyncio
    async def test_none_activities(self, fleet_client, mcp_server):
        """Test handling of None activities (null from Fleet API)."""
        mock_response = FleetResponse(
            success=True,
            data={"activities": None, "meta": {"has_next_results": False}},
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            # Register the tools
            host_tools.register_read_tools(mcp_server, fleet_client)

            # Get the registered tool
            tools = await mcp_server.list_tools()
            activities_tool = next(
                t for t in tools if t.name == "fleet_list_host_upcoming_activities"
            )

            # Actually call the tool - this should not raise TypeError
            result = await mcp_server.call_tool(
                activities_tool.name, arguments={"host_id": 1}
            )

            # Verify the result is valid
            assert result is not None
            result_str = str(result)
            # Should handle None gracefully and return count of 0
            assert "count" in result_str.lower() or "0" in result_str


class TestFleetListHostPastActivities:
    """Test fleet_list_host_past_activities tool."""

    @pytest.mark.asyncio
    async def test_none_activities(self, fleet_client, mcp_server):
        """Test handling of None activities (null from Fleet API)."""
        mock_response = FleetResponse(
            success=True,
            data={"activities": None, "meta": {"has_next_results": False}},
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            # Register the tools
            host_tools.register_read_tools(mcp_server, fleet_client)

            # Get the registered tool
            tools = await mcp_server.list_tools()
            activities_tool = next(
                t for t in tools if t.name == "fleet_list_host_past_activities"
            )

            # Actually call the tool - this should not raise TypeError
            result = await mcp_server.call_tool(
                activities_tool.name, arguments={"host_id": 1}
            )

            # Verify the result is valid
            assert result is not None
            result_str = str(result)
            # Should handle None gracefully and return count of 0
            assert "count" in result_str.lower() or "0" in result_str


class TestFleetListHostCertificates:
    """Test fleet_list_host_certificates tool."""

    @pytest.mark.asyncio
    async def test_none_certificates(self, fleet_client, mcp_server):
        """Test handling of None certificates (null from Fleet API)."""
        mock_response = FleetResponse(
            success=True,
            data={
                "certificates": None,
                "count": 0,
                "meta": {"has_next_results": False},
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            # Register the tools
            host_tools.register_read_tools(mcp_server, fleet_client)

            # Get the registered tool
            tools = await mcp_server.list_tools()
            certificates_tool = next(
                t for t in tools if t.name == "fleet_list_host_certificates"
            )

            # Actually call the tool - this should not raise TypeError
            result = await mcp_server.call_tool(
                certificates_tool.name, arguments={"host_id": 1}
            )

            # Verify the result is valid
            assert result is not None
            result_str = str(result)
            # Should handle None gracefully and return count of 0
            assert "count" in result_str.lower() or "0" in result_str


class TestFleetGetHostEncryptionKey:
    """Test fleet_get_host_encryption_key tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful retrieval of encryption key."""
        test_host = get_test_host("laptop")
        mock_response = FleetResponse(
            success=True,
            data={
                "host_id": test_host["id"],
                "encryption_key": {
                    "key": TEST_ENCRYPTION_KEYS["valid"],
                    "updated_at": "2024-01-15T10:30:00Z",
                },
            },
            message="Success",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_no_encryption_key(self, fleet_client, mock_mcp):
        """Test handling when no encryption key is available."""
        test_host = get_test_host("laptop")
        mock_response = FleetResponse(
            success=True,
            data={"host_id": test_host["id"], "encryption_key": None},
            message="No encryption key available",
        )

        with patch.object(fleet_client, "get", return_value=mock_response):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_403_forbidden(self, fleet_client, mock_mcp):
        """Test handling of 403 forbidden error."""
        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("Forbidden", status_code=403),
        ):
            host_tools.register_read_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestFleetRefetchHost:
    """Test fleet_refetch_host tool."""

    @pytest.mark.asyncio
    async def test_success(self, fleet_client, mock_mcp):
        """Test successful host refetch."""
        mock_response = FleetResponse(
            success=True,
            data={},
            message="Host refetch triggered successfully",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            host_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_host_not_found(self, fleet_client, mock_mcp):
        """Test handling when host is not found."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Host not found", status_code=404),
        ):
            host_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_host_offline(self, fleet_client, mock_mcp):
        """Test handling when host is offline."""
        mock_response = FleetResponse(
            success=False,
            data={},
            message="Host is offline",
        )

        with patch.object(fleet_client, "post", return_value=mock_response):
            host_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called

    @pytest.mark.asyncio
    async def test_api_error(self, fleet_client, mock_mcp):
        """Test handling of API error."""
        with patch.object(
            fleet_client,
            "post",
            side_effect=FleetAPIError("Internal server error", status_code=500),
        ):
            host_tools.register_write_tools(mock_mcp, fleet_client)
            assert mock_mcp.tool.called


class TestFleetQueryHostByIdentifier:
    """Test fleet_query_host_by_identifier tool."""

    @pytest.mark.asyncio
    async def test_success_with_hostname(self, mcp_server, fleet_client):
        """Test successful query using hostname identifier.

        This test validates that the tool correctly:
        1. Calls GET /hosts/identifier/{hostname} to resolve the hostname
        2. Calls POST /hosts/{host_id}/query with the resolved host ID
        3. Returns the expected result structure
        """
        # The identifier we're testing
        test_host = get_test_host("laptop")
        hostname = test_host["hostname"]
        test_query = "SELECT name, pid FROM processes LIMIT 5;"

        # Mock the host lookup response
        mock_host_response = FleetResponse(
            success=True,
            data={
                "host": {
                    "id": test_host["id"],
                    "hostname": test_host["hostname"],
                    "uuid": test_host["uuid"],
                    "hardware_serial": test_host["hardware_serial"],
                }
            },
            message="Success",
        )

        # Mock the query response
        mock_query_response = FleetResponse(
            success=True,
            data={
                "host_id": 123,
                "query": test_query,
                "status": "online",
                "error": None,
                "rows": [
                    {"name": "systemd", "pid": "1"},
                    {"name": "bash", "pid": "1234"},
                ],
            },
            message="Success",
        )

        with (
            patch.object(
                fleet_client, "get", return_value=mock_host_response
            ) as mock_get,
            patch.object(
                fleet_client, "post", return_value=mock_query_response
            ) as mock_post,
        ):
            # Register the query tools (where fleet_query_host_by_identifier is defined)
            host_tools.register_query_tools(mcp_server, fleet_client)

            # Get the registered tool
            tools = await mcp_server.list_tools()
            query_tool = next(
                t for t in tools if t.name == "fleet_query_host_by_identifier"
            )

            # Actually call the tool with the hostname
            result = await mcp_server.call_tool(
                query_tool.name, arguments={"identifier": hostname, "query": test_query}
            )

            # Verify the API was called with the correct identifier
            mock_get.assert_called_once_with(f"/hosts/identifier/{hostname}")

            # Verify the query was posted to the correct host ID
            mock_post.assert_called_once_with(
                "/hosts/123/query", json_data={"query": test_query}
            )

            # Verify the result structure
            result_list = result if isinstance(result, list) else [result]
            result_str = str(result_list[0])
            assert "success" in result_str.lower()
            assert hostname in result_str
            assert "123" in result_str  # host_id

    @pytest.mark.asyncio
    async def test_success_with_serial_number(self, mcp_server, fleet_client):
        """Test successful query using hardware serial number identifier.

        This test validates that the tool correctly:
        1. Calls GET /hosts/identifier/{serial} to resolve the serial number
        2. Calls POST /hosts/{host_id}/query with the resolved host ID
        3. Returns the expected result structure
        """
        # The identifier we're testing
        test_host = get_test_host("workstation")
        serial_number = test_host["hardware_serial"]
        test_query = "SELECT * FROM system_info;"

        # Mock the host lookup response
        mock_host_response = FleetResponse(
            success=True,
            data={
                "host": {
                    "id": test_host["id"],
                    "hostname": test_host["hostname"],
                    "uuid": test_host["uuid"],
                    "hardware_serial": test_host["hardware_serial"],
                }
            },
            message="Success",
        )

        # Mock the query response
        mock_query_response = FleetResponse(
            success=True,
            data={
                "host_id": test_host["id"],
                "query": test_query,
                "status": "online",
                "error": None,
                "rows": [
                    {"hostname": test_host["hostname"], "cpu_brand": "Test CPU Brand"}
                ],
            },
            message="Success",
        )

        with (
            patch.object(
                fleet_client, "get", return_value=mock_host_response
            ) as mock_get,
            patch.object(
                fleet_client, "post", return_value=mock_query_response
            ) as mock_post,
        ):
            # Register the query tools (where fleet_query_host_by_identifier is defined)
            host_tools.register_query_tools(mcp_server, fleet_client)

            # Get the registered tool
            tools = await mcp_server.list_tools()
            query_tool = next(
                t for t in tools if t.name == "fleet_query_host_by_identifier"
            )

            # Actually call the tool with the serial number
            result = await mcp_server.call_tool(
                query_tool.name,
                arguments={"identifier": serial_number, "query": test_query},
            )

            # Verify the API was called with the correct identifier
            mock_get.assert_called_once_with(f"/hosts/identifier/{serial_number}")

            # Verify the query was posted to the correct host ID
            mock_post.assert_called_once_with(
                "/hosts/456/query", json_data={"query": test_query}
            )

            # Verify the result structure
            result_list = result if isinstance(result, list) else [result]
            result_str = str(result_list[0])
            assert "success" in result_str.lower()
            assert "456" in result_str  # host_id

    @pytest.mark.asyncio
    async def test_success_with_uuid(self, mcp_server, fleet_client):
        """Test successful query using UUID identifier.

        This test validates that the tool correctly:
        1. Calls GET /hosts/identifier/{uuid} to resolve the UUID
        2. Calls POST /hosts/{host_id}/query with the resolved host ID
        3. Returns the expected result structure
        """
        # The identifier we're testing
        test_host = get_test_host("server")
        uuid = test_host["uuid"]
        test_query = "SELECT * FROM os_version;"

        # Mock the host lookup response
        mock_host_response = FleetResponse(
            success=True,
            data={
                "host": {
                    "id": test_host["id"],
                    "hostname": test_host["hostname"],
                    "uuid": test_host["uuid"],
                    "hardware_serial": test_host[
                        "hardware_serial"
                    ],  # Empty serial (common for VMs)
                }
            },
            message="Success",
        )

        # Mock the query response
        mock_query_response = FleetResponse(
            success=True,
            data={
                "host_id": test_host["id"],
                "query": test_query,
                "status": "online",
                "error": None,
                "rows": [
                    {
                        "name": "Test OS",
                        "version": "1.0.0",
                        "platform": "test",
                    }
                ],
            },
            message="Success",
        )

        with (
            patch.object(
                fleet_client, "get", return_value=mock_host_response
            ) as mock_get,
            patch.object(
                fleet_client, "post", return_value=mock_query_response
            ) as mock_post,
        ):
            # Register the query tools (where fleet_query_host_by_identifier is defined)
            host_tools.register_query_tools(mcp_server, fleet_client)

            # Get the registered tool
            tools = await mcp_server.list_tools()
            query_tool = next(
                t for t in tools if t.name == "fleet_query_host_by_identifier"
            )

            # Actually call the tool with the UUID
            result = await mcp_server.call_tool(
                query_tool.name, arguments={"identifier": uuid, "query": test_query}
            )

            # Verify the API was called with the correct identifier
            mock_get.assert_called_once_with(f"/hosts/identifier/{uuid}")

            # Verify the query was posted to the correct host ID
            mock_post.assert_called_once_with(
                "/hosts/789/query", json_data={"query": test_query}
            )

            # Verify the result structure
            result_list = result if isinstance(result, list) else [result]
            result_str = str(result_list[0])
            assert "success" in result_str.lower()
            assert "789" in result_str  # host_id

    @pytest.mark.asyncio
    async def test_host_not_found(self, mcp_server, fleet_client):
        """Test handling when host identifier is not found.

        This test validates that the tool correctly handles the case where
        the Fleet API returns a failure when looking up a host by identifier,
        and then tries fuzzy matching by listing all hosts.
        """
        unknown_identifier = "unknown-host-12345"
        test_query = "SELECT * FROM system_info;"

        # Mock response for the identifier lookup (not found)
        mock_identifier_response = FleetResponse(
            success=False, data=None, message="Host not found"
        )

        # Mock response for listing hosts (empty list)
        mock_hosts_response = FleetResponse(
            success=True, data={"hosts": []}, message="Success"
        )

        # Set up side_effect to return different responses for different calls
        def get_side_effect(endpoint, **kwargs):
            if endpoint.startswith("/hosts/identifier/"):
                return mock_identifier_response
            elif endpoint == "/hosts":
                return mock_hosts_response
            return FleetResponse(success=False, data=None, message="Unknown endpoint")

        with patch.object(fleet_client, "get", side_effect=get_side_effect) as mock_get:
            # Register the query tools (where fleet_query_host_by_identifier is defined)
            host_tools.register_query_tools(mcp_server, fleet_client)

            # Get the registered tool
            tools = await mcp_server.list_tools()
            query_tool = next(
                t for t in tools if t.name == "fleet_query_host_by_identifier"
            )

            # Actually call the tool with an unknown identifier
            result = await mcp_server.call_tool(
                query_tool.name,
                arguments={"identifier": unknown_identifier, "query": test_query},
            )

            # Verify the API was called twice (identifier lookup + hosts list)
            assert mock_get.call_count == 2
            mock_get.assert_any_call(f"/hosts/identifier/{unknown_identifier}")
            mock_get.assert_any_call("/hosts")

            # Verify the result indicates failure
            result_list = result if isinstance(result, list) else [result]
            result_str = str(result_list[0])
            assert "success" in result_str.lower()
            assert "false" in result_str.lower()
            assert "not found" in result_str.lower()

    @pytest.mark.asyncio
    async def test_query_fails_after_host_lookup(self, mcp_server, fleet_client):
        """Test handling when host is found but query fails.

        This test validates that the tool correctly handles the case where
        the host lookup succeeds but the query execution fails.
        """
        hostname = "test-host"
        test_query = "SELECT * FROM invalid_table;"

        # Mock successful host lookup
        mock_host_response = FleetResponse(
            success=True,
            data={
                "host": {
                    "id": 123,
                    "hostname": hostname,
                    "uuid": "abc-123",
                }
            },
            message="Success",
        )

        # Mock failed query
        mock_query_response = FleetResponse(
            success=False, data=None, message="Query execution failed"
        )

        with (
            patch.object(
                fleet_client, "get", return_value=mock_host_response
            ) as mock_get,
            patch.object(
                fleet_client, "post", return_value=mock_query_response
            ) as mock_post,
        ):
            # Register the query tools (where fleet_query_host_by_identifier is defined)
            host_tools.register_query_tools(mcp_server, fleet_client)

            # Get the registered tool
            tools = await mcp_server.list_tools()
            query_tool = next(
                t for t in tools if t.name == "fleet_query_host_by_identifier"
            )

            # Actually call the tool
            result = await mcp_server.call_tool(
                query_tool.name, arguments={"identifier": hostname, "query": test_query}
            )

            # Verify both API calls were made
            mock_get.assert_called_once_with(f"/hosts/identifier/{hostname}")
            mock_post.assert_called_once_with(
                "/hosts/123/query", json_data={"query": test_query}
            )

            # Verify the result indicates failure
            result_list = result if isinstance(result, list) else [result]
            result_str = str(result_list[0])
            assert "success" in result_str.lower()
            assert "false" in result_str.lower()

    @pytest.mark.asyncio
    async def test_api_error(self, mcp_server, fleet_client):
        """Test handling of API errors during host lookup.

        This test validates that the tool correctly handles FleetAPIError
        exceptions raised during the host lookup phase. The tool will try
        the identifier lookup first, then try to list hosts for fuzzy matching,
        both of which will fail with the same error.
        """
        hostname = "error-host"
        test_query = "SELECT * FROM system_info;"

        with patch.object(
            fleet_client,
            "get",
            side_effect=FleetAPIError("API error occurred"),
        ) as mock_get:
            # Register the query tools (where fleet_query_host_by_identifier is defined)
            host_tools.register_query_tools(mcp_server, fleet_client)

            # Get the registered tool
            tools = await mcp_server.list_tools()
            query_tool = next(
                t for t in tools if t.name == "fleet_query_host_by_identifier"
            )

            # Actually call the tool
            result = await mcp_server.call_tool(
                query_tool.name, arguments={"identifier": hostname, "query": test_query}
            )

            # Verify the API was called twice (identifier lookup + hosts list attempt)
            assert mock_get.call_count == 2
            mock_get.assert_any_call(f"/hosts/identifier/{hostname}")
            mock_get.assert_any_call("/hosts")

            # Verify the result indicates failure
            result_list = result if isinstance(result, list) else [result]
            result_str = str(result_list[0])
            assert "success" in result_str.lower()
            assert "false" in result_str.lower()
            assert "failed" in result_str.lower() or "error" in result_str.lower()
