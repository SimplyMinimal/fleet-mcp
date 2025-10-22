"""Command-line interface for Fleet MCP."""

import asyncio
import logging
import sys
from pathlib import Path

import click

from .config import FleetConfig, get_default_config_file, load_config
from .server import FleetMCPServer


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--server-url", envvar="FLEET_SERVER_URL", help="Fleet server URL")
@click.option("--api-token", envvar="FLEET_API_TOKEN", help="Fleet API token")
@click.option(
    "--readonly",
    envvar="FLEET_READONLY",
    is_flag=True,
    help="Enable read-only mode (disables write operations)",
)
@click.pass_context
def cli(
    ctx: click.Context,
    config: Path | None,
    verbose: bool,
    server_url: str | None,
    api_token: str | None,
    readonly: bool,
) -> None:
    """Fleet MCP - Model Context Protocol tool for Fleet DM integration."""
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Store config parameters in context for commands that need them
    ctx.ensure_object(dict)
    ctx.obj["config_file"] = config
    ctx.obj["server_url"] = server_url
    ctx.obj["api_token"] = api_token
    ctx.obj["readonly"] = readonly
    ctx.obj["verbose"] = verbose


def _load_config(ctx: click.Context) -> FleetConfig:
    """Load configuration from context parameters."""
    config_file = ctx.obj["config_file"]
    server_url = ctx.obj["server_url"]
    api_token = ctx.obj["api_token"]
    readonly = ctx.obj["readonly"]

    try:
        if config_file:
            fleet_config = load_config(config_file)
        else:
            default_config = get_default_config_file()
            fleet_config = load_config(
                default_config if default_config.exists() else None
            )

        # Override with CLI arguments if provided
        config_data = fleet_config.model_dump()
        if server_url:
            config_data["server_url"] = server_url
        if api_token:
            config_data["api_token"] = api_token
        if readonly:
            config_data["readonly"] = readonly

        return FleetConfig(**config_data)

    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def run(ctx: click.Context) -> None:
    """Run the Fleet MCP server."""
    config = _load_config(ctx)

    try:
        server = FleetMCPServer(config)
        readonly_status = " (READ-ONLY MODE)" if config.readonly else ""
        click.echo(
            f"Starting Fleet MCP Server for {config.server_url}{readonly_status}"
        )
        server.run()
    except KeyboardInterrupt:
        click.echo("\nShutting down Fleet MCP Server...")
    except Exception as e:
        click.echo(f"Error running server: {e}", err=True)
        sys.exit(1)


async def _run_connection_test(config: FleetConfig) -> None:
    """Run the actual connection test (async helper)."""
    from .client import FleetClient

    async with FleetClient(config) as client:
        response = await client.health_check()

        if response.success:
            click.echo("   Status: ✅ Connected")
            click.echo("   Authentication: ✅ Successful")
            click.echo()
            click.echo("=" * 50)
            click.echo("Connection test passed. Fleet MCP is ready to use.")
            click.echo()
        else:
            click.echo("   Status: ❌ Failed")
            click.echo(f"   Error: {response.message}")
            click.echo()
            click.echo("=" * 50)
            click.echo("❌ Connection test failed.")
            click.echo()
            click.echo("Troubleshooting tips:")
            click.echo("  • Verify your Fleet server URL is correct")
            click.echo("  • Check that your API token is valid")
            click.echo("  • Ensure the Fleet server is accessible from your network")
            click.echo(
                "  • Check if SSL verification needs to be disabled (verify_ssl = false)"
            )
            sys.exit(1)


@cli.command()
@click.pass_context
def test(ctx: click.Context) -> None:
    """Test connection to Fleet server."""
    click.echo("Fleet MCP Connection Test")
    click.echo("=" * 50)
    click.echo()

    # Step 1: Configuration validation
    click.echo("* Configuration Validation")
    click.echo("-" * 50)

    # Determine config source
    config_file = ctx.obj.get("config_file") if ctx.obj else None
    if config_file:
        config_source = f"Config file: {config_file}"
    else:
        default_config = get_default_config_file()
        if default_config.exists():
            config_source = f"Config file: {default_config}"
        else:
            config_source = "Environment variables"

    click.echo(f"   Source: {config_source}")

    try:
        config = _load_config(ctx)
        click.echo("   Status: Valid")
        click.echo()

        # Step 2: Display connection details
        click.echo("* Connection Details")
        click.echo("-" * 50)
        click.echo(f"   Fleet Server: {config.server_url}")
        click.echo(
            f"   SSL Verification: {'Enabled' if config.verify_ssl else 'Disabled'}"
        )
        click.echo(f"   Timeout: {config.timeout}s")
        click.echo(f"   Max Retries: {config.max_retries}")
        click.echo()

        # Step 3: Display mode configuration
        click.echo("* Mode Configuration")
        click.echo("-" * 50)
        if config.readonly:
            click.echo("   Mode: Read-Only")
            if config.allow_select_queries:
                click.echo("   SELECT Queries: Enabled")
            else:
                click.echo("   SELECT Queries: Disabled")
        else:
            click.echo("   Mode: ⚠️  Full Write Access")
        click.echo()

        # Step 4: Test connection
        click.echo("* Connection Test")
        click.echo("-" * 50)
        click.echo(f"   Testing connection to {config.server_url}...")

    except Exception as e:
        click.echo("   Status: Invalid")
        click.echo(f"   Error: {e}")
        click.echo()
        click.echo("Configuration validation failed. Please check your configuration.")
        sys.exit(1)

    # Perform actual connection test
    try:
        asyncio.run(_run_connection_test(config))

    except Exception as e:
        click.echo("   Status: Failed")
        click.echo(f"   Error: {e}")
        click.echo()
        click.echo("=" * 50)
        click.echo("Connection test failed.")
        click.echo()
        click.echo("Troubleshooting tips:")
        click.echo("  • Verify your Fleet server URL is correct")
        click.echo("  • Check that your API token is valid")
        click.echo("  • Ensure the Fleet server is accessible from your network")
        click.echo(
            "  • Check if SSL verification needs to be disabled (verify_ssl = false)"
        )
        click.echo(f"  • Error details: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="fleet-mcp.toml",
    help="Output configuration file path",
)
def init_config(output: Path) -> None:
    """Initialize a configuration file template."""
    config_template = """[fleet]
# Fleet server URL (required)
server_url = "https://your-fleet-instance.com"

# Fleet API token (required)
# Get this from Fleet UI: My account > Get API token
api_token = "your-api-token-here"

# Verify SSL certificates (default: true)
verify_ssl = true

# Request timeout in seconds (default: 30)
timeout = 30

# Maximum number of retries for failed requests (default: 3)
max_retries = 3
"""

    try:
        if output.exists():
            if not click.confirm(
                f"Configuration file {output} already exists. Overwrite?"
            ):
                click.echo("Configuration file creation cancelled.")
                return

        output.write_text(config_template)
        click.echo(f"Configuration template created at {output}")
        click.echo("Please edit the file and add your Fleet server URL and API token.")

    except Exception as e:
        click.echo(f"!! Failed to create configuration file: {e}", err=True)
        sys.exit(1)


@cli.command()
def version() -> None:
    """Show version information."""
    from . import __version__

    click.echo(f"Fleet MCP version {__version__}")


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
