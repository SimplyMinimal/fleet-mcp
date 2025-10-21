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


## Quick Start
Just want to dive right in? This will set up fleet-mcp with read-only access and SELECT query execution enabled. Just replace the `FLEET_SERVER_URL` and `FLEET_API_TOKEN` with your own.
```json
{
  "mcpServers": {
    "fleet": {
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  }
}
```

See the [Available Tools](#available-tools) section below for a complete list of tools.

---
<!-- 
<details>
<summary><b>Local Installation</b></summary>

### From PyPI
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
</details> -->

<!-- ### 1. Initialize Configuration
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
``` -->

## MCP Client Configuration

Fleet MCP can be integrated with various MCP-compatible clients. Below are configuration examples for popular clients.

### Prerequisites

Before configuring any MCP client, ensure you have:

1. **Install `uv`** (recommended) or `pip`:
   ```bash
   # Install uv (recommended)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Or use pip
   pip install fleet-mcp
   ```

2. **Fleet API Token**: Generate an API token from your Fleet instance:  
   Option 1) 
   - Log into Fleet UI
   - Navigate to: My account → Get API token
   - Copy the token for use in configuration

   Option 2)
   - Create an API-Only user with `fleetctl`
   ```bash
   # Generate an API-Only User and get the token
   fleetctl user create --name Fleet-MCP --email <email> --password <password> --role admin --api-only
   ```

   > **Note**: This API token and your fleet instance URL (https://your-fleet-instance.com) will be used in the client configuration.

3. **Pick Your Client**: Choose your preferred AI assistant client and follow the corresponding setup instructions below.

<details>
<summary><b>Install in Claude Desktop</b></summary>

#### Configuration File Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Configuration

```json
{
  "mcpServers": {
    "fleet": {
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  }
}
```

> **Note:** Replace `uvx` with `fleet-mcp` if you've installed the package globally. For enhanced security, use `--config` flag to reference a TOML file instead of embedding tokens (see [Security Best Practices](#security-best-practices)).

</details>

<details>
<summary><b>Install in Cursor</b></summary>

Go to: `Settings` → `Cursor Settings` → `MCP` → `Add new global MCP server`

Install globally in `~/.cursor/mcp.json` or per-project in `.cursor/mcp.json`. See [Cursor MCP docs](https://docs.cursor.com/context/model-context-protocol) for more info.

```json
{
  "mcpServers": {
    "fleet": {
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  }
}
```

</details>

<details>
<summary><b>Install in Cline (VS Code Extension)</b></summary>

**Config Location:** `~/.cline/mcp_settings.json` (macOS/Linux) or `%USERPROFILE%\.cline\mcp_settings.json` (Windows)

Alternatively: VS Code Settings → Search "Cline: MCP Settings" → Edit JSON

```json
{
  "mcpServers": {
    "fleet": {
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  }
}
```

</details>

<details>
<summary><b>Install in Continue (VS Code Extension)</b></summary>

**Config Location:** `~/.continue/config.json`

```json
{
  "mcpServers": [
    {
      "name": "fleet",
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  ]
}
```

</details>

<details>
<summary><b>Install in Zed Editor</b></summary>

**Config Location:** `~/.config/zed/settings.json` (macOS/Linux) or `%APPDATA%\Zed\settings.json` (Windows)

```json
{
  "context_servers": {
    "fleet": {
      "command": {
        "path": "uvx",
        "args": ["fleet-mcp", "run"]
      },
      "settings": {
        "env": {
          "FLEET_SERVER_URL": "https://your-fleet-instance.com",
          "FLEET_API_TOKEN": "your-api-token",
          "FLEET_READONLY": "true",
          "FLEET_ALLOW_SELECT_QUERIES": "true"
        }
      }
    }
  }
}
```

</details>

<details>
<summary><b>Install in Windsurf</b></summary>

See [Windsurf MCP docs](https://docs.windsurf.com/windsurf/cascade/mcp) for more info.

```json
{
  "mcpServers": {
    "fleet": {
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  }
}
```

</details>

<details>
<summary><b>Install in VS Code</b></summary>

See [VS Code MCP docs](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) for more info.

```json
"mcp": {
  "servers": {
    "fleet": {
      "type": "stdio",
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  }
}
```

</details>

<details>
<summary><b>Install in Sourcegraph Cody</b></summary>

**Config Location:** `~/Library/Application Support/Cody/mcp_settings.json` (macOS), `%APPDATA%\Cody\mcp_settings.json` (Windows), or `~/.config/Cody/mcp_settings.json` (Linux)

```json
{
  "mcpServers": {
    "fleet": {
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  }
}
```

</details>

<details>
<summary><b>Install in Augment Code</b></summary>

**Via UI:** Hamburger menu → Settings → Tools → + Add MCP → Enter `uvx fleet-mcp run` → Name: "Fleet" → Add

**Manual Config:** Settings → Advanced → Edit settings.json

```json
"augment.advanced": {
  "mcpServers": [
    {
      "name": "fleet",
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  ]
}
```

</details>

<details>
<summary><b>Install in LM Studio</b></summary>

Navigate to `Program` → `Install` → `Edit mcp.json`. See [LM Studio MCP Support](https://lmstudio.ai/blog/lmstudio-v0.3.17).

```json
{
  "mcpServers": {
    "fleet": {
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  }
}
```

</details>

<details>
<summary><b>Generic MCP Client Configuration</b></summary>

For other MCP-compatible clients, use this general pattern:

```json
{
  "mcpServers": {
    "fleet": {
      "command": "uvx",
      "args": ["fleet-mcp", "run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token",
        "FLEET_READONLY": "true",
        "FLEET_ALLOW_SELECT_QUERIES": "true"
      }
    }
  }
}
```

</details>

### Configuration Options Reference

| Environment Variable | Description | Default | Required |
|---------------------|-------------|---------|----------|
| `FLEET_SERVER_URL` | Fleet server URL | - | ✅ |
| `FLEET_API_TOKEN` | Fleet API token | - | ✅ |
| `FLEET_READONLY` | Enable read-only mode | `true` | ❌ |
| `FLEET_ALLOW_SELECT_QUERIES` | Allow SELECT queries in read-only mode | `false` | ❌ |
| `FLEET_VERIFY_SSL` | Verify SSL certificates | `true` | ❌ |
| `FLEET_TIMEOUT` | Request timeout (seconds) | `30` | ❌ |
| `FLEET_MAX_RETRIES` | Maximum request retries | `3` | ❌ |

> **Note:** All clients above use the same environment variables. Replace `uvx` with `fleet-mcp` if installed globally.

### Security Best Practices

1. **Use Config Files**: Store tokens in TOML files: `"args": ["fleet-mcp", "--config", "~/.config/fleet-mcp.toml", "run"]`
2. **File Permissions**: `chmod 600 ~/.config/fleet-mcp.toml`
3. **Read-Only Mode**: Start with `FLEET_READONLY=true` (default)
4. **Token Rotation**: Regularly rotate Fleet API tokens
5. **Environment-Specific Configs**: Use separate configs for dev/prod

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
- `fleet_run_live_query` - Execute a live query against specified hosts (no results)
- `fleet_query_hosts_batch` ⭐ - Run a query against multiple hosts concurrently with results
- `fleet_query_hosts_aggregate` - Run a query and return aggregated results (count, unique, stats)
- `fleet_query_hosts_smart` - Smart query with automatic host filtering and sampling
- `fleet_query_hosts_paginated` - Query hosts in pages to avoid memory issues
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

Fleet MCP supports three configuration methods (in order of precedence):

1. **Command-line arguments** (highest priority)
2. **Environment variables** (with `FLEET_` prefix)
3. **Configuration file** (recommended for security)

### Configuration File (Recommended)

Create `fleet-mcp.toml`:

```toml
[fleet]
server_url = "https://your-fleet-instance.com"  # Required
api_token = "your-api-token"                     # Required
verify_ssl = true                                # Default: true
timeout = 30                                     # Default: 30 seconds
max_retries = 3                                  # Default: 3
readonly = true                                  # Default: true
allow_select_queries = false                     # Default: false
```

### Environment Variables

See [Configuration Options Reference](#configuration-options-reference) for all available variables. Environment variables use the `FLEET_` prefix and override config file settings.

### Command-Line Arguments

```bash
fleet-mcp --server-url https://fleet.example.com --api-token YOUR_TOKEN run
```

Options: `--config`, `--server-url`, `--api-token`, `--readonly`, `--verbose`

## Read-Only Mode

Fleet MCP runs in **read-only mode by default** for safe exploration without risk of changes.

### Three Operational Modes

| Mode | Config | Capabilities | Best For |
|------|--------|--------------|----------|
| **Strict Read-Only** (Default) | `readonly=true`<br>`allow_select_queries=false` | ✅ View all resources<br>❌ No query execution<br>❌ No modifications | Safe exploration |
| **Read-Only + SELECT** | `readonly=true`<br>`allow_select_queries=true` | ✅ View all resources<br>✅ Run SELECT queries<br>❌ No modifications | Active monitoring |
| **Full Write** | `readonly=false` | ✅ All operations<br>⚠️ AI can modify Fleet | Full management |

### Configuration Examples

```toml
# Strict Read-Only (Default)
[fleet]
readonly = true
allow_select_queries = false
```
```toml
# Read-Only with SELECT Queries
[fleet]
readonly = true
allow_select_queries = true
```
```toml
# Full Write Access (⚠️ Use with caution) - Recommended to have LLM prompt for confirmation before making changes
[fleet]
readonly = false
```

## CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `run` | Start MCP server | `fleet-mcp run` |
| `test` | Test Fleet connection | `fleet-mcp test` |
| `init-config` | Create config template | `fleet-mcp init-config` |
| `version` | Show version | `fleet-mcp version` |

**Global Options:** `--config`, `--verbose`, `--server-url`, `--api-token`, `--readonly`

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
<details>
<summary><b>Development Setup</b></summary>

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Setup

```bash
git clone https://github.com/SimplyMinimal/fleet-mcp.git
cd fleet-mcp
uv sync --dev
```

### Common Tasks

| Task | Command |
|------|---------|
| Run tests | `uv run pytest` |
| Format code | `uv run black src tests && uv run isort src tests` |
| Type check | `uv run mypy src` |
| Lint | `uv run ruff check src tests` |
| Add dependency | `uv add package-name` |
| Add dev dependency | `uv add --group dev package-name` |

### Project Structure

```
src/fleet_mcp/
├── cli.py              # Command-line interface
├── client.py           # Fleet API client
├── config.py           # Configuration management
├── server.py           # MCP server implementation
├── tools/              # MCP tool implementations
└── utils/              # Utilities (SQL validator, etc.)
```
</details>

## Troubleshooting

<details>
<summary><b>Server Not Appearing in Client</b></summary>

1. Validate JSON syntax in config file
2. Restart the MCP client
3. Check client logs for errors
4. Verify `uvx` or `fleet-mcp` is in PATH: `which uvx`

</details>

<details>
<summary><b>Connection Errors</b></summary>

1. Test manually: `uvx fleet-mcp test`
2. Verify `FLEET_SERVER_URL` is accessible
3. Check `FLEET_API_TOKEN` is valid
4. For self-signed certs: `FLEET_VERIFY_SSL=false`

</details>

<details>
<summary><b>Authentication Failed (401)</b></summary>

1. Verify API token is correct
2. Check token hasn't expired
3. Ensure token has appropriate permissions
4. Generate new token: Fleet UI → My account → Get API token

</details>

<details>
<summary><b>Query Validation Failed</b></summary>

1. Set `FLEET_ALLOW_SELECT_QUERIES=true`
2. Ensure query is SELECT-only (no INSERT, UPDATE, DELETE, etc.)
3. Verify osquery SQL syntax is valid

</details>

<details>
<summary><b>Tool Not Available</b></summary>

- Write operations require `FLEET_READONLY=false`
- Query execution requires `FLEET_ALLOW_SELECT_QUERIES=true`
- Check tool availability in current mode

</details>

## Licensing

Fleet MCP uses a **dual-use licensing model**:

- **Free for Development & Testing**: Use Fleet MCP without restrictions for local development, testing, evaluation, and non-commercial purposes
- **Commercial License Required for Production**: Any production deployment or commercial use requires a registered commercial license

### Quick Reference

| Scenario | License Required |
|----------|------------------|
| Local development | ❌ No |
| Testing & evaluation | ❌ No |
| Commercial testing (14 days max) | ❌ No |
| Production deployment | ✅ Yes |
| Commercial services | ✅ Yes |

### Learn More

For detailed information about licensing, including:
- When a license is required vs. optional
- Examples of development vs. production use
- How to obtain a commercial license
- Frequently asked questions

See the [LICENSING.md](LICENSING.md) file.

## Disclaimer

This project is not affiliated with or endorsed by Fleet DM. It is an independent implementation of the Model Context Protocol for interacting with [Fleet](https://fleetdm.com) instances.
