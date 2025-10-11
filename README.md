# Fleet MCP

A Model Context Protocol (MCP) server that enables AI assistants to interact with [Fleet Device Management](https://fleetdm.com) for device management, security monitoring, and compliance enforcement.

## Features

- **Host Management**: List, search, query, and manage hosts across your fleet
- **Live Query Execution**: Run osquery queries in real-time against hosts
- **Policy Management**: Create, update, and monitor compliance policies
- **Software Inventory**: Track software installations and vulnerabilities across devices
- **Team & User Management**: Organize hosts and users into teams
- **Osquery Table Discovery**: Dynamic discovery and documentation of osquery tables
- **Read-Only Mode**: Safe exploration with optional SELECT-only query execution
- **Activity Monitoring**: Track Fleet activities and audit logs

## Installation

### From PyPI (when published)
```bash
pip install fleet-mcp
```

### From Source
```bash
git clone https://github.com/SimplyMinimal/fleet-mcp.git
cd fleet-mcp
pip install -e .
```

### Using uv (recommended for development)
```bash
git clone https://github.com/SimplyMinimal/fleet-mcp.git
cd fleet-mcp
uv sync --dev
```

## Quick Start

### 1. Initialize Configuration
```bash
fleet-mcp init-config
```

This creates a `fleet-mcp.toml` configuration file. Edit it with your Fleet server details:

```toml
[fleet]
server_url = "https://your-fleet-instance.com"
api_token = "your-api-token"
readonly = true  # Safe default - enables read-only mode
allow_select_queries = false  # Set to true to allow SELECT queries
```

### 2. Test Connection
```bash
fleet-mcp test
```

### 3. Run the MCP Server
```bash
fleet-mcp run
```

### 4. Use with Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "fleet": {
      "command": "fleet-mcp",
      "args": ["run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true"
      }
    }
  }
}
```

## Available Tools

Fleet MCP provides 40+ tools organized into the following categories:

### Host Management (Read-Only)
- `fleet_list_hosts` - List hosts with filtering, pagination, and search
- `fleet_get_host` - Get detailed information about a specific host by ID
- `fleet_get_host_by_identifier` - Get host by hostname, UUID, or hardware serial
- `fleet_search_hosts` - Search hosts by hostname, UUID, serial number, or IP
- `fleet_get_host_software` - Get software installed on a specific host

### Host Management (Write Operations)
- `fleet_delete_host` - Remove a host from Fleet
- `fleet_transfer_hosts` - Transfer hosts to a different team
- `fleet_query_host` - Run an ad-hoc live query against a specific host
- `fleet_query_host_by_identifier` - Run a live query by hostname/UUID/serial

### Query Management (Read-Only)
- `fleet_list_queries` - List all saved queries with pagination
- `fleet_get_query` - Get details of a specific saved query
- `fleet_get_query_report` - Get the latest results from a scheduled query

### Query Management (Write Operations)
- `fleet_create_query` - Create a new saved query
- `fleet_delete_query` - Delete a saved query
- `fleet_run_live_query` - Execute a live query against specified hosts
- `fleet_run_saved_query` - Run a saved query against hosts

### Policy Management (Read-Only)
- `fleet_list_policies` - List all compliance policies
- `fleet_get_policy_results` - Get compliance results for a specific policy

### Policy Management (Write Operations)
- `fleet_create_policy` - Create a new compliance policy
- `fleet_update_policy` - Update an existing policy
- `fleet_delete_policy` - Delete a policy

### Software & Vulnerabilities (Read-Only)
- `fleet_list_software` - List software inventory across the fleet
- `fleet_get_software` - Get detailed information about a specific software item
- `fleet_search_software` - Search for software by name
- `fleet_find_software_on_host` - Find specific software on a host by hostname
- `fleet_get_host_software` - Get software installed on a specific host
- `fleet_get_vulnerabilities` - List known vulnerabilities with filtering

### Team & User Management (Read-Only)
- `fleet_list_teams` - List all teams
- `fleet_get_team` - Get details of a specific team
- `fleet_list_users` - List all users with filtering
- `fleet_get_user` - Get details of a specific user
- `fleet_list_activities` - List Fleet activities and audit logs

### Team Management (Write Operations)
- `fleet_create_team` - Create a new team

### Osquery Table Discovery & Reference
- `fleet_list_osquery_tables` - List available osquery tables with dynamic discovery
- `fleet_get_osquery_table_schema` - Get detailed schema for a specific table
- `fleet_suggest_tables_for_query` - Get AI-powered table suggestions based on intent

### System
- `fleet_health_check` - Check Fleet server connectivity and authentication

## Configuration

Fleet MCP can be configured via environment variables, configuration file, or command-line arguments.

### Configuration File (Recommended)

Create a `fleet-mcp.toml` file:

```toml
[fleet]
# Fleet server URL (required)
server_url = "https://your-fleet-instance.com"

# Fleet API token (required)
api_token = "your-api-token"

