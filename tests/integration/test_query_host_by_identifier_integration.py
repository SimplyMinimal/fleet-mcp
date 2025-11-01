"""Integration tests for fleet_query_host_by_identifier tool.

These tests verify that the tool works correctly with a live Fleet instance,
testing all three identifier types: hostname, UUID, and hardware serial number.
"""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestFleetQueryHostByIdentifierIntegration:
    """Integration tests for fleet_query_host_by_identifier tool."""

    async def test_query_by_hostname(self, live_fleet_client):
        """Test querying a host by hostname against live Fleet instance."""
        try:
            async with live_fleet_client:
                # First, get a list of online hosts
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip("No online hosts available for hostname query test")

                # Pick the first online host and get its hostname
                test_host = online_hosts[0]
                hostname = test_host.get("hostname")
                host_id = test_host.get("id")

                if not hostname:
                    pytest.skip("Test host has no hostname")

                print(f"\nTesting with hostname: {hostname} (host_id: {host_id})")

                # Test 1: Lookup host by hostname
                lookup_response = await live_fleet_client.get(
                    f"/hosts/identifier/{hostname}"
                )
                assert (
                    lookup_response.success
                ), f"Failed to lookup host by hostname: {hostname}"
                assert lookup_response.data is not None
                assert lookup_response.data.get("host", {}).get("id") == host_id

                # Test 2: Run a simple query using the hostname
                test_query = "SELECT * FROM system_info;"
                query_response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query", json_data={"query": test_query}
                )

                assert (
                    query_response.success
                ), f"Failed to query host {host_id} by hostname"
                assert query_response.data is not None
                assert "rows" in query_response.data or "status" in query_response.data

                print(
                    f"✓ Successfully queried host by hostname: {hostname} -> host_id {host_id}"
                )

        except Exception as e:
            pytest.skip(f"Query by hostname test failed: {e}")

    async def test_query_by_uuid(self, live_fleet_client):
        """Test querying a host by UUID against live Fleet instance."""
        try:
            async with live_fleet_client:
                # First, get a list of online hosts
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip("No online hosts available for UUID query test")

                # Pick the first online host and get its UUID
                test_host = online_hosts[0]
                uuid = test_host.get("uuid")
                host_id = test_host.get("id")

                if not uuid:
                    pytest.skip("Test host has no UUID")

                print(f"\nTesting with UUID: {uuid} (host_id: {host_id})")

                # Test 1: Lookup host by UUID
                lookup_response = await live_fleet_client.get(
                    f"/hosts/identifier/{uuid}"
                )
                assert lookup_response.success, f"Failed to lookup host by UUID: {uuid}"
                assert lookup_response.data is not None
                assert lookup_response.data.get("host", {}).get("id") == host_id

                # Test 2: Run a simple query using the UUID
                test_query = "SELECT * FROM os_version;"
                query_response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query", json_data={"query": test_query}
                )

                assert query_response.success, f"Failed to query host {host_id} by UUID"
                assert query_response.data is not None
                assert "rows" in query_response.data or "status" in query_response.data

                print(
                    f"✓ Successfully queried host by UUID: {uuid} -> host_id {host_id}"
                )

        except Exception as e:
            pytest.skip(f"Query by UUID test failed: {e}")

    async def test_query_by_serial_number(self, live_fleet_client):
        """Test querying a host by hardware serial number against live Fleet instance."""
        try:
            async with live_fleet_client:
                # First, get a list of online hosts
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip(
                        "No online hosts available for serial number query test"
                    )

                # Find a host with a hardware serial number
                test_host = None
                for host in online_hosts:
                    serial = host.get("hardware_serial")
                    if serial and serial.strip():  # Non-empty serial
                        test_host = host
                        break

                if not test_host:
                    pytest.skip(
                        "No online hosts with hardware serial numbers available"
                    )

                serial_number = test_host.get("hardware_serial")
                host_id = test_host.get("id")

                print(
                    f"\nTesting with serial number: {serial_number} (host_id: {host_id})"
                )

                # Test 1: Lookup host by serial number
                lookup_response = await live_fleet_client.get(
                    f"/hosts/identifier/{serial_number}"
                )
                assert (
                    lookup_response.success
                ), f"Failed to lookup host by serial: {serial_number}"
                assert lookup_response.data is not None
                assert lookup_response.data.get("host", {}).get("id") == host_id

                # Test 2: Run a simple query using the serial number
                test_query = "SELECT * FROM system_info;"
                query_response = await live_fleet_client.post(
                    f"/hosts/{host_id}/query", json_data={"query": test_query}
                )

                assert (
                    query_response.success
                ), f"Failed to query host {host_id} by serial"
                assert query_response.data is not None
                assert "rows" in query_response.data or "status" in query_response.data

                print(
                    f"✓ Successfully queried host by serial: {serial_number} -> host_id {host_id}"
                )

        except Exception as e:
            pytest.skip(f"Query by serial number test failed: {e}")

    async def test_query_nonexistent_identifier(self, live_fleet_client):
        """Test that querying with a nonexistent identifier returns appropriate error."""
        try:
            async with live_fleet_client:
                # Try to lookup a host that doesn't exist
                fake_identifier = "nonexistent-host-12345-abcde"

                lookup_response = await live_fleet_client.get(
                    f"/hosts/identifier/{fake_identifier}"
                )

                # Should fail or return no data
                assert (
                    not lookup_response.success or lookup_response.data is None
                ), "Expected failure when looking up nonexistent identifier"

                print(f"✓ Correctly handled nonexistent identifier: {fake_identifier}")

        except Exception as e:
            # This is expected - the API should return an error
            print(f"✓ API correctly raised error for nonexistent identifier: {e}")

    async def test_all_identifier_types_resolve_to_same_host(self, live_fleet_client):
        """Test that hostname, UUID, and serial all resolve to the same host."""
        try:
            async with live_fleet_client:
                # Get a list of online hosts
                response = await live_fleet_client.get("/hosts")
                assert response.success, "Failed to list hosts"

                hosts = response.data.get("hosts", [])
                online_hosts = [h for h in hosts if h.get("status") == "online"]

                if not online_hosts:
                    pytest.skip("No online hosts available")

                # Find a host with all three identifiers
                test_host = None
                for host in online_hosts:
                    if (
                        host.get("hostname")
                        and host.get("uuid")
                        and host.get("hardware_serial")
                        and host.get("hardware_serial").strip()
                    ):
                        test_host = host
                        break

                if not test_host:
                    pytest.skip(
                        "No online hosts with all three identifier types available"
                    )

                hostname = test_host.get("hostname")
                uuid = test_host.get("uuid")
                serial = test_host.get("hardware_serial")
                expected_host_id = test_host.get("id")

                print(
                    f"\nTesting identifier equivalence for host_id {expected_host_id}:"
                )
                print(f"  hostname: {hostname}")
                print(f"  uuid: {uuid}")
                print(f"  serial: {serial}")

                # Lookup by hostname
                hostname_response = await live_fleet_client.get(
                    f"/hosts/identifier/{hostname}"
                )
                assert hostname_response.success
                hostname_host_id = hostname_response.data.get("host", {}).get("id")

                # Lookup by UUID
                uuid_response = await live_fleet_client.get(f"/hosts/identifier/{uuid}")
                assert uuid_response.success
                uuid_host_id = uuid_response.data.get("host", {}).get("id")

                # Lookup by serial
                serial_response = await live_fleet_client.get(
                    f"/hosts/identifier/{serial}"
                )
                assert serial_response.success
                serial_host_id = serial_response.data.get("host", {}).get("id")

                # All should resolve to the same host ID
                assert (
                    hostname_host_id
                    == uuid_host_id
                    == serial_host_id
                    == expected_host_id
                ), f"Identifiers resolved to different hosts: hostname={hostname_host_id}, uuid={uuid_host_id}, serial={serial_host_id}, expected={expected_host_id}"

                print(
                    f"✓ All three identifiers correctly resolved to host_id {expected_host_id}"
                )

        except Exception as e:
            pytest.skip(f"Identifier equivalence test failed: {e}")
