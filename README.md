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

```bash
pip install fleet-mcp
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

### Query Management
- `fleet_list_queries` - List all saved queries
- `fleet_create_query` - Create a new saved query
- `fleet_run_live_query` - Execute a live query against hosts
- `fleet_get_query_results` - Get results from a query execution

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

## Configuration

Fleet MCP can be configured via environment variables or a configuration file:

### Environment Variables
- `FLEET_SERVER_URL` - Fleet server URL (required)
- `FLEET_API_TOKEN` - API authentication token (required)
- `FLEET_VERIFY_SSL` - Verify SSL certificates (default: true)
- `FLEET_TIMEOUT` - Request timeout in seconds (default: 30)

### Configuration File
Create a `fleet-mcp.toml` file:

```toml
[fleet]
server_url = "https://your-fleet-instance.com"
api_token = "your-api-token"
verify_ssl = true
timeout = 30
```

## Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fleet-mcp/fleet-mcp.git
   cd fleet-mcp
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Run tests**:
   ```bash
   pytest
   ```

4. **Format code**:
   ```bash
   black src tests
   isort src tests
   ```

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
