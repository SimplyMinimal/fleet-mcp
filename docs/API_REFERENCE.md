# Fleet MCP API Reference

This document provides detailed information about all available MCP tools in the Fleet MCP server.

## Tool Categories

### Host Management Tools

#### `fleet_list_hosts`
List hosts in Fleet with optional filtering and pagination.

**Parameters:**
- `page` (int, default: 0): Page number for pagination (0-based)
- `per_page` (int, default: 100): Number of hosts per page (max 500)
- `query` (str, default: ""): Search query to filter hosts by hostname, UUID, hardware serial, or IPv4
- `team_id` (int, optional): Filter hosts by team ID
- `status` (str, optional): Filter by host status (online, offline, mia)
- `order_key` (str, default: "hostname"): Field to order by (hostname, computer_name, platform, status)
- `order_direction` (str, default: "asc"): Sort direction (asc, desc)

**Returns:**
```json
{
  "success": true,
  "hosts": [...],
  "count": 25,
  "total_count": 150,
  "page": 0,
  "per_page": 100,
  "message": "Found 25 hosts"
}
```

#### `fleet_get_host`
Get detailed information about a specific host.

**Parameters:**
- `host_id` (int): The ID of the host to retrieve

**Returns:**
```json
{
  "success": true,
  "host": {
    "id": 123,
    "hostname": "laptop-001",
    "platform": "darwin",
    "osquery_version": "5.9.1",
    "status": "online",
    ...
  },
  "message": "Retrieved host laptop-001"
}
```

#### `fleet_search_hosts`
Search for hosts by hostname, UUID, hardware serial, or IP address.

**Parameters:**
- `query` (str): Search term
- `limit` (int, default: 50): Maximum number of results

#### `fleet_get_host_by_identifier`
Get host by hostname, UUID, or hardware serial number.

**Parameters:**
- `identifier` (str): Host identifier

#### `fleet_delete_host`
Delete a host from Fleet.

**Parameters:**
- `host_id` (int): The ID of the host to delete

**Note:** Deleted hosts may attempt to re-enroll if they have valid enroll secrets.

#### `fleet_transfer_hosts`
Transfer hosts to a different team.

**Parameters:**
- `team_id` (int): Target team ID (use 0 for "No team")
- `host_ids` (List[int]): List of host IDs to transfer

### Query Management Tools

#### `fleet_list_queries`
List all saved queries in Fleet.

**Parameters:**
- `page` (int, default: 0): Page number for pagination
- `per_page` (int, default: 100): Number of queries per page
- `order_key` (str, default: "name"): Field to order by
- `order_direction` (str, default: "asc"): Sort direction
- `team_id` (int, optional): Filter queries by team ID

#### `fleet_create_query`
Create a new saved query in Fleet.

**Parameters:**
- `name` (str): Name for the query
- `query` (str): SQL query string (osquery syntax)
- `description` (str, optional): Description of the query
- `team_id` (int, optional): Team ID to associate the query with
- `observer_can_run` (bool, default: false): Whether observers can run this query

**Example:**
```python
fleet_create_query(
    name="Running Processes",
    query="SELECT pid, name, cmdline FROM processes WHERE state = 'R';",
    description="Show all currently running processes"
)
```

#### `fleet_run_live_query`
Execute a live query against specified hosts.

**Parameters:**
- `query` (str): SQL query string to execute
- `host_ids` (List[int], optional): List of specific host IDs to target
- `label_ids` (List[int], optional): List of label IDs to target hosts
- `team_ids` (List[int], optional): List of team IDs to target hosts

#### `fleet_get_query_results`
Get results from a live query campaign.

**Parameters:**
- `campaign_id` (int): ID of the query campaign

#### `fleet_run_saved_query`
Run a saved query against specified hosts.

**Parameters:**
- `query_id` (int): ID of the saved query to run
- `host_ids` (List[int], optional): List of specific host IDs to target
- `label_ids` (List[int], optional): List of label IDs to target hosts
- `team_ids` (List[int], optional): List of team IDs to target hosts

### Policy Management Tools

#### `fleet_list_policies`
List all policies in Fleet.

**Parameters:**
- `team_id` (int, optional): Filter policies by team ID

#### `fleet_create_policy`
Create a new compliance policy in Fleet.

**Parameters:**
- `name` (str): Name for the policy
- `query` (str): SQL query that defines the policy check
- `description` (str, optional): Description of the policy
- `resolution` (str, optional): Resolution steps for policy failures
- `team_id` (int, optional): Team ID to associate the policy with
- `critical` (bool, default: false): Whether this is a critical policy

**Example:**
```python
fleet_create_policy(
    name="Firewall Enabled",
    query="SELECT 1 FROM alf WHERE global_state = 1;",
    description="Ensure macOS firewall is enabled",
    resolution="Enable the firewall in System Preferences > Security & Privacy",
    critical=True
)
```

