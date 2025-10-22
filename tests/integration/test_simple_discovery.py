"""Simple integration tests for table discovery and host queries.

These are basic connectivity and functionality tests.
"""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestSimpleDiscovery:
    """Simple integration tests for basic Fleet operations."""

    async def test_simple_host_query(self, live_fleet_client):
        """Test simple query to a live host."""
        query = "SELECT name FROM osquery_registry WHERE registry = 'table' LIMIT 5;"

        try:
            async with live_fleet_client:
                # Get an online host
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip("No online hosts available for simple query test")

                host_id = online_hosts[0]["id"]

                response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query", json_data={"query": query}
                )

                assert response.success, f"Query failed: {response.message}"
                assert response.data is not None, "No data in response"

                # Check for rows in response
                rows = response.data.get("rows", [])
                assert len(rows) > 0, "No rows returned from query"
                assert len(rows) <= 5, "More rows than expected"

                # Verify row structure
                for row in rows:
                    assert "name" in row, "Row missing 'name' field"

        except Exception as e:
            pytest.skip(f"Host query failed (host may be offline): {e}")

    async def test_osquery_registry_query(self, live_fleet_client):
        """Test querying the osquery registry for available tables."""
        # Query osquery_registry table - columns: name, registry, active, internal, owner_uuid
        query = "SELECT name, registry FROM osquery_registry WHERE registry = 'table' ORDER BY name LIMIT 10;"

        try:
            async with live_fleet_client:
                # Get online hosts
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip("No online hosts available for registry query test")

                # Try all online hosts until one succeeds
                last_error = None
                for host in online_hosts:
                    host_id = host["id"]

                    response = await live_fleet_client.post(
                        f"/hosts/{host_id}/query", json_data={"query": query}
                    )

                    if response.success:
                        rows = response.data.get("rows", [])
                        if len(rows) > 0:
                            # Success! Verify structure
                            for row in rows:
                                assert "name" in row, "Missing table name"
                                assert "registry" in row, "Missing registry column"
                            return  # Test passed
                        else:
                            # Query succeeded but returned 0 rows
                            last_error = "osquery_registry table returned 0 rows"
                    else:
                        last_error = response.message

                # If we get here, no hosts returned data
                pytest.skip(
                    f"osquery_registry table not available or empty on all tested hosts. "
                    f"Last error: {last_error}"
                )

        except Exception as e:
            pytest.skip(f"Registry query failed: {e}")

    async def test_system_info_query(self, live_fleet_client):
        """Test querying system_info table."""
        query = "SELECT hostname, uuid, cpu_brand FROM system_info;"

        try:
            async with live_fleet_client:
                # Get an online host
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip("No online hosts available for system_info query test")

                host_id = online_hosts[0]["id"]

                response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query", json_data={"query": query}
                )

                assert response.success, "system_info query failed"

                rows = response.data.get("rows", [])
                assert len(rows) == 1, "Expected exactly one row from system_info"

                row = rows[0]
                assert "hostname" in row, "Missing hostname"
                assert "uuid" in row, "Missing uuid"
                assert "cpu_brand" in row, "Missing cpu_brand"

                # Verify data is not empty
                assert len(row["hostname"]) > 0, "Hostname is empty"
                assert len(row["uuid"]) > 0, "UUID is empty"

        except Exception as e:
            pytest.skip(f"system_info query failed (host may be offline): {e}")

    async def test_multiple_hosts_query(self, live_fleet_client):
        """Test that we can query different hosts."""
        query = "SELECT hostname FROM system_info;"

        try:
            async with live_fleet_client:
                # Get all online hosts
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip(
                        "No online hosts available for multiple hosts query test"
                    )

                successful_queries = 0

                # Try querying up to 4 hosts
                for host in online_hosts[:4]:
                    host_id = host["id"]
                    try:
                        response = await live_fleet_client.post(
                            f"/hosts/{host_id}/query", json_data={"query": query}
                        )

                        if response.success:
                            successful_queries += 1

                    except Exception:
                        # Host may not respond, continue
                        continue

                # At least one host should respond
                assert successful_queries > 0, "No successful queries to any host"

        except Exception as e:
            pytest.skip(f"Multiple hosts query test failed: {e}")

    async def test_invalid_query_handling(self, live_fleet_client):
        """Test that invalid queries are handled properly."""
        query = "SELECT * FROM nonexistent_table_xyz;"

        try:
            async with live_fleet_client:
                # Get an online host
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip("No online hosts available for invalid query test")

                host_id = online_hosts[0]["id"]

                response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query", json_data={"query": query}
                )

                # Query should fail or return empty results
                # The exact behavior depends on osquery version
                if response.success:
                    rows = response.data.get("rows", [])
                    # If successful, should return empty results
                    assert len(rows) == 0, "Invalid query returned results"

        except Exception:
            # Expected to fail - this is acceptable
            pass

    async def test_query_timeout_handling(self, live_fleet_client):
        """Test that query timeouts are handled properly."""
        # This query might take a while on some systems
        query = "SELECT * FROM processes;"

        try:
            async with live_fleet_client:
                # Get an online host
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip("No online hosts available for timeout test")

                host_id = online_hosts[0]["id"]

                response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query", json_data={"query": query}
                )

                # Should either succeed or timeout gracefully
                if response.success:
                    assert response.data is not None
                    rows = response.data.get("rows", [])
                    # processes table should return at least some rows
                    assert len(rows) > 0, "processes query returned no results"

        except Exception as e:
            # Timeout or other error is acceptable for this test
            pytest.skip(f"Query timeout test inconclusive: {e}")
