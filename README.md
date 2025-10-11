# Fleet MCP

A Model Context Protocol (MCP) tool that enables agentic AIs to interact with [Fleet DM](https://fleetdm.com) instances for device management, security monitoring, and compliance enforcement.

## Features

- **Host Management**: List, search, and manage hosts across your fleet
- **Query Execution**: Create and run osquery queries for real-time data collection
- **Policy Enforcement**: Define and monitor compliance policies
- **Software Inventory**: Track software installations and vulnerabilities
- **Team Management**: Organize hosts and users into teams
- **Security Monitoring**: Monitor activities and security events

## Installation

### Using pip
```bash
pip install fleet-mcp
```

### Using uv (recommended for development)
```bash
uv add fleet-mcp
```

## Quick Start

1. **Configure Fleet Connection**:
   ```bash
   export FLEET_SERVER_URL="https://your-fleet-instance.com"
   export FLEET_API_TOKEN="your-api-token"
   ```

2. **Run the MCP Server**:
   ```bash
   fleet-mcp
   ```

3. **Use with Claude Desktop** (add to your MCP configuration):
   ```json
   {
     "mcpServers": {
       "fleet": {
         "command": "fleet-mcp",
         "env": {
           "FLEET_SERVER_URL": "https://your-fleet-instance.com",
           "FLEET_API_TOKEN": "your-api-token"
         }
       }
     }
   }
   ```

## Available Tools

### Host Management
- `fleet_list_hosts` - List all hosts with filtering options
- `fleet_get_host` - Get detailed information about a specific host
- `fleet_search_hosts` - Search hosts by various criteria
- `fleet_delete_host` - Remove a host from Fleet
- `fleet_query_host` - Run an ad-hoc live query against a specific host
- `fleet_query_host_by_identifier` - Run an ad-hoc live query by identifier

### Query Management
- `fleet_list_queries` - List all saved queries
- `fleet_create_query` - Create a new saved query
- `fleet_run_live_query` - Execute a live query against hosts
- `fleet_get_query_report` - Get results from a scheduled query

### Policy Management
- `fleet_list_policies` - List all policies
- `fleet_create_policy` - Create a new compliance policy
- `fleet_get_policy_results` - Get policy compliance results

### Software & Vulnerabilities
- `fleet_list_software` - Get software inventory across the fleet
- `fleet_get_vulnerabilities` - List known vulnerabilities
- `fleet_get_host_software` - Get software installed on specific host

### Team & User Management
- `fleet_list_teams` - List all teams
- `fleet_list_users` - List all users
- `fleet_create_team` - Create a new team

### Osquery Table Reference
- `fleet_list_osquery_tables` - List all available osquery tables with filtering
- `fleet_get_osquery_table_schema` - Get detailed schema for a specific table
- `fleet_suggest_tables_for_query` - Get table suggestions based on query intent

## Configuration

Fleet MCP can be configured via environment variables or a configuration file:

### Environment Variables
- `FLEET_SERVER_URL` - Fleet server URL (required)
- `FLEET_API_TOKEN` - API authentication token (required)
- `FLEET_VERIFY_SSL` - Verify SSL certificates (default: true)
- `FLEET_TIMEOUT` - Request timeout in seconds (default: 30)
- `FLEET_READONLY` - Enable read-only mode (default: false)

### Configuration File
Create a `fleet-mcp.toml` file:

```toml
[fleet]
server_url = "https://your-fleet-instance.com"
api_token = "your-api-token"
verify_ssl = true
timeout = 30
readonly = false
```

## Read-Only Mode

Fleet MCP supports a read-only mode that disables all write operations, providing a safe way to explore and monitor your Fleet instance without risk of making changes.

### Enabling Read-Only Mode

**Environment Variable:**
```bash
export FLEET_READONLY=true
fleet-mcp run
```

**Configuration File:**
```toml
[fleet]
readonly = true
```

**Command Line:**
```bash
fleet-mcp --readonly run
```

**Claude Desktop Configuration:**
```json
{
  "mcpServers": {
    "fleet-readonly": {
      "command": "fleet-mcp",
      "args": ["--readonly", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### Available Operations in Read-Only Mode

When read-only mode is enabled, only the following operations are available:

**Host Management:**
- List hosts with filtering and search
- Get detailed host information
- Search hosts by identifier

**Query Management:**
- List saved queries
- Get query details
- Get query execution results

**Policy Management:**
- List policies
- Get policy compliance results

**Software & Vulnerabilities:**
- List software inventory
- Get vulnerability information
- Search for software packages

**Team & User Management:**
- List teams and users
- Get team/user details
- View activity logs

**Disabled Operations:**
- Creating, updating, or deleting queries
- Creating, updating, or deleting policies
- Creating teams
- Deleting hosts or transferring between teams
- Running live queries

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and development workflows.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fleet-mcp/fleet-mcp.git
   cd fleet-mcp
   ```

2. **Install dependencies** (uv will automatically create a virtual environment):
   ```bash
   uv sync --dev
   ```

3. **Run tests**:
   ```bash
   uv run pytest
   ```

4. **Format code**:
   ```bash
   uv run black src tests
   uv run isort src tests
   ```

5. **Type checking**:
   ```bash
   uv run mypy src
   ```

6. **Linting**:
   ```bash
   uv run ruff check src tests
   ```

7. **Run the CLI**:
   ```bash
   uv run fleet-mcp
   ```

### Adding Dependencies

- **Runtime dependencies**: `uv add package-name`
- **Development dependencies**: `uv add --group dev package-name`

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

For security issues, please see our [Security Policy](SECURITY.md).

## Support

- [Documentation](https://github.com/fleet-mcp/fleet-mcp#readme)
- [Issues](https://github.com/fleet-mcp/fleet-mcp/issues)
- [Fleet DM Documentation](https://fleetdm.com/docs)
