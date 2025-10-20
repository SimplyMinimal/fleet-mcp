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

#### `fleet_query_host`
Run an ad-hoc live query against a specific host and get results immediately.

**Parameters:**
- `host_id` (int): ID of the host to query
- `query` (str): SQL query string to execute

**Returns:**
```json
{
  "success": true,
  "host_id": 123,
  "query": "SELECT * FROM processes;",
  "status": "online",
  "error": null,
  "rows": [...],
  "row_count": 45
}
```

**Note:** Query will timeout if the host doesn't respond within FLEET_LIVE_QUERY_REST_PERIOD (default 25 seconds).

#### `fleet_query_host_by_identifier`
Run an ad-hoc live query against a host identified by UUID, hostname, or serial number.

**Parameters:**
- `identifier` (str): Host UUID, hostname, or hardware serial number
- `query` (str): SQL query string to execute

**Returns:**
```json
{
  "success": true,
  "identifier": "my-laptop",
  "query": "SELECT * FROM system_info;",
  "status": "online",
  "error": null,
  "rows": [...],
  "row_count": 1
}
```

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

#### `fleet_get_query_report`
Get the latest results from a scheduled query.

**Parameters:**
- `query_id` (int): ID of the saved query
- `team_id` (int, optional): Filter results to hosts in a specific team

**Returns:**
```json
{
  "success": true,
  "query_id": 31,
  "results": [...],
  "result_count": 150,
  "report_clipped": false
}
```

