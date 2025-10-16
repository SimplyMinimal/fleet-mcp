"""Configuration management for Fleet MCP."""

import os
import sys
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore[assignment]


class FleetConfig(BaseSettings):
    """Configuration for Fleet DM connection."""

    server_url: str = Field(
        ..., description="Fleet server URL (e.g., https://fleet.example.com)"
    )

    api_token: str = Field(..., description="Fleet API token for authentication")

    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")

    timeout: int = Field(default=30, description="Request timeout in seconds")

    max_retries: int = Field(
        default=3, description="Maximum number of retries for failed requests"
    )

    user_agent: str = Field(
        default="fleet-mcp/0.1.0", description="User agent string for API requests"
    )

    readonly: bool = Field(
        default=True, description="Enable read-only mode (disables write operations)"
    )

    allow_select_queries: bool = Field(
        default=False,
        description="Allow SELECT-only queries in read-only mode (enables fleet_run_live_query, fleet_run_saved_query, fleet_query_host with validation)",
    )

    @field_validator("server_url")
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        """Validate and normalize server URL."""
        if not v:
            raise ValueError("Fleet server URL is required")

        # Remove trailing slash
        v = v.rstrip("/")

        # Ensure it starts with http:// or https://
        if not v.startswith(("http://", "https://")):
            v = f"https://{v}"

        return v

    @field_validator("api_token")
    @classmethod
    def validate_api_token(cls, v: str) -> str:
        """Validate API token."""
        if not v:
            raise ValueError("Fleet API token is required")

        if len(v) < 10:
            raise ValueError("Fleet API token appears to be too short")

        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout value."""
        if v <= 0:
            raise ValueError("Timeout must be positive")

        if v > 300:  # 5 minutes
            raise ValueError("Timeout cannot exceed 300 seconds")

        return v

    model_config = {"env_prefix": "FLEET_", "case_sensitive": False}


def load_config(config_file: Path | None = None) -> FleetConfig:
    """Load configuration from environment variables and optional config file.

    Args:
        config_file: Optional path to configuration file

    Returns:
        FleetConfig instance

    Raises:
        ValueError: If required configuration is missing or invalid
    """
    # If we have a config file, load it and merge with environment
    if config_file and config_file.exists():
        if tomllib is None:
            raise ImportError("TOML support requires Python 3.11+ or 'tomli' package")

        with open(config_file, "rb") as f:
            file_config = tomllib.load(f)

        # Get fleet config section
        file_data = file_config.get("fleet", {})

        # Create a new config with file data as defaults and env as overrides
        config_data = {}

        # Start with file data
        for key, value in file_data.items():
            config_data[key] = value

        # Override with environment variables if they exist
        for key in config_data.keys():
            env_var_name = f"FLEET_{key.upper()}"
            if env_var_name in os.environ:
                env_value = os.environ[env_var_name]
                # Convert string values to appropriate types
                if key in [
                    "verify_ssl",
                    "readonly",
                    "allow_select_queries",
                ] and isinstance(env_value, str):
                    config_data[key] = env_value.lower() in ("true", "1", "yes", "on")
                elif key in ["timeout", "max_retries"] and isinstance(env_value, str):
                    config_data[key] = int(env_value)
                else:
                    config_data[key] = env_value

        return FleetConfig.model_validate(config_data)

    # No config file, try to create from environment variables only
    # BaseSettings will automatically load from FLEET_* environment variables
    return FleetConfig.model_validate({})


def get_default_config_file() -> Path:
    """Get the default configuration file path."""
    # Check current directory first
    current_dir_config = Path("fleet-mcp.toml")
    if current_dir_config.exists():
        return current_dir_config

    # Check user home directory
    home_config = Path.home() / ".fleet-mcp.toml"
    if home_config.exists():
        return home_config

    # Check XDG config directory
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        xdg_config = Path(xdg_config_home) / "fleet-mcp" / "config.toml"
        if xdg_config.exists():
            return xdg_config

    # Default XDG location
    default_xdg = Path.home() / ".config" / "fleet-mcp" / "config.toml"
    return default_xdg