# Verify SSL certificates (default: true)
verify_ssl = true

# Request timeout in seconds (default: 30)
timeout = 30

# Maximum retries for failed requests (default: 3)
max_retries = 3

# Read-only mode - disables write operations (default: true)
readonly = true

# Allow SELECT-only queries in read-only mode (default: false)
# When true, enables fleet_run_live_query, fleet_query_host, etc. with validation
allow_select_queries = false
```

### Environment Variables

All configuration options can be set via environment variables with the `FLEET_` prefix:

- `FLEET_SERVER_URL` - Fleet server URL (required)
- `FLEET_API_TOKEN` - API authentication token (required)
- `FLEET_VERIFY_SSL` - Verify SSL certificates (default: `true`)
- `FLEET_TIMEOUT` - Request timeout in seconds (default: `30`)
- `FLEET_MAX_RETRIES` - Maximum retries for failed requests (default: `3`)
- `FLEET_READONLY` - Enable read-only mode (default: `true`)
- `FLEET_ALLOW_SELECT_QUERIES` - Allow SELECT-only queries in read-only mode (default: `false`)

Environment variables override configuration file settings.

### Command-Line Arguments

```bash
fleet-mcp --server-url https://fleet.example.com --api-token YOUR_TOKEN run
```

Available options:
- `--config, -c` - Path to configuration file
- `--server-url` - Fleet server URL
- `--api-token` - Fleet API token
- `--readonly` - Enable read-only mode
- `--verbose, -v` - Enable verbose logging

## Read-Only Mode

Fleet MCP runs in **read-only mode by default** to provide a safe way to explore and monitor your Fleet instance without risk of making changes.

### Three Operational Modes

#### 1. Strict Read-Only Mode (Default)
**Configuration:** `readonly=true`, `allow_select_queries=false`

- ✅ View hosts, queries, policies, software, teams, users
- ✅ Get query reports from scheduled queries
- ✅ List vulnerabilities and software inventory
- ✅ View activity logs
- ❌ No query execution (even SELECT queries)
- ❌ No create, update, or delete operations

**Best for:** Safe exploration and monitoring without any risk

#### 2. Read-Only with SELECT Queries
**Configuration:** `readonly=true`, `allow_select_queries=true`

- ✅ All read-only mode features
- ✅ Run SELECT-only queries against hosts (`fleet_query_host`, `fleet_query_host_by_identifier`)
- ✅ Execute live SELECT queries (`fleet_run_live_query`)
- ✅ Run saved queries with SELECT validation (`fleet_run_saved_query`)
- ✅ All queries are validated to ensure they're SELECT-only
- ❌ No INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, or other data modification
- ❌ No create, update, or delete operations on Fleet resources

**Best for:** Active monitoring and investigation while maintaining safety

**Query Validation:** All queries are automatically validated before execution. Queries containing data modification keywords (INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, REPLACE, MERGE) are rejected with a clear error message.

#### 3. Full Write Mode
**Configuration:** `readonly=false`

- ✅ All read operations
- ✅ All query execution (no validation)
- ✅ Create, update, and delete queries
- ✅ Create, update, and delete policies
- ✅ Create teams
- ✅ Delete and transfer hosts

**Best for:** Full Fleet management with AI assistance

⚠️ **Use with caution** - AI can make changes to your Fleet instance

### Configuration Examples

#### Example 1: Strict Read-Only (Default)
```toml
[fleet]
server_url = "https://fleet.example.com"
api_token = "your-token"
readonly = true
allow_select_queries = false
```

#### Example 2: Read-Only with SELECT Queries
```toml
[fleet]
server_url = "https://fleet.example.com"
api_token = "your-token"
readonly = true
allow_select_queries = true
```

#### Example 3: Full Write Access
```toml
[fleet]
server_url = "https://fleet.example.com"
api_token = "your-token"
readonly = false
```

### Claude Desktop Configuration Examples

#### Read-Only with SELECT Queries
```json
{
  "mcpServers": {
    "fleet": {
      "command": "fleet-mcp",
      "args": ["run"],
      "env": {
        "FLEET_SERVER_URL": "https://fleet.example.com",
        "FLEET_API_TOKEN": "your-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  }
}
```

#### Full Write Access
```json
{
  "mcpServers": {
    "fleet": {
      "command": "fleet-mcp",
      "args": ["run"],
      "env": {
        "FLEET_SERVER_URL": "https://fleet.example.com",
        "FLEET_API_TOKEN": "your-token",
        "FLEET_READONLY": "false"
      }
    }
  }
}
```

## CLI Commands

Fleet MCP provides several CLI commands for managing the server:

### `fleet-mcp run`
Start the MCP server.

```bash
fleet-mcp run
fleet-mcp --config custom-config.toml run
fleet-mcp --verbose run
```

### `fleet-mcp test`
Test connection to Fleet server.

```bash
fleet-mcp test
fleet-mcp --config custom-config.toml test
```

### `fleet-mcp init-config`
Create a configuration file template.

```bash
fleet-mcp init-config
fleet-mcp init-config --output my-config.toml
```

### `fleet-mcp version`
Show version information.

```bash
fleet-mcp version
```

### Global Options
- `--config, -c PATH` - Path to configuration file
- `--verbose, -v` - Enable verbose logging
- `--server-url URL` - Fleet server URL (overrides config)
- `--api-token TOKEN` - Fleet API token (overrides config)
- `--readonly` - Enable read-only mode (overrides config)

## Usage Examples

### Example 1: List All Hosts
```python
# In Claude Desktop or any MCP client
"List all hosts in the fleet"
```

### Example 2: Find Software on a Host
```python
"What version of Chrome is installed on host-123?"
```

### Example 3: Run a Query
```python
# With allow_select_queries=true
"Run a query to find all processes listening on port 80"
```

### Example 4: Check Compliance
```python
"Show me which hosts are failing the disk encryption policy"
```

### Example 5: Discover Osquery Tables
```python
"What osquery tables are available for monitoring network connections?"
```

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and development workflows.

### Setup Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SimplyMinimal/fleet-mcp.git
   cd fleet-mcp
   ```

2. **Install dependencies** (uv will automatically create a virtual environment):
   ```bash
   uv sync --dev
   ```

3. **Run tests**:
   ```bash
   uv run pytest
   uv run pytest -v  # Verbose output
   uv run pytest tests/unit  # Unit tests only
   uv run pytest tests/integration  # Integration tests only
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
   uv run ruff check --fix src tests  # Auto-fix issues
   ```

7. **Run the CLI**:
   ```bash
   uv run fleet-mcp run
   uv run fleet-mcp test
   ```

### Adding Dependencies

- **Runtime dependencies**: `uv add package-name`
- **Development dependencies**: `uv add --group dev package-name`

### Project Structure

```
fleet-mcp/
├── src/fleet_mcp/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── client.py           # Fleet API client
│   ├── config.py           # Configuration management
│   ├── server.py           # MCP server implementation
│   ├── tools/              # MCP tool implementations
│   │   ├── host_tools.py
│   │   ├── query_tools.py
│   │   ├── query_tools_readonly.py
│   │   ├── policy_tools.py
│   │   ├── software_tools.py
│   │   ├── team_tools.py
│   │   ├── table_tools.py
│   │   └── table_discovery.py
│   └── utils/
│       └── sql_validator.py
├── tests/
│   ├── unit/
│   └── integration/
├── pyproject.toml
└── README.md
```

## Troubleshooting

### Connection Issues

**Problem:** "Failed to connect to Fleet server"

**Solutions:**
- Verify `FLEET_SERVER_URL` is correct and accessible
- Check that `FLEET_API_TOKEN` is valid
- If using self-signed certificates, set `verify_ssl = false` in config
- Test connection with `fleet-mcp test`

### Authentication Issues

**Problem:** "Authentication failed" or "401 Unauthorized"

**Solutions:**
- Verify your API token is correct
- Check token hasn't expired
- Ensure token has appropriate permissions
- Generate a new token from Fleet UI: My account → Get API token

### Query Validation Errors

**Problem:** "Query validation failed" when running queries

**Solutions:**
- Ensure `allow_select_queries = true` in configuration
- Verify query is SELECT-only (no INSERT, UPDATE, DELETE, etc.)
- Check query syntax is valid osquery SQL

### Tool Not Available

**Problem:** Tool like `fleet_create_query` not available

**Solutions:**
- Check if read-only mode is enabled (`readonly = true`)
- Write operations require `readonly = false`
- Some tools require `allow_select_queries = true`

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Format code (`uv run black src tests && uv run isort src tests`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Fleet Device Management](https://fleetdm.com) - The open-source device management platform
- [Model Context Protocol](https://modelcontextprotocol.io) - The protocol enabling AI-application integration
- [osquery](https://osquery.io) - The SQL-powered operating system instrumentation framework

## Support & Resources

- **Documentation**: [GitHub README](https://github.com/SimplyMinimal/fleet-mcp#readme)
- **Issues**: [GitHub Issues](https://github.com/SimplyMinimal/fleet-mcp/issues)
- **Fleet Documentation**: [Fleet DM Docs](https://fleetdm.com/docs)
- **MCP Documentation**: [MCP Specification](https://modelcontextprotocol.io)
- **osquery Documentation**: [osquery Schema](https://osquery.io/schema/)

## Related Projects

- [Fleet DM](https://github.com/fleetdm/fleet) - Open-source device management
- [osquery](https://github.com/osquery/osquery) - SQL-powered system instrumentation
- [MCP Servers](https://github.com/modelcontextprotocol/servers) - Official MCP server implementations

## Disclaimer

This project is not affiliated with or endorsed by Fleet DM. It is an independent implementation of the Model Context Protocol for interacting with Fleet DM instances.
