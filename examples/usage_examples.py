"""Usage examples for Fleet MCP."""

import asyncio
from fleet_mcp import FleetClient, FleetConfig


async def example_host_management():
    """Example of host management operations."""
    config = FleetConfig(
        server_url="https://fleet.example.com",
        api_token="your-api-token"
    )
    
    async with FleetClient(config) as client:
        # List all hosts
        response = await client.get("/hosts")
        print(f"Found {len(response.data.get('hosts', []))} hosts")
        
        # Search for specific host
        response = await client.get("/hosts", params={"query": "laptop"})
        hosts = response.data.get("hosts", [])
        
        if hosts:
            host = hosts[0]
            print(f"Host: {host['hostname']} ({host['platform']})")
            
            # Get detailed host information
            host_id = host["id"]
            response = await client.get(f"/hosts/{host_id}")
            detailed_host = response.data.get("host", {})
            print(f"Host details: {detailed_host.get('computer_name')}")


async def example_query_operations():
    """Example of query operations."""
    config = FleetConfig(
        server_url="https://fleet.example.com",
        api_token="your-api-token"
    )
    
    async with FleetClient(config) as client:
        # Create a new query
        query_data = {
            "name": "List Running Processes",
            "query": "SELECT pid, name, cmdline FROM processes WHERE state = 'R';",
            "description": "Show all currently running processes"
        }
        
        response = await client.post("/queries", json_data=query_data)
        if response.success:
            query = response.data.get("query", {})
            print(f"Created query: {query['name']} (ID: {query['id']})")
            
            # Run the query on all hosts
            run_data = {
                "selected": {
                    "hosts": [],  # Empty means all hosts
                    "labels": [],
                    "teams": []
                }
            }
            
            response = await client.post(f"/queries/{query['id']}/run", json_data=run_data)
            if response.success:
                campaign = response.data.get("campaign", {})
                print(f"Started campaign: {campaign['id']}")
                
                # Wait a bit and get results
                await asyncio.sleep(5)
                response = await client.get(f"/queries/{campaign['id']}/results")
                if response.success:
                    results = response.data.get("results", [])
                    print(f"Got {len(results)} results")


async def example_policy_management():
    """Example of policy management."""
    config = FleetConfig(
        server_url="https://fleet.example.com",
        api_token="your-api-token"
    )
    
    async with FleetClient(config) as client:
        # Create a security policy
        policy_data = {
            "name": "Firewall Enabled",
            "query": "SELECT 1 FROM alf WHERE global_state = 1;",
            "description": "Ensure macOS firewall is enabled",
            "resolution": "Enable the firewall in System Preferences > Security & Privacy",
            "critical": True
        }
        
        response = await client.post("/policies", json_data=policy_data)
        if response.success:
            policy = response.data.get("policy", {})
            print(f"Created policy: {policy['name']} (ID: {policy['id']})")
            
            # Check policy results
            response = await client.get(f"/policies/{policy['id']}")
            if response.success:
                policy_results = response.data.get("policy", {})
                passing = policy_results.get("passing_host_count", 0)
                failing = policy_results.get("failing_host_count", 0)
                print(f"Policy compliance: {passing} passing, {failing} failing")


async def example_software_inventory():
    """Example of software inventory operations."""
    config = FleetConfig(
        server_url="https://fleet.example.com",
        api_token="your-api-token"
    )
    
    async with FleetClient(config) as client:
        # List vulnerable software
        response = await client.get("/software", params={"vulnerable": "true"})
        if response.success:
            vulnerable_software = response.data.get("software", [])
            print(f"Found {len(vulnerable_software)} vulnerable software packages")
            
            for software in vulnerable_software[:5]:  # Show first 5
                print(f"- {software['name']} v{software['version']} "
                      f"({software.get('vulnerabilities_count', 0)} CVEs)")
        
        # Get vulnerabilities
        response = await client.get("/vulnerabilities", params={"exploit": "true"})
        if response.success:
            exploitable_vulns = response.data.get("vulnerabilities", [])
            print(f"Found {len(exploitable_vulns)} exploitable vulnerabilities")


if __name__ == "__main__":
    print("Fleet MCP Usage Examples")
    print("========================")
    
    # Note: These examples require a real Fleet instance and API token
    # Uncomment and modify the examples below to test with your Fleet instance
    
    # asyncio.run(example_host_management())
    # asyncio.run(example_query_operations())
    # asyncio.run(example_policy_management())
    # asyncio.run(example_software_inventory())
    
    print("Examples are commented out. Uncomment and configure to test with your Fleet instance.")
