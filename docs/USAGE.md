# Fleet MCP API Reference

This document provides detailed information about all available MCP tools in the Fleet MCP server.

## Overview

Fleet MCP provides a set of tools for managing and monitoring your Fleet DM instance through the Model Context Protocol (MCP). The server supports three operational modes:

1. **Strict Read-Only Mode** (Default): `readonly=true`, `allow_select_queries=false`
   - View-only access to all Fleet resources
   - No query execution capabilities
   - Safest mode for exploration and monitoring

2. **Read-Only with SELECT Queries**: `readonly=true`, `allow_select_queries=true`
   - View-only access to all Fleet resources
   - Run SELECT-only osquery queries on hosts
   - All queries are validated to prevent data modification (yes, even though Fleet itself doesn't allow it anyway)
   - Recommended for investigation and monitoring

3. **Full Write Access**: `readonly=false`
   - Complete access to all Fleet operations
   - Create, update, and delete resources
   - Run any osquery queries without validation
   - ⚠️ Use with caution - recommended to have LLM prompt for confirmation before making changes

## Getting Started

1. **Start with read-only mode** for safe exploration
2. **Use `fleet_health_check`** to verify your configuration
   - Example: "Check the health of the Fleet server"
3. **Try `fleet_list_hosts`** to see your fleet
   - Example: "List all hosts in Fleet"
4. **Enable SELECT queries** when you need to investigate
5. **Use table discovery tools** to build effective queries
   - `fleet_suggest_tables_for_query`
   - `fleet_get_osquery_table_schema`
   - `fleet_list_osquery_tables`
6. **Run queries with `fleet_query_host`** for immediate results from one host
7. **Use `fleet_run_live_query_with_results`** for multi-host queries with results
8. **Explore other tools** for managing policies, software, and more

## Quick Reference

### Most Commonly Used Tools

**Host Management:**
- `fleet_list_hosts` - List all hosts with filtering
- `fleet_get_host` - Get detailed host information
- `fleet_search_hosts` - Search for hosts by name/UUID/IP
- `fleet_get_host_software` - Get software installed on a host

**Query Execution (requires `allow_select_queries=true` or `readonly=false`):**
- `fleet_query_host` - Run query on a specific host (immediate results)
- `fleet_query_host_by_identifier` - Run query by hostname/UUID (immediate results)
- `fleet_run_live_query_with_results` - Run live query across multiple hosts and collect results via WebSocket
- `fleet_get_query_report` - Get results from scheduled queries

**Software & Vulnerabilities:**
- `fleet_list_software` - List all software across the fleet
- `fleet_search_software` - Search for software by name
- `fleet_find_software_on_host` - Find specific software on a host
- `fleet_get_vulnerabilities` - List known vulnerabilities

**Osquery Table Discovery:**
- `fleet_suggest_tables_for_query` - Get table suggestions based on intent
- `fleet_get_osquery_table_schema` - Get detailed table schema
- `fleet_list_osquery_tables` - List all available tables

**Policies & Compliance:**
- `fleet_list_policies` - List all policies
- `fleet_get_policy_results` - Get policy compliance results

**System:**
- `fleet_health_check` - Check server connectivity and configuration

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
- `query` (str): Search term (hostname, UUID, serial number, or IP)
- `page` (int, default: 0): Page number for pagination (0-based)
- `per_page` (int, default: 50): Number of results per page (max 500)
- `order_key` (str, default: "hostname"): Field to order by (hostname, computer_name, platform, status)
- `order_direction` (str, default: "asc"): Sort direction (asc, desc)

**Returns:**
```json
{
  "success": true,
  "hosts": [...],
  "count": 10,
  "message": "Found 10 hosts matching 'laptop'"
}
```

#### `fleet_get_host_by_identifier`
Get host by hostname, UUID, or hardware serial number.

**Parameters:**
- `identifier` (str): Host identifier (hostname, UUID, or hardware serial)

**Returns:**
```json
{
  "success": true,
  "host": {
    "id": 123,
    "hostname": "laptop-001",
    "uuid": "abc-123-def",
    ...
  },
  "message": "Retrieved host laptop-001"
}
```

#### `fleet_get_host_software`
Get software installed on a specific host.

**Parameters:**
- `host_id` (int): ID of the host to get software for
- `query` (str, default: ""): Search query to filter software by name (case-insensitive)
- `vulnerable` (bool, optional): Filter to only vulnerable software (true) or non-vulnerable (false)

**Returns:**
```json
{
  "success": true,
  "host_id": 123,
  "software": [
    {
      "id": 456,
      "name": "Google Chrome",
      "version": "120.0.6099.109",
      "source": "programs",
      "vulnerabilities": []
    }
  ],
  "count": 150,
  "message": "Found 150 software items on host 123"
}
```

#### `fleet_delete_host`
Delete a host from Fleet.

**Parameters:**
- `host_id` (int): The ID of the host to delete

**Note:**
- Deleted hosts may attempt to re-enroll if they have valid enroll secrets.
- This tool is only available when `readonly=false`.

#### `fleet_transfer_hosts`
Transfer hosts to a different team.

**Parameters:**
- `team_id` (int): Target team ID (use 0 for "No team")
- `host_ids` (List[int]): List of host IDs to transfer

**Note:** This tool is only available when `readonly=false`.

#### `fleet_query_host`
Run an ad-hoc live query against a specific host and get results immediately.

**Availability:**
- **Read-Only Mode with SELECT Queries** (`readonly=true`, `allow_select_queries=true`): Only SELECT queries allowed, validated before execution
- **Full Write Access** (`readonly=false`): All queries allowed without validation

**Parameters:**
- `host_id` (int): ID of the host to query
- `query` (str): SQL query string to execute (SELECT-only in read-only mode)

**Returns:**
```json
{
  "success": true,
  "host_id": 123,
  "query": "SELECT * FROM processes WHERE name LIKE '%chrome%';",
  "status": "online",
  "error": null,
  "rows": [
    {
      "pid": "1234",
      "name": "chrome",
      "cmdline": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    }
  ],
  "row_count": 1
}
```

**Notes:**
- Query will timeout if the host doesn't respond within FLEET_LIVE_QUERY_REST_PERIOD (default 25 seconds)
- In read-only mode with SELECT queries enabled, all queries are validated to ensure they are SELECT-only
- Use this for quick, one-off queries on a single host

#### `fleet_query_host_by_identifier`
Run an ad-hoc live query against a host identified by UUID, hostname, or serial number.

**Availability:**
- **Read-Only Mode with SELECT Queries** (`readonly=true`, `allow_select_queries=true`): Only SELECT queries allowed, validated before execution
- **Full Write Access** (`readonly=false`): All queries allowed without validation

**Parameters:**
- `identifier` (str): Host identifier - supports multiple formats:
  - Host UUID (e.g., `392547dc-0000-0000-a87a-d701ff75bc65`)
  - Hostname/computer name (e.g., `my-laptop.local`)
  - Hardware serial number (e.g., `C02ABC123DEF`)
  - osquery host ID
  - Node key
- `query` (str): SQL query string to execute (SELECT-only in read-only mode)

**Returns:**
```json
{
  "success": true,
  "identifier": "my-laptop",
  "host_id": 123,
  "hostname": "my-laptop.local",
  "query": "SELECT * FROM system_info;",
  "status": "online",
  "error": null,
  "rows": [
    {
      "hostname": "my-laptop",
      "cpu_brand": "Apple M1",
      "physical_memory": "17179869184"
    }
  ],
  "row_count": 1,
  "message": "Query executed on my-laptop.local, returned 1 rows"
}
```

**Notes:**
- Convenient when you know the hostname/serial but not the host ID
- Automatically resolves the identifier to the host ID before executing the query
- Same timeout and validation rules as `fleet_query_host`
- Returns both the original identifier and the resolved host information

### Query Management Tools

#### `fleet_list_queries`
List all saved queries in Fleet.

**Parameters:**
- `page` (int, default: 0): Page number for pagination
- `per_page` (int, default: 100): Number of queries per page
- `order_key` (str, default: "name"): Field to order by
- `order_direction` (str, default: "asc"): Sort direction
- `team_id` (int, optional): Filter queries by team ID

#### `fleet_get_query`
Get details of a specific saved query.

**Parameters:**
- `query_id` (int): ID of the query to retrieve

**Returns:**
```json
{
  "success": true,
  "query": {
    "id": 31,
    "name": "Running Processes",
    "query": "SELECT pid, name FROM processes WHERE state = 'R';",
    "description": "Show all currently running processes",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "Retrieved query 31"
}
```

#### `fleet_create_query`
Create a new saved query in Fleet.

**Availability:** Only available when `readonly=false`

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

#### `fleet_run_live_query_with_results`
Execute a live query campaign and collect results in real-time via WebSocket.

**Availability:**
- **Read-Only Mode with SELECT Queries** (`readonly=true`, `allow_select_queries=true`): Only SELECT queries allowed, validated before execution
- **Full Write Access** (`readonly=false`): All queries allowed without validation

**Overview:**
This tool runs a live query campaign across multiple hosts and **collects and returns query results** via WebSocket. It creates a campaign, connects to Fleet's WebSocket API, and streams results back as they arrive with real-time progress notifications.

**Parameters:**
- `query` (str): SQL query string to execute (SELECT-only in read-only mode)
- `host_ids` (List[int], optional*): List of specific host IDs to target
- `label_ids` (List[int], optional*): List of label IDs to target hosts
- `team_ids` (List[int], optional*): List of team IDs to target hosts
- `target_all_online_hosts` (bool, optional*): If True, automatically fetches and targets all online hosts
- `timeout` (float, default: 60.0): Maximum time in seconds to wait for results

*At least ONE targeting parameter must be provided.

**Returns:**
```json
{
  "success": true,
  "campaign_id": 123,
  "results": [
    {
      "host_id": 1,
      "hostname": "host1.example.com",
      "rows": [{"column1": "value1", "column2": "value2"}],
      "error": null
    },
    {
      "host_id": 2,
      "hostname": "host2.example.com",
      "rows": [{"column1": "value3", "column2": "value4"}],
      "error": null
    }
  ],
  "total_hosts_targeted": 150,
  "total_results_received": 127,
  "execution_time_seconds": 28.4,
  "message": "Campaign completed. Received 127 results from 150 targeted hosts in 28.4s"
}
```

**Progress Notifications:**
As the query executes, you'll receive real-time progress updates:
```
Creating live query campaign...
Targeting 150 online hosts
Connecting to WebSocket...
Subscribed to campaign 123
Received 45/150 results (8.2s elapsed)
Received 89/150 results (15.7s elapsed)
Received 127/150 results (28.4s elapsed)
Campaign completed
```

**Examples:**

```python
# Query all online hosts and get results
result = fleet_run_live_query_with_results(
    query="SELECT * FROM uptime",
    target_all_online_hosts=True,
    timeout=60.0
)
# Returns: {"success": true, "results": [...], "total_results_received": 127, ...}

# Query specific hosts by ID
result = fleet_run_live_query_with_results(
    query="SELECT * FROM system_info",
    host_ids=[1, 2, 3],
    timeout=30.0
)

# Query hosts with a specific label
result = fleet_run_live_query_with_results(
    query="SELECT * FROM users WHERE username LIKE 'admin%'",
    label_ids=[5],
    timeout=45.0
)

# Query all hosts in a team
result = fleet_run_live_query_with_results(
    query="SELECT * FROM processes WHERE name = 'chrome'",
    team_ids=[0],  # 0 = "No team"
    timeout=60.0
)
```

**When to Use This Tool:**
- ✅ You need query results from **multiple hosts** programmatically
- ✅ You want real-time progress updates as results arrive
- ✅ You're okay with waiting up to `timeout` seconds for results
- ✅ You need aggregated results from many hosts in one response

**When to Use Alternatives:**
- Use `fleet_query_host()` if you only need results from **one specific host** (faster, no WebSocket overhead)
- Use `fleet_query_host_by_identifier()` if you want to query by hostname/UUID instead of host ID

**Timeout Behavior:**
- The tool waits up to `timeout` seconds for results to arrive
- If the timeout expires, the tool returns whatever results were collected so far
- The campaign continues running on Fleet even after timeout (results just won't be collected)
- Recommended timeout: 60-120 seconds for large fleets (100+ hosts)

**WebSocket Connection:**
- Requires WebSocket connectivity to Fleet server (port 443 for HTTPS, port 80 for HTTP)
- Uses the same SSL verification settings as the REST API (`verify_ssl` config)
- Automatically handles authentication using your API token
- Connection is closed automatically after results are collected or timeout expires

**Error Handling:**
- Returns `{"success": false, "message": "..."}` if campaign creation fails
- Returns partial results if some hosts fail to respond
- Individual host errors are included in the `results` array with `"error": "message"`
- WebSocket connection errors are logged and returned in the response

**Notes:**
- In read-only mode, all queries are validated to ensure they are SELECT-only
- Progress notifications are sent via MCP's standard progress reporting mechanism
- Results are aggregated in memory - very large result sets may consume significant memory
- This tool is ideal for investigations, audits, and compliance checks across your fleet

#### `fleet_get_query_report`
Get the latest stored results from a SCHEDULED query.

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

**Important Notes:**
- This tool ONLY works for scheduled queries (queries with an 'interval' set that run periodically)
- It retrieves the stored results from the last time the scheduled query ran
- This tool does NOT work for:
  - Ad-hoc queries that haven't been saved and scheduled
  - Queries that don't have 'interval' configured
- For running ad-hoc queries and getting results, use:
  - `fleet_query_host(host_id, query)` - Run query on ONE host and get results
  - `fleet_query_host_by_identifier(identifier, query)` - Run query by hostname/UUID
  - `fleet_run_live_query_with_results(query, ...)` - Run query across multiple hosts and collect results

#### `fleet_run_saved_query`
Run a saved query against specified hosts.

**Availability:**
- **Read-Only Mode with SELECT Queries** (`readonly=true`, `allow_select_queries=true`): Only SELECT queries allowed, validated before execution
- **Full Write Access** (`readonly=false`): All queries allowed without validation

**Parameters:**
- `query_id` (int): ID of the saved query to run
- `host_ids` (List[int], optional): List of specific host IDs to target
- `label_ids` (List[int], optional): List of label IDs to target hosts
- `team_ids` (List[int], optional): List of team IDs to target hosts

**Returns:**
```json
{
  "success": true,
  "campaign_id": 456,
  "query_id": 31,
  "query_name": "Running Processes",
  "message": "Saved query campaign 456 started"
}
```

**Notes:**
- The saved query will be validated to ensure it's SELECT-only in read-only mode
- For immediate results from a single host, use `fleet_query_host` instead

### Policy Management Tools

#### `fleet_list_policies`
List all policies in Fleet.

**Parameters:**
- `team_id` (int, optional): Filter policies by team ID

#### `fleet_get_policy`
Get details of a specific policy.

**Parameters:**
- `policy_id` (int): ID of the policy to retrieve

**Returns:**
```json
{
  "success": true,
  "policy": {
    "id": 1,
    "name": "Firewall Enabled",
    "query": "SELECT 1 FROM alf WHERE global_state = 1;",
    "description": "Ensure macOS firewall is enabled",
    "resolution": "Enable the firewall in System Preferences > Security & Privacy",
    "critical": true,
    "passing_host_count": 45,
    "failing_host_count": 5
  },
  "message": "Retrieved policy 1"
}
```

#### `fleet_create_policy`
Create a new compliance policy in Fleet.

**Availability:** Only available when `readonly=false`

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

**Availability:** Only available when `readonly=false`

**Parameters:**
- `policy_id` (int): ID of the policy to update
- `name` (str, optional): New name for the policy
- `query` (str, optional): New SQL query for the policy
- `description` (str, optional): New description for the policy
- `resolution` (str, optional): New resolution steps for the policy
- `critical` (bool, optional): Whether this is a critical policy

#### `fleet_delete_policy`
Delete a policy from Fleet.

**Availability:** Only available when `readonly=false`

**Parameters:**
- `policy_id` (int): ID of the policy to delete

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

#### `fleet_search_software`
Search for software by name across the fleet.

**Parameters:**
- `query` (str): Search term for software name
- `limit` (int, default: 50): Maximum number of results to return
- `team_id` (int, optional): Filter search by team ID
- `vulnerable` (bool, optional): Filter to only vulnerable software (true) or non-vulnerable (false)

**Returns:**
```json
{
  "success": true,
  "software": [
    {
      "id": 123,
      "name": "Google Chrome",
      "version": "120.0.6099.109",
      "hosts_count": 45,
      "vulnerabilities": ["CVE-2024-1234"]
    }
  ],
  "count": 1,
  "message": "Found 1 software items matching 'chrome'"
}
```

**Notes:**
- Useful for quickly finding software across your entire fleet
- Returns aggregated software data (not host-specific)

#### `fleet_find_software_on_host`
Find specific software on a host by hostname.

**Parameters:**
- `hostname` (str): The hostname of the host to search
- `software_name` (str): The name of the software to find (case-insensitive)

**Returns:**
```json
{
  "success": true,
  "hostname": "laptop-001",
  "host_id": 123,
  "software_name": "firefox",
  "software": [
    {
      "id": 456,
      "name": "Firefox",
      "version": "121.0",
      "source": "programs",
      "vulnerabilities": []
    }
  ],
  "count": 1,
  "message": "Found 1 software items matching 'firefox' on laptop-001"
}
```

**Notes:**
- Useful for answering questions like "What version of Firefox is XYZ-Machine using?"
- Combines host lookup and software search in one convenient tool

#### `fleet_get_vulnerabilities`
List known vulnerabilities across the fleet with advanced filtering capabilities.

This function retrieves vulnerabilities from the Fleet API and applies optional client-side filters to the results. Server-side filters (known_exploit, cve_search, order_key) are applied first, then client-side filters are applied to the returned data.

**Server-Side Parameters:**
- `page` (int, default: 0): Page number for pagination
- `per_page` (int, default: 100): Number of vulnerabilities per page
- `order_key` (str, default: "cve"): Field to order by (cve, created_at, hosts_count)
- `order_direction` (str, default: "asc"): Sort direction (asc, desc)
- `team_id` (int, optional): Filter vulnerabilities by team ID
- `known_exploit` (bool, optional): Filter to vulnerabilities with known exploits
- `cve_search` (str, default: ""): Search for specific CVE IDs

**Client-Side Filter Parameters (Fleet Premium):**
- `cve_published_after` (str, optional): Filter CVEs published after this date (ISO format, e.g., "2023-01-01")
- `cve_published_before` (str, optional): Filter CVEs published before this date (ISO format, e.g., "2024-01-01")
- `description_keywords` (str, optional): Filter CVEs whose description contains these keywords (case-insensitive)
- `min_epss_probability` (float, optional): Filter CVEs with EPSS probability >= this value (0.0-1.0)
- `max_epss_probability` (float, optional): Filter CVEs with EPSS probability <= this value (0.0-1.0)
- `min_cvss_score` (float, optional): Filter CVEs with CVSS score >= this value (0.0-10.0)
- `max_cvss_score` (float, optional): Filter CVEs with CVSS score <= this value (0.0-10.0)

**Note:** Client-side filters require Fleet Premium as they depend on Premium-only fields (cvss_score, epss_probability, cve_published, cve_description). If these fields are not available, the filters will skip vulnerabilities with missing data.

**Returns:**
```json
{
  "success": true,
  "vulnerabilities": [
    {
      "cve": "CVE-2024-1234",
      "details_link": "https://nvd.nist.gov/vuln/detail/CVE-2024-1234",
      "hosts_count": 15,
      "created_at": "2024-01-15T10:30:00Z",
      "cvss_score": 9.8,
      "epss_probability": 0.95,
      "cisa_known_exploit": true,
      "cve_published": "2024-01-10T00:00:00Z",
      "cve_description": "Critical remote code execution vulnerability"
    }
  ],
  "count": 1,
  "total_count": 5,
  "message": "Found 1 vulnerabilities (4 filtered out by client-side filters)"
}
```

**Example Usage:**
```python
# Get high-severity vulnerabilities with known exploits published in 2023
result = await fleet_get_vulnerabilities(
    known_exploit=True,
    min_cvss_score=7.0,
    cve_published_after="2023-01-01",
    cve_published_before="2024-01-01"
)

# Get vulnerabilities with high exploit probability
result = await fleet_get_vulnerabilities(
    min_epss_probability=0.7,
    min_cvss_score=8.0
)

# Search for specific types of vulnerabilities
result = await fleet_get_vulnerabilities(
    description_keywords="remote code execution",
    min_cvss_score=9.0
)
```

#### `fleet_list_software_titles`
List software titles in Fleet.

**Parameters:**
- `page` (int, default: 0): Page number for pagination
- `per_page` (int, default: 100): Number of software titles per page
- `order_key` (str, default: "name"): Field to order by
- `order_direction` (str, default: "asc"): Sort direction
- `query` (str, default: ""): Search query to filter software by name
- `team_id` (int, optional): Filter software by team ID
- `available_for_install` (bool, optional): Filter to software available for installation

**Notes:**
- Software titles represent unique software products that may have multiple versions installed across hosts
- This is different from `fleet_list_software` which lists individual software versions

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

#### `fleet_get_team`
Get details of a specific team.

**Parameters:**
- `team_id` (int): ID of the team to retrieve

**Returns:**
```json
{
  "success": true,
  "team": {
    "id": 1,
    "name": "Engineering",
    "description": "Engineering team hosts",
    "host_count": 25,
    "user_count": 10
  },
  "message": "Retrieved team 1"
}
```

#### `fleet_create_team`
Create a new team in Fleet.

**Availability:** Only available when `readonly=false`

**Parameters:**
- `name` (str): Name for the team
- `description` (str, optional): Description of the team

#### `fleet_list_users`
List all users in Fleet.

**Parameters:**
- `page` (int, default: 0): Page number for pagination
- `per_page` (int, default: 100): Number of users per page
- `order_key` (str, default: "name"): Field to order by (name, email, created_at)
- `order_direction` (str, default: "asc"): Sort direction (asc, desc)
- `query` (str, default: ""): Search query to filter users by name or email
- `team_id` (int, optional): Filter users by team ID

**Returns:**
```json
{
  "success": true,
  "users": [
    {
      "id": 1,
      "name": "Admin User",
      "email": "admin@example.com",
      "global_role": "admin",
      "teams": [],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1,
  "message": "Found 1 users"
}
```

#### `fleet_get_user`
Get details of a specific user.

**Parameters:**
- `user_id` (int): ID of the user to retrieve

**Returns:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "name": "Admin User",
    "email": "admin@example.com",
    "global_role": "admin",
    "teams": [],
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "Retrieved user 1"
}
```

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

**Osquery Schema Cache:**
The health check includes detailed information about the osquery schema cache, which powers the table discovery tools. The cache uses a hybrid approach:
1. Downloads YAML schema files from Fleet's GitHub repository (https://github.com/fleetdm/fleet/tree/main/schema/tables)
2. Caches them locally in `~/.fleet-mcp/cache/`
3. Merges with bundled schemas for offline fallback
4. Provides rich metadata including usage requirements, examples, and platform compatibility

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
- `loaded_overrides_count` (int): Number of schema overrides loaded from Fleet's YAML files
- `overrides_source` (str): Source of schema overrides - `"cache"`, `"download"`, or `"none"`
- `overrides_cache_file` (str): Path to the cached schema overrides file

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

**Authentication Errors:**
- **Invalid API Token**: Check that your `FLEET_API_TOKEN` is correct
- **Expired Token**: Generate a new API token in Fleet UI
- **Insufficient Permissions**: Ensure the API token has the required role (admin, maintainer, observer, gitops)

**Query Validation Errors (Read-Only Mode):**
- **Non-SELECT Query**: Only SELECT queries are allowed in read-only mode with `allow_select_queries=true`
- **Blocked Operations**: INSERT, UPDATE, DELETE, DROP, and other modification operations are blocked
- **Solution**: Either modify the query to be SELECT-only or switch to `readonly=false` mode

**Resource Errors:**
- **Not Found**: Requested resource (host, query, policy, etc.) doesn't exist
- **Invalid ID**: Check that the ID is correct and the resource hasn't been deleted

**Network Errors:**
- **Connection Timeout**: Check that `FLEET_SERVER_URL` is correct and accessible
- **SSL Verification Failed**: Set `verify_ssl=false` if using self-signed certificates (not recommended for production)
- **DNS Resolution Failed**: Verify the Fleet server hostname is correct

**Permission Errors:**
- **Read-Only Mode**: Operation requires `readonly=false`
- **Insufficient Role**: Some operations require admin or maintainer roles
- **Team Access**: User may not have access to the specified team

### Rate Limiting

Fleet MCP respects Fleet API rate limits:
- Automatic retry with exponential backoff
- Configurable timeout and retry settings via `timeout` and `max_retries` config
- Graceful handling of rate limit responses
- Default timeout: 30 seconds
- Default max retries: 3

### Troubleshooting Tips

1. **Check server connectivity**: Run `fleet_health_check` to verify connection and configuration
2. **Verify API token**: Ensure your API token is valid and has the required permissions
3. **Check mode configuration**: Verify `readonly` and `allow_select_queries` settings match your needs
4. **Review query syntax**: Use `fleet_suggest_tables_for_query` to find the right tables
5. **Check schema overrides**: Use `fleet_get_osquery_table_schema` to see usage requirements
6. **Monitor cache health**: Check `fleet_health_check` for schema cache status

## Osquery Table Reference Tools

These tools help you discover and understand osquery tables for building effective queries. They use a hybrid approach combining live table discovery with Fleet's curated schema repository.

### Schema Overrides Feature

Fleet MCP includes support for a powerful schema overrides feature that enhances osquery table documentation with important usage requirements and examples from Fleet's curated repository.

**How It Works:**
1. Downloads YAML schema files from Fleet's GitHub repository: `https://github.com/fleetdm/fleet/tree/main/schema/tables/`
2. Caches them locally in `~/.fleet-mcp/cache/schema_overrides.json`
3. Merges override data with base osquery schemas
4. Displays usage requirements prominently in table schema responses

**What You Get:**
- **Override Notes**: Important usage requirements, warnings, and best practices
- **Override Examples**: Recommended query patterns and examples
- **Platform Compatibility**: Accurate platform support information
- **Join Requirements**: Tables that require joins are clearly marked

**Example Override:**
When you query the `vscode_extensions` table schema, you'll see:
```
⚠️ IMPORTANT: Querying this table requires joining against the users table.
Example: SELECT * FROM users CROSS JOIN vscode_extensions USING (uid);
```

**Cache Management:**
- Schemas are cached for 24 hours to reduce network requests
- Automatic refresh when cache expires
- Offline fallback to bundled schemas if download fails
- Check cache status with `fleet_health_check`

### `fleet_list_osquery_tables`
List all available osquery tables with their schemas and descriptions.

This tool dynamically discovers tables from:
1. Live osquery hosts (if host_id provided) - most accurate
2. Fleet's curated schema repository - rich metadata
3. Bundled schemas - offline fallback

**Parameters:**
- `host_id` (int, optional): Optional host ID to discover tables from (recommended for accuracy)
- `platform` (str, optional): Filter tables by platform (darwin, linux, windows, chrome)
- `search` (str, optional): Search tables by name or description (case-insensitive)
- `evented_only` (bool, default: false): If True, only return evented tables
- `limit` (int, default: 100): Maximum number of tables to return
- `include_custom` (bool, default: true): Include custom/extension tables

**Returns:**
```json
{
  "success": true,
  "tables": [
    {
      "name": "processes",
      "description": "All running processes on the host",
      "platforms": ["darwin", "linux", "windows"],
      "columns": ["pid", "name", "path", "cmdline", "state"],
      "evented": true,
      "examples": ["SELECT * FROM processes WHERE name = 'chrome';"],
      "has_overrides": true,
      "override_notes": "Querying this table requires joining..."
    }
  ],
  "count": 1,
  "total_tables": 250,
  "message": "Found 1 osquery tables"
}
```

**Example:**
```python
fleet_list_osquery_tables(
    host_id=123,  # Discover tables from this host
    platform="darwin",
    search="process",
    limit=50
)
```

### `fleet_get_osquery_table_schema`
Get detailed schema information for a specific osquery table.

**Parameters:**
- `table_name` (str): Name of the osquery table to get schema for
- `host_id` (int, optional): Optional host ID to get live schema from (recommended)

**Returns:**
```json
{
  "success": true,
  "table": {
    "name": "processes",
    "description": "All running processes on the host",
    "platforms": ["darwin", "linux", "windows"],
    "columns": [
      {
        "name": "pid",
        "type": "BIGINT",
        "description": "Process ID",
        "required": false
      }
    ],
    "evented": true,
    "examples": [
      "SELECT * FROM processes WHERE name = 'chrome';"
    ],
    "notes": "This table is evented...",
    "has_overrides": true,
    "override_notes": "⚠️ IMPORTANT: Querying this table requires...",
    "override_examples": ["SELECT * FROM ..."]
  },
  "message": "Retrieved schema for table 'processes'"
}
```

**Example:**
```python
fleet_get_osquery_table_schema("processes", host_id=123)
```

**Notes:**
- Schema overrides from Fleet's repository are displayed prominently
- Override notes contain important usage requirements and warnings
- Override examples show recommended query patterns

### `fleet_suggest_tables_for_query`
Suggest relevant osquery tables based on query intent or keywords.

This tool helps you find the right osquery tables for your query by:
1. Analyzing your intent (e.g., "find installed software", "check network connections")
2. Matching keywords against table names, descriptions, and columns
3. Providing relevance scores to rank suggestions
4. Including usage examples and metadata

**Parameters:**
- `query_intent` (str): Natural language description of what you want to query
- `host_id` (int, optional): Optional host ID to discover tables from (recommended)
- `platform` (str, optional): Target platform (darwin, linux, windows, chrome) - filters suggestions
- `limit` (int, default: 10): Maximum number of suggestions

**Returns:**
```json
{
  "success": true,
  "suggestions": [
    {
      "table_name": "processes",
      "relevance_score": 0.95,
      "description": "All running processes on the host",
      "platforms": ["darwin", "linux", "windows"],
      "examples": ["SELECT * FROM processes WHERE name = 'chrome';"],
      "reason": "Matched keywords: process, running"
    }
  ],
  "count": 1,
  "query_intent": "running processes",
  "message": "Found 1 table suggestions"
}
```

**Best Practices:**
- Describe what you want to find, not how to find it
- Use natural language (e.g., "running processes" not "SELECT * FROM processes")
- Specify host_id for most accurate results (discovers custom tables)
- Specify platform if known (darwin/linux/windows) for better suggestions

**Examples:**
```python
# Find tables for installed software
fleet_suggest_tables_for_query(
    query_intent="find all installed Python packages",
    platform="darwin",
    limit=5
)
# Suggests: rpm_packages, deb_packages, programs

# Find tables for network monitoring
fleet_suggest_tables_for_query(
    query_intent="check which processes are listening on ports",
    host_id=123,
    limit=5
)
# Suggests: processes, listening_ports

# Find tables for browser data
fleet_suggest_tables_for_query(
    query_intent="list browser extensions",
    platform="darwin"
)
# Suggests: chrome_extensions, firefox_addons
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
Get details of a specific script including its contents.

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
    "updated_at": "2023-07-30T13:41:07Z",
    "script_contents": "#!/bin/bash\necho 'Hello World'\n"
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

**Availability:** Only available when `readonly=false`

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

**Important:**
- Always validate script contents before running on production hosts
- Use `fleet_get_script_result` to check execution status and output

#### `fleet_run_batch_script`
Run a script on multiple hosts in a batch.

**Availability:** Only available when `readonly=false`

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

**Best Practices:**
- Test scripts on a small set of hosts before rolling out fleet-wide
- Use filters for batch operations to target specific host groups
- Monitor script execution results with `fleet_list_batch_script_hosts`

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

**Availability:** Only available when `readonly=false`

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

**Availability:** Only available when `readonly=false`

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

**Availability:** Only available when `readonly=false`

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

## Configuration Modes

Fleet MCP supports three operational modes to balance functionality with safety:

### 1. Strict Read-Only Mode (Default)
```toml
[fleet]
readonly = true
allow_select_queries = false
```

**Available Tools:**
- All list/get/search tools (hosts, software, policies, queries, etc.)
- `fleet_health_check`
- Osquery table reference tools
- NO query execution capabilities

**Use Cases:**
- Safe exploration of Fleet resources
- Monitoring and reporting
- Learning about your fleet without risk of changes

### 2. Read-Only with SELECT Queries
```toml
[fleet]
readonly = true
allow_select_queries = true
```

**Available Tools:**
- All read-only tools from strict mode
- `fleet_query_host` - Run SELECT queries on specific hosts
- `fleet_query_host_by_identifier` - Run SELECT queries by hostname/UUID
- `fleet_run_live_query_with_results` - Run SELECT queries across multiple hosts and collect results via WebSocket
- `fleet_run_saved_query` - Run saved SELECT queries

**Query Validation:**
- All queries are validated to ensure they are SELECT-only
- INSERT, UPDATE, DELETE, DROP, and other modification operations are blocked
- Provides safe investigation and monitoring capabilities

**Use Cases:**
- Security investigations
- Compliance auditing
- Performance monitoring
- Troubleshooting without risk of data modification

### 3. Full Write Access
```toml
[fleet]
readonly = false
```

**Available Tools:**
- All read-only tools
- All query execution tools (without SELECT validation)
- Create/update/delete operations for:
  - Hosts (`fleet_delete_host`, `fleet_transfer_hosts`)
  - Queries (`fleet_create_query`, `fleet_update_query`, `fleet_delete_query`)
  - Policies (`fleet_create_policy`, `fleet_update_policy`, `fleet_delete_policy`)
  - Scripts (`fleet_create_script`, `fleet_modify_script`, `fleet_delete_script`, `fleet_run_script`)
  - Teams (`fleet_create_team`, `fleet_update_team`, `fleet_delete_team`)
  - And more...

**⚠️ Important:**
- Use with caution - all Fleet operations are available
- Recommended to have LLM prompt for confirmation before making changes
- Consider using this mode only when necessary for administrative tasks

## Best Practices

### General
1. **Start with read-only mode** - Use strict read-only mode for exploration and monitoring
2. **Enable SELECT queries when needed** - Use read-only with SELECT queries for investigations
3. **Use specific targeting** - Target specific hosts instead of fleet-wide operations when possible
4. **Implement pagination** - Use pagination for large datasets to avoid overwhelming responses
5. **Use team filtering** - Scope operations to specific teams when appropriate

### Query Execution
1. **Test queries on one host first** - Use `fleet_query_host` to test queries before running fleet-wide
2. **Use table discovery tools** - Use `fleet_suggest_tables_for_query` to find the right tables
3. **Check schema overrides** - Use `fleet_get_osquery_table_schema` to see important usage notes
4. **Monitor query performance** - Optimize queries that take too long or return too much data
5. **Understand scheduled vs live queries**:
   - Use `fleet_get_query_report` for scheduled query results
   - Use `fleet_query_host` for immediate ad-hoc queries

### Script Management
1. **Validate before running** - Always validate script contents before running on production hosts
2. **Test on small sets** - Test scripts on a small set of hosts before rolling out fleet-wide
3. **Use batch operations** - Use `fleet_run_batch_script` for running scripts on multiple hosts
4. **Monitor execution** - Use `fleet_get_script_result` and `fleet_list_batch_script_hosts` to monitor results
5. **Use filters effectively** - Use filters for batch operations to target specific host groups

### Software & Vulnerability Management
1. **Use search tools** - Use `fleet_search_software` to quickly find software across the fleet
2. **Check specific hosts** - Use `fleet_find_software_on_host` to check software on specific hosts
3. **Monitor vulnerabilities** - Regularly check `fleet_get_vulnerabilities` for security issues
4. **Filter by criticality** - Use `known_exploit=true` to prioritize critical vulnerabilities
5. **Advanced filtering** - Combine multiple filters for precise vulnerability targeting:
   - Use `min_cvss_score` and `max_cvss_score` to filter by severity
   - Use `min_epss_probability` to focus on vulnerabilities likely to be exploited
   - Use `cve_published_after` and `cve_published_before` to find recent vulnerabilities
   - Use `description_keywords` to search for specific vulnerability types (e.g., "remote code execution")
6. **Optimize queries** - Server-side filters (`known_exploit`, `cve_search`) are applied first, then client-side filters refine the results