#### `fleet_get_policy_results`
Get compliance results for a specific policy.

**Parameters:**
- `policy_id` (int): ID of the policy to get results for
- `team_id` (int, optional): Filter results by team ID

#### `fleet_update_policy`
Update an existing policy in Fleet.

**Parameters:**
- `policy_id` (int): ID of the policy to update
- `name` (str, optional): New name for the policy
- `query` (str, optional): New SQL query for the policy
- `description` (str, optional): New description for the policy
- `resolution` (str, optional): New resolution steps for the policy
- `critical` (bool, optional): Whether this is a critical policy

### Software & Vulnerability Tools

#### `fleet_list_software`
List software inventory across the fleet.

**Parameters:**
- `page` (int, default: 0): Page number for pagination
- `per_page` (int, default: 100): Number of software items per page
- `order_key` (str, default: "name"): Field to order by
- `order_direction` (str, default: "asc"): Sort direction
- `query` (str, default: ""): Search query to filter software by name
- `team_id` (int, optional): Filter software by team ID
- `vulnerable` (bool, optional): Filter to only vulnerable software

#### `fleet_get_software`
Get detailed information about a specific software item.

**Parameters:**
- `software_id` (int): ID of the software item to retrieve

#### `fleet_get_host_software`
Get software installed on a specific host.

**Parameters:**
- `host_id` (int): ID of the host to get software for
- `page` (int, default: 0): Page number for pagination
- `per_page` (int, default: 100): Number of software items per page
- `query` (str, default: ""): Search query to filter software by name
- `vulnerable` (bool, optional): Filter to only vulnerable software

#### `fleet_get_vulnerabilities`
List known vulnerabilities across the fleet.

**Parameters:**
- `page` (int, default: 0): Page number for pagination
- `per_page` (int, default: 100): Number of vulnerabilities per page
- `order_key` (str, default: "cve"): Field to order by
- `order_direction` (str, default: "asc"): Sort direction
- `team_id` (int, optional): Filter vulnerabilities by team ID
- `known_exploit` (bool, optional): Filter to vulnerabilities with known exploits
- `cve_search` (str, default: ""): Search for specific CVE IDs

### Team & User Management Tools

#### `fleet_list_teams`
List all teams in Fleet.

**Returns:**
```json
{
  "success": true,
  "teams": [
    {
      "id": 1,
      "name": "Engineering",
      "description": "Engineering team hosts",
      "host_count": 25
    }
  ],
  "count": 3,
  "message": "Found 3 teams"
}
```

#### `fleet_create_team`
Create a new team in Fleet.

**Parameters:**
- `name` (str): Name for the team
- `description` (str, optional): Description of the team

#### `fleet_list_users`
List all users in Fleet.

**Parameters:**
- `page` (int, default: 0): Page number for pagination
- `per_page` (int, default: 100): Number of users per page
- `order_key` (str, default: "name"): Field to order by
- `order_direction` (str, default: "asc"): Sort direction
- `query` (str, default: ""): Search query to filter users by name or email
- `team_id` (int, optional): Filter users by team ID

#### `fleet_list_activities`
List Fleet activities and audit logs.

**Parameters:**
- `page` (int, default: 0): Page number for pagination
- `per_page` (int, default: 100): Number of activities per page
- `order_key` (str, default: "created_at"): Field to order by
- `order_direction` (str, default: "desc"): Sort direction

### System Tools

#### `fleet_health_check`
Check Fleet server connectivity and authentication.

**Returns:**
```json
{
  "success": true,
  "message": "Fleet server is accessible and authentication successful",
  "server_url": "https://fleet.example.com",
  "status": "healthy",
  "details": {}
}
```

## Error Handling

All tools return a standardized response format:

```json
{
  "success": boolean,
  "message": "Human-readable message",
  "data": "Tool-specific data",
  "error_details": "Additional error information (if applicable)"
}
```

### Common Error Types

- **Authentication Error**: Invalid or expired API token
- **Not Found Error**: Requested resource doesn't exist
- **Validation Error**: Invalid input parameters
- **Network Error**: Connection issues with Fleet server
- **Permission Error**: Insufficient permissions for operation

## Rate Limiting

Fleet MCP respects Fleet API rate limits:
- Automatic retry with exponential backoff
- Configurable timeout and retry settings
- Graceful handling of rate limit responses

## Best Practices

1. **Use specific targeting** for queries instead of fleet-wide operations
2. **Implement pagination** for large datasets
3. **Cache results** when appropriate to reduce API calls
4. **Monitor query performance** and optimize as needed
5. **Use team filtering** to scope operations appropriately
