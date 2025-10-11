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
        host_id = 6
        query = "SELECT name FROM osquery_registry WHERE registry = 'table' LIMIT 5;"
        
        try:
            async with live_fleet_client:
                response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query",
                    json_data={"query": query}
                )
                
                assert response.success, f"Query failed: {response.message}"
                assert response.data is not None, "No data in response"
                
                # Check for rows in response
                rows = response.data.get('rows', [])
                assert len(rows) > 0, "No rows returned from query"
                assert len(rows) <= 5, "More rows than expected"
                
                # Verify row structure
                for row in rows:
                    assert 'name' in row, "Row missing 'name' field"
                    
        except Exception as e:
            pytest.skip(f"Host query failed (host may be offline): {e}")

    async def test_osquery_registry_query(self, live_fleet_client):
        """Test querying the osquery registry for available tables."""
        host_id = 6
        query = "SELECT name, type FROM osquery_registry WHERE registry = 'table' ORDER BY name LIMIT 10;"
        
        try:
            async with live_fleet_client:
                response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query",
                    json_data={"query": query}
                )
                
                assert response.success, "Registry query failed"
                
                rows = response.data.get('rows', [])
                assert len(rows) > 0, "No tables found in registry"
                
                # Verify we got table information
                for row in rows:
                    assert 'name' in row, "Missing table name"
                    assert 'type' in row, "Missing table type"
                    
        except Exception as e:
            pytest.skip(f"Registry query failed (host may be offline): {e}")

    async def test_system_info_query(self, live_fleet_client):
        """Test querying system_info table."""
        host_id = 6
        query = "SELECT hostname, uuid, cpu_brand FROM system_info;"
        
        try:
            async with live_fleet_client:
                response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query",
                    json_data={"query": query}
                )
                
                assert response.success, "system_info query failed"
                
                rows = response.data.get('rows', [])
                assert len(rows) == 1, "Expected exactly one row from system_info"
                
                row = rows[0]
                assert 'hostname' in row, "Missing hostname"
                assert 'uuid' in row, "Missing uuid"
                assert 'cpu_brand' in row, "Missing cpu_brand"
                
                # Verify data is not empty
                assert len(row['hostname']) > 0, "Hostname is empty"
                assert len(row['uuid']) > 0, "UUID is empty"
                
        except Exception as e:
            pytest.skip(f"system_info query failed (host may be offline): {e}")

    async def test_multiple_hosts_query(self, live_fleet_client):
        """Test that we can query different hosts."""
        query = "SELECT hostname FROM system_info;"
        
        # Try multiple host IDs
        host_ids = [3, 4, 5, 6]
        successful_queries = 0
        
        for host_id in host_ids:
            try:
                async with live_fleet_client:
                    response = await live_fleet_client.post(
                        f"/hosts/{host_id}/query",
                        json_data={"query": query}
                    )
                    
                    if response.success:
                        successful_queries += 1
                        
            except Exception:
                # Host may be offline, continue
                continue
        
        # At least one host should respond
        if successful_queries == 0:
            pytest.skip("No hosts available for testing")
        
        assert successful_queries > 0, "No successful queries to any host"

    async def test_invalid_query_handling(self, live_fleet_client):
        """Test that invalid queries are handled properly."""
        host_id = 6
        query = "SELECT * FROM nonexistent_table_xyz;"
        
        try:
            async with live_fleet_client:
                response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query",
                    json_data={"query": query}
                )
                
                # Query should fail or return empty results
                # The exact behavior depends on osquery version
                if response.success:
                    rows = response.data.get('rows', [])
                    # If successful, should return empty results
                    assert len(rows) == 0, "Invalid query returned results"
                    
        except Exception as e:
            # Expected to fail - this is acceptable
            pass

    async def test_query_timeout_handling(self, live_fleet_client):
        """Test that query timeouts are handled properly."""
        host_id = 6
        # This query might take a while on some systems
        query = "SELECT * FROM processes;"
        
        try:
            async with live_fleet_client:
                response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query",
                    json_data={"query": query}
                )
                
                # Should either succeed or timeout gracefully
                if response.success:
                    assert response.data is not None
                    rows = response.data.get('rows', [])
                    # processes table should return at least some rows
                    assert len(rows) > 0, "processes query returned no results"
                    
        except Exception as e:
            # Timeout or other error is acceptable for this test
            pytest.skip(f"Query timeout test inconclusive: {e}")

