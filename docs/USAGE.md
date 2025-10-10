# Fleet MCP Usage Guide

This guide provides comprehensive instructions for using the Fleet MCP tool to interact with Fleet DM instances.

## Installation

### From PyPI (when published)
```bash
pip install fleet-mcp
```

### From Source
```bash
git clone https://github.com/fleet-mcp/fleet-mcp.git
cd fleet-mcp
pip install -e .
```

## Configuration

Fleet MCP requires configuration of your Fleet server URL and API token. There are several ways to provide this configuration:

### 1. Environment Variables (Recommended)

Set the following environment variables:

```bash
export FLEET_SERVER_URL="https://your-fleet-instance.com"
export FLEET_API_TOKEN="your-api-token"
export FLEET_VERIFY_SSL="true"  # Optional, default: true
export FLEET_TIMEOUT="30"       # Optional, default: 30 seconds
```

### 2. Configuration File

Create a TOML configuration file:

```bash
fleet-mcp init-config --output fleet-mcp.toml
```

Edit the generated file:

```toml
[fleet]
server_url = "https://your-fleet-instance.com"
api_token = "your-api-token"
verify_ssl = true
timeout = 30
max_retries = 3
```

### 3. Command Line Arguments

```bash
fleet-mcp --server-url "https://your-fleet-instance.com" --api-token "your-token" run
```

### Getting Your API Token

1. Log into your Fleet UI
2. Go to "My account" (click your profile in top right)
3. Click "Get API token"
4. Copy the token

**Note**: For SSO/MFA users, the API token can only be retrieved from the UI, not via API login.

## Running the MCP Server

### Basic Usage

```bash
fleet-mcp run
```

### With Custom Configuration

```bash
fleet-mcp --config /path/to/config.toml run
```

### Testing Connection

Before running the server, test your connection:

```bash
fleet-mcp test
```

## Integration with Claude Desktop

Add Fleet MCP to your Claude Desktop configuration:

### macOS/Linux
Edit `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fleet": {
      "command": "fleet-mcp",
      "args": ["run"],
      "env": {
        "FLEET_SERVER_URL": "https://your-fleet-instance.com",
        "FLEET_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### Windows
Edit `%APPDATA%\Claude\claude_desktop_config.json` with the same content.

## Available Tools

Once connected, you can use these tools through Claude or other MCP clients:

### Host Management
- `fleet_list_hosts` - List all hosts with filtering
- `fleet_get_host` - Get detailed host information
- `fleet_search_hosts` - Search hosts by criteria
- `fleet_get_host_by_identifier` - Find host by hostname/UUID/serial
- `fleet_delete_host` - Remove a host from Fleet
- `fleet_transfer_hosts` - Move hosts between teams

### Query Management
- `fleet_list_queries` - List saved queries
- `fleet_create_query` - Create new saved query
- `fleet_run_live_query` - Execute live query on hosts
- `fleet_run_saved_query` - Run existing saved query
- `fleet_get_query_results` - Get query execution results
- `fleet_get_query` - Get query details
- `fleet_delete_query` - Delete a saved query

### Policy Management
- `fleet_list_policies` - List compliance policies
- `fleet_create_policy` - Create new policy
- `fleet_get_policy_results` - Get policy compliance results
- `fleet_update_policy` - Modify existing policy
- `fleet_delete_policy` - Delete a policy

### Software & Vulnerabilities
- `fleet_list_software` - Get software inventory
- `fleet_get_software` - Get software details
- `fleet_get_host_software` - Get software on specific host
- `fleet_get_vulnerabilities` - List vulnerabilities
- `fleet_search_software` - Search for software

### Team & User Management
- `fleet_list_teams` - List all teams
- `fleet_create_team` - Create new team
- `fleet_get_team` - Get team details
- `fleet_list_users` - List users
- `fleet_get_user` - Get user details
- `fleet_list_activities` - Get audit logs

### System Tools
- `fleet_health_check` - Test server connectivity

## Example Conversations with Claude

### Host Management
```
"Show me all hosts that are currently offline"
"Find the host with hostname 'laptop-001'"
"List all macOS hosts in the Engineering team"
"Get detailed information about host ID 123"
```

### Security Monitoring
```
"Show me all hosts with critical policy failures"
"List all software with known vulnerabilities"
"Find hosts running outdated versions of Chrome"
"Show me recent security activities in the fleet"
```

### Query Operations
```
"Create a query to find all running processes named 'chrome'"
"Run a live query to check disk usage on all hosts"
"Show me the results from query campaign 456"
"List all saved queries related to security"
```

### Policy Compliance
```
"Create a policy to ensure firewall is enabled on macOS"
"Show me which hosts are failing the encryption policy"
"List all critical policies and their compliance status"
"Update the password policy to require 12 characters"
```

## Troubleshooting

### Connection Issues

1. **Authentication Failed**
   - Verify your API token is correct
   - Check if token has expired
   - Ensure you have proper permissions

2. **Connection Timeout**
   - Check your Fleet server URL
   - Verify network connectivity
   - Increase timeout in configuration

3. **SSL Certificate Errors**
   - For development: set `FLEET_VERIFY_SSL=false`
   - For production: ensure valid SSL certificate

### Common Error Messages

- **"Fleet server URL is required"**: Set `FLEET_SERVER_URL` environment variable
- **"Fleet API token is required"**: Set `FLEET_API_TOKEN` environment variable
- **"Authentication failed"**: Check your API token and permissions
- **"Resource not found"**: Verify the host/query/policy ID exists

### Debug Mode

Enable verbose logging:

```bash
fleet-mcp --verbose run
```

### Getting Help

```bash
fleet-mcp --help
fleet-mcp run --help
```

## Security Considerations

1. **API Token Security**
   - Store tokens securely (environment variables, not in code)
   - Rotate tokens regularly
   - Use least-privilege access

2. **Network Security**
   - Always use HTTPS in production
   - Consider VPN for remote access
   - Monitor API access logs

3. **Audit Trail**
   - All actions are logged in Fleet's activity feed
   - Review activities regularly
   - Set up alerts for sensitive operations

## Performance Tips

1. **Query Optimization**
   - Use specific host targeting instead of fleet-wide queries
   - Limit result sets with appropriate filters
   - Monitor query execution times

2. **Rate Limiting**
   - Fleet MCP respects API rate limits
   - Use pagination for large datasets
   - Batch operations when possible

3. **Caching**
   - Host information is cached briefly
   - Refresh data when needed for real-time accuracy
