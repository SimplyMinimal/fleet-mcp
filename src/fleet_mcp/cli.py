"""Command-line interface for Fleet MCP."""

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
    help="Path to configuration file"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging"
)
@click.option(
    "--server-url",
    envvar="FLEET_SERVER_URL",
    help="Fleet server URL"
)
@click.option(
    "--api-token",
    envvar="FLEET_API_TOKEN",
    help="Fleet API token"
)
@click.option(
    "--readonly",
    envvar="FLEET_READONLY",
    is_flag=True,
    help="Enable read-only mode (disables write operations)"
)
@click.pass_context
def cli(
    ctx: click.Context,
    config: Path | None,
    verbose: bool,
    server_url: str | None,
    api_token: str | None,
    readonly: bool
) -> None:
    """Fleet MCP - Model Context Protocol tool for Fleet DM integration."""
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
            fleet_config = load_config(default_config if default_config.exists() else None)

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
        click.echo(f"Starting Fleet MCP Server for {config.server_url}{readonly_status}")
        server.run()
    except KeyboardInterrupt:
        click.echo("\nShutting down Fleet MCP Server...")
    except Exception as e:
        click.echo(f"Error running server: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
async def test(ctx: click.Context) -> None:
    """Test connection to Fleet server."""
    config = _load_config(ctx)

    try:
        from .client import FleetClient

        async with FleetClient(config) as client:
            response = await client.health_check()

            if response.success:
                click.echo(f"✅ Successfully connected to Fleet server at {config.server_url}")
                click.echo("   Authentication: OK")
            else:
                click.echo(f"❌ Failed to connect to Fleet server: {response.message}")
                sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Connection test failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="fleet-mcp.toml",
    help="Output configuration file path"
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
            if not click.confirm(f"Configuration file {output} already exists. Overwrite?"):
                click.echo("Configuration file creation cancelled.")
                return

        output.write_text(config_template)
        click.echo(f"✅ Configuration template created at {output}")
        click.echo("Please edit the file and add your Fleet server URL and API token.")

    except Exception as e:
        click.echo(f"❌ Failed to create configuration file: {e}", err=True)
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
