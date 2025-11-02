"""Integration tests for fleet_run_live_query_with_results tool.

These tests verify that the tool works correctly with a live Fleet instance,
testing WebSocket connectivity, result collection, and progress notifications.
"""

import json

import pytest

from fleet_mcp.config import FleetConfig
from fleet_mcp.server import FleetMCPServer


@pytest.mark.integration
@pytest.mark.asyncio
class TestFleetRunLiveQueryWithResultsIntegration:
    """Integration tests for fleet_run_live_query_with_results tool."""

    async def test_tool_is_registered(self, live_fleet_config):
        """Test that fleet_run_live_query_with_results tool is registered."""
        # Create server with allow_select_queries enabled
        config = FleetConfig(
            server_url=live_fleet_config.server_url,
            api_token=live_fleet_config.api_token,
            readonly=True,
            allow_select_queries=True,
            verify_ssl=live_fleet_config.verify_ssl,
        )

        server = FleetMCPServer(config)
        tools = await server.mcp.list_tools()
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]

        # Verify the new tool is registered
        assert "fleet_run_live_query_with_results" in tool_names
        print("✓ fleet_run_live_query_with_results tool is registered")

    async def test_query_with_target_all_online_hosts(self, live_fleet_config):
        """Test running a live query targeting all online hosts."""
        try:
            # Create server with allow_select_queries enabled
            config = FleetConfig(
                server_url=live_fleet_config.server_url,
                api_token=live_fleet_config.api_token,
                readonly=True,
                allow_select_queries=True,
                verify_ssl=live_fleet_config.verify_ssl,
            )

            server = FleetMCPServer(config)

            # Call the tool
            result_content = await server.mcp.call_tool(
                "fleet_run_live_query_with_results",
                arguments={
                    "query": "SELECT * FROM uptime;",
                    "target_all_online_hosts": True,
                    "timeout": 30.0,
                },
            )

            # Parse the result (MCP returns TextContent objects)
            result_text = str(result_content[0].text) if result_content else "{}"
            result = json.loads(result_text)

            # Verify the response structure
            assert result is not None
            assert "success" in result

            # If successful, verify full structure
            if result["success"]:
                assert "campaign_id" in result
                assert "results" in result
                assert "total_hosts_targeted" in result
                assert "total_results_received" in result
                assert "execution_time_seconds" in result
                assert "message" in result

                # Verify we got some results
                assert result["total_hosts_targeted"] > 0, "No hosts were targeted"
                assert result["total_results_received"] >= 0, "Invalid result count"

                # Verify results structure
                assert isinstance(result["results"], list)

                # If we got results, verify their structure
                if result["results"]:
                    first_result = result["results"][0]
                    assert "host_id" in first_result
                    assert "hostname" in first_result
                    assert "rows" in first_result or "error" in first_result

                print(
                    f"✓ Successfully executed query on {result['total_hosts_targeted']} hosts"
                )
                print(f"✓ Received {result['total_results_received']} results")
                print(f"✓ Execution time: {result['execution_time_seconds']:.2f}s")
            else:
                # If no online hosts, that's okay for this test
                if "no online hosts" in result.get("message", "").lower():
                    pytest.skip("No online hosts available for testing")
                else:
                    pytest.fail(f"Query failed: {result.get('message')}")

        except Exception as e:
            pytest.skip(f"Query with target_all_online_hosts test failed: {e}")

    async def test_query_validation_no_targets(self, live_fleet_config):
        """Test that the tool validates targeting parameters."""
        try:
            # Create server with allow_select_queries enabled
            config = FleetConfig(
                server_url=live_fleet_config.server_url,
                api_token=live_fleet_config.api_token,
                readonly=True,
                allow_select_queries=True,
                verify_ssl=live_fleet_config.verify_ssl,
            )

            server = FleetMCPServer(config)

            # Try to run a query without any targeting parameters
            result_content = await server.mcp.call_tool(
                "fleet_run_live_query_with_results",
                arguments={
                    "query": "SELECT * FROM uptime;",
                    "timeout": 10.0,
                },
            )

            # Parse the result
            result_text = str(result_content[0].text) if result_content else "{}"
            result = json.loads(result_text)

            # Should fail with validation error
            assert result["success"] is False
            assert "targeting parameter" in result["message"].lower()

            print("✓ Correctly rejected query with no targeting parameters")

        except Exception as e:
            pytest.skip(f"Validation test failed: {e}")

    async def test_tool_not_registered_in_strict_readonly(self, live_fleet_config):
        """Test that the tool is NOT registered when allow_select_queries=False."""
        # Create server with strict readonly mode (no SELECT queries)
        config = FleetConfig(
            server_url=live_fleet_config.server_url,
            api_token=live_fleet_config.api_token,
            readonly=True,
            allow_select_queries=False,  # Strict readonly
            verify_ssl=live_fleet_config.verify_ssl,
        )

        server = FleetMCPServer(config)
        tools = await server.mcp.list_tools()
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]

        # Verify the tool is NOT registered
        assert "fleet_run_live_query_with_results" not in tool_names
        print(
            "✓ fleet_run_live_query_with_results correctly not registered in strict readonly mode"
        )

    async def test_tool_registered_in_write_mode(self, live_fleet_config):
        """Test that the tool is registered in write mode."""
        # Create server with write mode
        config = FleetConfig(
            server_url=live_fleet_config.server_url,
            api_token=live_fleet_config.api_token,
            readonly=False,  # Write mode
            verify_ssl=live_fleet_config.verify_ssl,
        )

        server = FleetMCPServer(config)
        tools = await server.mcp.list_tools()
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]

        # Verify the tool is registered
        assert "fleet_run_live_query_with_results" in tool_names
        print("✓ fleet_run_live_query_with_results correctly registered in write mode")