**Note:** This retrieves stored results from scheduled queries. For live/ad-hoc queries, use `fleet_run_live_query` or `fleet_query_host`.

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
  "details": {},
  "server_config": {
    "readonly_mode": true,
    "allow_select_queries": true
  },
  "fleet_user": {
    "fleet_user_role": "admin",
    "fleet_user_email": "admin@example.com",
    "fleet_user_name": "Admin User",
    "fleet_user_global_role": "admin",
    "fleet_user_teams": [1, 2, 3],
    "fleet_user_error": null
  },
  "osquery_schema_cache": {
    "cached": true,
    "cache_file_path": "/Users/username/.fleet-mcp/cache/osquery_fleet_schema.json",
    "file_size_bytes": 1048576,
    "file_size_human": "1.00 MB",
    "tables_loaded": 250,
    "cache_age_seconds": 3600,
    "cache_age_hours": 1.0,
    "cache_valid": true,
    "cache_ttl_hours": 24,
    "last_modified": "1.00 hours ago",
    "schema_source": "cache",
    "status": "healthy",
    "errors": [],
    "warnings": []
  }
}
```

**Server Configuration Fields:**
- `readonly_mode` (bool): Whether the MCP server is running in read-only mode (from `FLEET_READONLY` config)
- `allow_select_queries` (bool): Whether SELECT queries are allowed when in read-only mode (from `FLEET_ALLOW_SELECT_QUERIES` config)

**Fleet User Information Fields:**
- `fleet_user_role` (str|null): The role assigned to the authenticated API token in Fleet (e.g., "admin", "maintainer", "observer", "gitops")
- `fleet_user_email` (str|null): Email address of the authenticated user
- `fleet_user_name` (str|null): Name of the authenticated user
- `fleet_user_global_role` (str|null): Global role if applicable, or null if team-specific
- `fleet_user_teams` (list[int]|null): List of team IDs the user has access to
- `fleet_user_error` (str|null): Error message if user information could not be retrieved, null on success

**Cache Information Fields:**
- `cached` (bool): Whether the schema file is cached locally
- `cache_file_path` (str): Full path to the cached schema file
- `file_size_bytes` (int|null): Size of the cache file in bytes
- `file_size_human` (str): Human-readable file size (e.g., "1.5 MB")
- `tables_loaded` (int): Number of osquery tables loaded from cache
- `cache_age_seconds` (float|null): Age of cache file in seconds
- `cache_age_hours` (float|null): Age of cache file in hours
- `cache_valid` (bool): Whether the cache is within the TTL period (24 hours)
- `cache_ttl_hours` (float): Cache time-to-live in hours
- `last_modified` (str): Human-readable timestamp of last cache modification
- `schema_source` (str|null): Source of loaded schemas - `"cache"`, `"download"`, `"cache_stale"`, `"bundled"`, or `"none"`
- `status` (str): Overall cache health status - `"healthy"`, `"warning"`, `"degraded"`, or `"error"`
- `errors` (list[str]): List of error messages encountered during cache loading
- `warnings` (list[str]): List of warning messages (e.g., stale cache, low table count)

**Cache Status Values:**
- `"healthy"`: Cache is working properly with 50+ tables loaded
- `"warning"`: Cache has warnings (e.g., stale cache, using bundled schemas)
- `"degraded"`: Low table count (< 50 tables) but no errors
- `"error"`: Critical errors encountered during cache loading

**Schema Source Values:**
- `"cache"`: Loaded from valid cached file
- `"download"`: Freshly downloaded from Fleet's schema repository
- `"cache_stale"`: Loaded from expired cache (download failed)
- `"bundled"`: Using bundled fallback schemas (no cache available)
- `"none"`: No schemas loaded (all loading attempts failed)

**Example - Cache with Warnings:**
```json
{
  "osquery_schema_cache": {
    "cached": true,
    "tables_loaded": 2,
    "schema_source": "cache",
    "status": "warning",
    "errors": [],
    "warnings": [
      "Low table count (2 tables) - expected 100+ tables. Cache may be incomplete or using test data."
    ]
  }
}
```

**Example - Cache Loading Error:**
```json
{
  "osquery_schema_cache": {
    "cached": false,
    "tables_loaded": 0,
    "schema_source": "none",
    "status": "error",
    "errors": [
      "Failed to download Fleet schema: Connection timeout",
      "Failed to load bundled schemas: File not found"
    ],
    "warnings": [
      "No schemas loaded - all loading attempts failed. Check network connectivity and cache file."
    ]
  }
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

## Osquery Table Reference Tools

### `fleet_list_osquery_tables`
List all available osquery tables with their schemas and descriptions.

**Parameters:**
- `platform` (str, optional): Filter tables by platform (darwin, linux, windows, chrome)
- `search` (str, optional): Search tables by name or description (case-insensitive)
- `evented_only` (bool, default: false): If True, only return evented tables
- `limit` (int, default: 100): Maximum number of tables to return

**Example:**
```python
fleet_list_osquery_tables(
    platform="darwin",
    search="process",
    limit=50
)
```

### `fleet_get_osquery_table_schema`
Get detailed schema information for a specific osquery table.

**Parameters:**
- `table_name` (str): Name of the osquery table to get schema for

**Example:**
```python
fleet_get_osquery_table_schema("processes")
```

### `fleet_suggest_tables_for_query`
Suggest relevant osquery tables based on query intent or keywords.

**Parameters:**
- `query_intent` (str): Description of what you want to query
- `platform` (str, optional): Target platform to filter suggestions
- `limit` (int, default: 10): Maximum number of suggestions to return

**Example:**
```python
fleet_suggest_tables_for_query(
    query_intent="running processes and network connections",
    platform="linux",
    limit=5
)
```

### Script Management Tools

#### `fleet_list_scripts`
List all scripts available in Fleet.

**Parameters:**
- `team_id` (int, optional): Filter scripts by team ID (Premium feature)
- `page` (int, default: 0): Page number for pagination (0-based)
- `per_page` (int, default: 100): Number of scripts per page

**Returns:**
```json
{
  "success": true,
  "scripts": [
    {
      "id": 1,
      "team_id": null,
      "name": "script_1.sh",
      "created_at": "2023-07-30T13:41:07Z",
      "updated_at": "2023-07-30T13:41:07Z"
    }
  ],
  "count": 1,
  "message": "Found 1 scripts"
}
```

#### `fleet_get_script`
Get details of a specific script.

**Parameters:**
- `script_id` (int): ID of the script to retrieve

**Returns:**
```json
{
  "success": true,
  "script": {
    "id": 1,
    "team_id": null,
    "name": "script_1.sh",
    "created_at": "2023-07-30T13:41:07Z",
    "updated_at": "2023-07-30T13:41:07Z"
  },
  "message": "Retrieved script 1"
}
```

#### `fleet_get_script_result`
Get the result of a script execution.

**Parameters:**
- `execution_id` (str): The execution ID of the script run

**Returns:**
```json
{
  "success": true,
  "result": {
    "script_contents": "echo 'hello'",
    "exit_code": 0,
    "output": "hello",
    "message": "",
    "hostname": "Test Host",
    "host_timeout": false,
    "host_id": 1,
    "execution_id": "e797d6c6-3aae-11ee-be56-0242ac120002",
    "runtime": 20,
    "created_at": "2024-09-11T20:30:24Z"
  },
  "message": "Retrieved script result for execution e797d6c6-3aae-11ee-be56-0242ac120002"
}
```

#### `fleet_list_batch_scripts`
List batch script executions.

**Parameters:**
- `team_id` (int, optional): Filter by team ID (Premium feature)
- `status` (str, optional): Filter by status (started, scheduled, finished)
- `page` (int, default: 0): Page number for pagination (0-based)
- `per_page` (int, default: 100): Number of results per page

#### `fleet_get_batch_script`
Get details of a batch script execution.

**Parameters:**
- `batch_execution_id` (str): The batch execution ID

#### `fleet_list_batch_script_hosts`
List hosts targeted in a batch script execution.

**Parameters:**
- `batch_execution_id` (str): The batch execution ID
- `status` (str, optional): Filter by host status (ran, pending, errored, incompatible, canceled)
- `page` (int, default: 0): Page number for pagination (0-based)
- `per_page` (int, default: 100): Number of results per page

#### `fleet_list_host_scripts`
List scripts available for a specific host.

**Parameters:**
- `host_id` (int): ID of the host
- `page` (int, default: 0): Page number for pagination (0-based)
- `per_page` (int, default: 100): Number of results per page

#### `fleet_run_script`
Run a script on a specific host.

**Parameters:**
- `host_id` (int): ID of the host to run the script on
- `script_id` (int, optional): ID of an existing saved script
- `script_contents` (str, optional): Contents of the script to run (max 10,000 characters)
- `script_name` (str, optional): Name of an existing saved script (requires team_id)
- `team_id` (int, optional): Team ID (required if using script_name)

**Note:** Exactly one of script_id, script_contents, or script_name must be provided.

**Returns:**
```json
{
  "success": true,
  "host_id": 1227,
  "execution_id": "e797d6c6-3aae-11ee-be56-0242ac120002",
  "message": "Script execution started on host 1227"
}
```

#### `fleet_run_batch_script`
Run a script on multiple hosts in a batch.

**Parameters:**
- `script_id` (int): ID of the saved script to run
- `host_ids` (List[int], optional): List of host IDs to target
- `filters` (dict, optional): Filter object with query, status, label_id, team_id
- `not_before` (str, optional): UTC time when batch should start (ISO 8601 format)

**Note:** Either host_ids or filters must be provided, but not both.

**Returns:**
```json
{
  "success": true,
  "batch_execution_id": "e797d6c6-3aae-11ee-be56-0242ac120002",
  "message": "Batch script execution started"
}
```

#### `fleet_cancel_batch_script`
Cancel a batch script execution.

**Parameters:**
- `batch_execution_id` (str): The batch execution ID to cancel

**Returns:**
```json
{
  "success": true,
  "batch_execution_id": "e797d6c6-3aae-11ee-be56-0242ac120002",
  "message": "Batch script e797d6c6-3aae-11ee-be56-0242ac120002 canceled"
}
```

#### `fleet_create_script`
Create and upload a new script.

**Parameters:**
- `script_contents` (str): The contents of the script
- `team_id` (int, optional): Team ID to associate the script with (Premium feature)

**Returns:**
```json
{
  "success": true,
  "script_id": 1227,
  "message": "Script created with ID 1227"
}
```

#### `fleet_modify_script`
Modify an existing script.

**Parameters:**
- `script_id` (int): ID of the script to modify
- `script_contents` (str): New contents of the script

**Returns:**
```json
{
  "success": true,
  "script": {
    "id": 1,
    "team_id": null,
    "name": "script_1.sh",
    "created_at": "2023-07-30T13:41:07Z",
    "updated_at": "2023-07-30T13:41:07Z"
  },
  "message": "Script 1 modified successfully"
}
```

#### `fleet_delete_script`
Delete a script.

**Parameters:**
- `script_id` (int): ID of the script to delete

**Returns:**
```json
{
  "success": true,
  "script_id": 1,
  "message": "Script 1 deleted successfully"
}
```

## Best Practices

1. **Use specific targeting** for queries instead of fleet-wide operations
2. **Implement pagination** for large datasets
3. **Cache results** when appropriate to reduce API calls
4. **Monitor query performance** and optimize as needed
5. **Use team filtering** to scope operations appropriately
6. **Script Management:**
   - Always validate script contents before running on production hosts
   - Use batch operations for running scripts on multiple hosts
   - Monitor script execution results to ensure successful completion
   - Use filters for batch operations to target specific host groups
   - Test scripts on a small set of hosts before rolling out fleet-wide
