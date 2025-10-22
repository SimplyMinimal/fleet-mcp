"""Dynamic osquery table discovery and schema management."""

import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx
import yaml

from ..client import FleetClient

logger = logging.getLogger(__name__)

# Official Fleet osquery schema URL
FLEET_SCHEMA_URL = "https://raw.githubusercontent.com/fleetdm/fleet/main/schema/osquery_fleet_schema.json"

# Fleet schema overrides base URL
FLEET_SCHEMA_OVERRIDES_BASE_URL = (
    "https://raw.githubusercontent.com/fleetdm/fleet/main/schema/tables"
)

# Cache directory and file
CACHE_DIR = Path.home() / ".fleet-mcp" / "cache"
SCHEMA_CACHE_FILE = CACHE_DIR / "osquery_fleet_schema.json"
SCHEMA_OVERRIDES_CACHE_FILE = CACHE_DIR / "osquery_schema_overrides.json"
SCHEMA_CACHE_TTL = 86400  # 24 hours in seconds
SCHEMA_OVERRIDES_CACHE_TTL = 86400  # 24 hours in seconds


class TableSchemaCache:
    """Multi-level cache for osquery table schemas.

    This cache manages:
    1. Fleet schemas (loaded from official JSON schema with 24-hour cache)
    2. Per-host table lists (cached with 1-hour TTL)
    3. Bundled fallback schemas (for offline operation)

    The official Fleet schema is downloaded from:
    https://raw.githubusercontent.com/fleetdm/fleet/main/schema/osquery_fleet_schema.json

    Caching behavior:
    - Schema is cached locally in ~/.fleet-mcp/cache/osquery_fleet_schema.json
    - Cache is valid for 24 hours
    - On cache miss or expiry, attempts to download fresh schema
    - Falls back to cached version if download fails
    - Falls back to bundled minimal schemas if no cache exists
    """

    def __init__(self) -> None:
        self.fleet_schemas: dict[str, dict[str, Any]] = {}
        self.host_tables: dict[str, list[dict[str, Any]]] = {}
        self.last_fetch: dict[str, float] = {}
        self.fleet_schemas_loaded = False
        self.cache_ttl = 3600  # 1 hour for host tables
        self.schema_cache_ttl = SCHEMA_CACHE_TTL  # 24 hours for Fleet schemas

        # Schema overrides from Fleet's YAML files
        self.schema_overrides: dict[str, dict[str, Any]] = {}
        self.overrides_loaded = False
        self.overrides_source: str | None = None  # "cache", "download", or None

        # Track loading status and errors
        self.schema_source: str | None = None  # "cache", "download", "bundled", or None
        self.loading_errors: list[str] = []  # List of error messages encountered
        self.loading_warnings: list[str] = []  # List of warning messages encountered

    async def initialize(self, force_refresh: bool = False) -> None:
        """Initialize the cache by loading Fleet schemas and overrides.

        Args:
            force_refresh: If True, force download of fresh schema even if cache is valid
        """
        if not self.fleet_schemas_loaded or force_refresh:
            await self._load_fleet_schemas(force_refresh=force_refresh)
            self.fleet_schemas_loaded = True

        # Load schema overrides (non-blocking - failures don't prevent schema loading)
        if not self.overrides_loaded or force_refresh:
            await self._load_schema_overrides(force_refresh=force_refresh)
            self.overrides_loaded = True

    async def _load_fleet_schemas(self, force_refresh: bool = False) -> None:
        """Load table schemas from Fleet's official JSON schema.

        This method implements a multi-tier loading strategy:
        1. Check local cache file (if valid and not force_refresh)
        2. Download fresh schema from GitHub
        3. Fall back to cached version if download fails
        4. Fall back to bundled minimal schemas if no cache exists

        Args:
            force_refresh: If True, skip cache and force download
        """
        logger.info("Loading Fleet table schemas...")

        # Clear previous errors/warnings
        self.loading_errors.clear()
        self.loading_warnings.clear()
        self.schema_source = None

        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Try to load from cache first (unless force_refresh)
        if not force_refresh and SCHEMA_CACHE_FILE.exists():
            cache_age = time.time() - SCHEMA_CACHE_FILE.stat().st_mtime
            if cache_age < self.schema_cache_ttl:
                try:
                    schemas = await self._load_cached_schema()
                    if schemas:
                        self.fleet_schemas = schemas
                        self.schema_source = "cache"
                        logger.info(
                            f"Loaded {len(schemas)} table schemas from cache "
                            f"(age: {cache_age/3600:.1f} hours)"
                        )
                        return
                except Exception as e:
                    error_msg = f"Failed to load cached schema: {e}"
                    logger.warning(error_msg)
                    self.loading_warnings.append(error_msg)

        # Try to download fresh schema
        try:
            schemas = await self._download_fleet_schema()
            if schemas:
                self.fleet_schemas = schemas
                self.schema_source = "download"
                # Save to cache
                await self._save_schema_cache(schemas)
                logger.info(
                    f"Downloaded and cached {len(schemas)} table schemas from Fleet"
                )
                return
        except Exception as e:
            error_msg = f"Failed to download Fleet schema: {e}"
            logger.warning(error_msg)
            self.loading_warnings.append(error_msg)

        # Fall back to cached version (even if expired)
        if SCHEMA_CACHE_FILE.exists():
            try:
                schemas = await self._load_cached_schema()
                if schemas:
                    self.fleet_schemas = schemas
                    self.schema_source = "cache_stale"
                    warning_msg = (
                        f"Using stale cached schema ({len(schemas)} tables) - "
                        "download failed"
                    )
                    logger.warning(warning_msg)
                    self.loading_warnings.append(warning_msg)
                    return
            except Exception as e:
                error_msg = f"Failed to load stale cache: {e}"
                logger.error(error_msg)
                self.loading_errors.append(error_msg)

        # Last resort: fall back to bundled schemas
        try:
            schemas = await self._load_bundled_schemas()
            self.fleet_schemas = schemas
            self.schema_source = "bundled"
            warning_msg = (
                f"Using bundled fallback schemas ({len(schemas)} tables) - "
                "no cache available"
            )
            logger.warning(warning_msg)
            self.loading_warnings.append(warning_msg)
        except Exception as e:
            error_msg = f"Failed to load bundled schemas: {e}"
            logger.error(error_msg)
            self.loading_errors.append(error_msg)
            self.fleet_schemas = {}
            self.schema_source = "none"

    async def _download_fleet_schema(self) -> dict[str, dict[str, Any]]:
        """Download the official Fleet osquery schema JSON file.

        Returns:
            Dictionary mapping table names to schema dictionaries
        """
        logger.debug(f"Downloading Fleet schema from {FLEET_SCHEMA_URL}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(FLEET_SCHEMA_URL)
            response.raise_for_status()

            # Parse JSON schema
            schema_json = response.json()

            # Convert to our internal format
            schemas = self._parse_fleet_json_schema(schema_json)

            return schemas

    async def _load_cached_schema(self) -> dict[str, dict[str, Any]]:
        """Load schema from local cache file.

        Returns:
            Dictionary mapping table names to schema dictionaries
        """
        logger.debug(f"Loading schema from cache: {SCHEMA_CACHE_FILE}")

        with open(SCHEMA_CACHE_FILE) as f:
            schema_json = json.load(f)

        # Convert to our internal format
        schemas = self._parse_fleet_json_schema(schema_json)

        return schemas

    async def _save_schema_cache(self, _schemas: dict[str, dict[str, Any]]) -> None:
        """Save schemas to local cache file.

        Note: We save the raw JSON format, not our internal format,
        to preserve all original data from Fleet.

        Args:
            _schemas: Schema dictionary (unused - we re-download to get raw JSON)
        """
        # We need to re-download to get the raw JSON
        # This is a bit inefficient but ensures we cache the original format
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(FLEET_SCHEMA_URL)
                response.raise_for_status()
                schema_json = response.json()

                with open(SCHEMA_CACHE_FILE, "w") as f:
                    json.dump(schema_json, f, indent=2)

                logger.debug(f"Saved schema cache to {SCHEMA_CACHE_FILE}")
        except Exception as e:
            logger.warning(f"Failed to save schema cache: {e}")

    def _parse_fleet_json_schema(
        self, schema_json: dict | list
    ) -> dict[str, dict[str, Any]]:
        """Parse Fleet's official JSON schema format into our internal format.

        The Fleet JSON schema is a list of table objects with the structure:
        [
          {
            "name": "table_name",
            "description": "...",
            "platforms": ["darwin", "linux", "windows"],
            "evented": false,
            "columns": [
              {
                "name": "column_name",
                "type": "TEXT",
                "description": "...",
                "required": false
              },
              ...
            ],
            "examples": "SELECT ... FROM table_name;",
            "notes": "..."
          },
          ...
        ]

        Args:
            schema_json: Parsed JSON data from Fleet schema file (list or dict)

        Returns:
            Dictionary mapping table names to schema dictionaries in our format
        """
        schemas = {}

        # Handle both list format (official schema) and dict format (legacy/test)
        if isinstance(schema_json, list):
            table_list = schema_json
        else:
            # Convert dict format to list format
            table_list = [{"name": name, **data} for name, data in schema_json.items()]

        for table_data in table_list:
            table_name = table_data.get("name")
            if not table_name:
                continue

            # Extract column information
            columns = []
            column_details = {}

            for col in table_data.get("columns", []):
                col_name = col.get("name", "")
                if col_name:
                    columns.append(col_name)
                    column_details[col_name] = {
                        "type": col.get("type", "TEXT"),
                        "description": col.get("description", ""),
                        "required": col.get("required", False),
                    }

            # Parse examples (can be string or list)
            examples_raw = table_data.get("examples", "")
            if isinstance(examples_raw, str):
                examples = [
                    ex.strip() for ex in examples_raw.strip().split("\n") if ex.strip()
                ]
            elif isinstance(examples_raw, list):
                examples = examples_raw
            else:
                examples = []

            schemas[table_name] = {
                "description": table_data.get("description", "").strip(),
                "platforms": table_data.get("platforms", []),
                "evented": table_data.get("evented", False),
                "columns": columns,
                "column_details": column_details,
                "examples": examples,
                "notes": (
                    table_data.get("notes", "").strip()
                    if table_data.get("notes")
                    else None
                ),
            }

        return schemas

    async def _load_schema_overrides(self, force_refresh: bool = False) -> None:
        """Load table schema overrides from Fleet's YAML files.

        This method implements a multi-tier loading strategy:
        1. Check local cache file (if valid and not force_refresh)
        2. Download fresh overrides from GitHub
        3. Fall back to cached version if download fails
        4. Continue gracefully if no overrides available

        Args:
            force_refresh: If True, skip cache and force download
        """
        logger.info("Loading Fleet table schema overrides...")

        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Try to load from cache first (unless force_refresh)
        if not force_refresh and SCHEMA_OVERRIDES_CACHE_FILE.exists():
            cache_age = time.time() - SCHEMA_OVERRIDES_CACHE_FILE.stat().st_mtime
            if cache_age < SCHEMA_OVERRIDES_CACHE_TTL:
                try:
                    overrides = await self._load_cached_overrides()
                    if overrides:
                        self.schema_overrides = overrides
                        self.overrides_source = "cache"
                        logger.info(
                            f"Loaded {len(overrides)} table overrides from cache "
                            f"(age: {cache_age/3600:.1f} hours)"
                        )
                        return
                except Exception as e:
                    logger.warning(f"Failed to load cached overrides: {e}")

        # Try to download fresh overrides
        try:
            overrides = await self._download_schema_overrides()
            if overrides:
                self.schema_overrides = overrides
                self.overrides_source = "download"
                # Save to cache
                await self._save_overrides_cache(overrides)
                logger.info(
                    f"Downloaded and cached {len(overrides)} table overrides from Fleet"
                )
                return
        except Exception as e:
            logger.warning(f"Failed to download schema overrides: {e}")

        # Fall back to cached version (even if expired)
        if SCHEMA_OVERRIDES_CACHE_FILE.exists():
            try:
                overrides = await self._load_cached_overrides()
                if overrides:
                    self.schema_overrides = overrides
                    self.overrides_source = "cache_stale"
                    logger.warning(
                        f"Using stale cached overrides ({len(overrides)} tables) - "
                        "download failed"
                    )
                    return
            except Exception as e:
                logger.warning(f"Failed to load stale override cache: {e}")

        # If we get here, no overrides are available - this is not fatal
        logger.info("No schema overrides available - continuing with base schemas")
        self.schema_overrides = {}
        self.overrides_source = "none"

    async def _download_schema_overrides(self) -> dict[str, dict[str, Any]]:
        """Download schema override YAML files from Fleet's GitHub repository.

        Returns:
            Dictionary mapping table names to override dictionaries
        """
        logger.debug(
            f"Downloading schema overrides from {FLEET_SCHEMA_OVERRIDES_BASE_URL}"
        )

        overrides = {}

        # Get list of tables we have schemas for
        table_names = list(self.fleet_schemas.keys())
        logger.debug(f"Attempting to download overrides for {len(table_names)} tables")

        async with httpx.AsyncClient(timeout=30.0) as client:
            for table_name in table_names:
                try:
                    # Construct URL for the YAML file
                    yaml_url = f"{FLEET_SCHEMA_OVERRIDES_BASE_URL}/{table_name}.yml"

                    response = await client.get(yaml_url)

                    # 404 is expected for tables without overrides
                    if response.status_code == 404:
                        continue

                    response.raise_for_status()

                    # Parse YAML
                    override_data = yaml.safe_load(response.text)
                    if override_data:
                        overrides[table_name] = override_data
                        logger.debug(f"Downloaded override for table: {table_name}")

                except httpx.HTTPStatusError as e:
                    if e.response.status_code != 404:
                        logger.debug(
                            f"Failed to download override for {table_name}: {e}"
                        )
                except Exception as e:
                    logger.debug(f"Error processing override for {table_name}: {e}")

        logger.info(f"Downloaded {len(overrides)} table overrides")
        return overrides

    async def _load_cached_overrides(self) -> dict[str, dict[str, Any]]:
        """Load schema overrides from local cache file.

        Returns:
            Dictionary mapping table names to override dictionaries
        """
        logger.debug(f"Loading overrides from cache: {SCHEMA_OVERRIDES_CACHE_FILE}")

        with open(SCHEMA_OVERRIDES_CACHE_FILE) as f:
            overrides_json: dict[str, dict[str, Any]] = json.load(f)

        return overrides_json

    async def _save_overrides_cache(self, overrides: dict[str, dict[str, Any]]) -> None:
        """Save schema overrides to local cache file.

        Args:
            overrides: Dictionary of table overrides to cache
        """
        try:
            with open(SCHEMA_OVERRIDES_CACHE_FILE, "w") as f:
                json.dump(overrides, f, indent=2)

            logger.debug(f"Saved overrides cache to {SCHEMA_OVERRIDES_CACHE_FILE}")
        except Exception as e:
            logger.warning(f"Failed to save overrides cache: {e}")

    async def _load_bundled_schemas(self) -> dict[str, dict[str, Any]]:
        """Load bundled fallback schemas.

        Returns:
            Dictionary mapping table names to schema dictionaries
        """
        # Minimal set of critical tables for offline fallback
        return {
            "rpm_packages": {
                "description": "RPM packages installed on RHEL/CentOS/Fedora systems",
                "platforms": ["linux"],
                "evented": False,
                "columns": [
                    "name",
                    "version",
                    "release",
                    "arch",
                    "epoch",
                    "install_time",
                    "vendor",
                ],
                "column_details": {},
                "examples": [
                    "SELECT name, version FROM rpm_packages WHERE name = 'platform-python';"
                ],
                "notes": "Use version_compare() function with 'RHEL' flavor for version comparisons",
            },
            "processes": {
                "description": "All running processes on the host system",
                "platforms": ["darwin", "linux", "windows"],
                "evented": False,
                "columns": ["pid", "name", "path", "cmdline", "state", "uid", "gid"],
                "column_details": {},
                "examples": [
                    "SELECT pid, name, cmdline FROM processes WHERE name = 'chrome';"
                ],
                "notes": None,
            },
        }

    async def get_tables_for_host(
        self, client: FleetClient, host_id: int, platform: str
    ) -> list[dict[str, Any]]:
        """Get enriched table list for a specific host.

        Args:
            client: Fleet API client
            host_id: Host ID to query
            platform: Host platform (darwin, linux, windows, chrome)

        Returns:
            List of enriched table dictionaries
        """
        cache_key = f"{host_id}_{platform}"
        now = time.time()

        # Check cache
        if cache_key in self.host_tables:
            last_fetch = self.last_fetch.get(cache_key, 0)
            if now - last_fetch < self.cache_ttl:
                logger.debug(f"Returning cached tables for host {host_id}")
                return self.host_tables[cache_key]

        # Cache miss or expired: discover tables
        logger.info(f"Discovering tables on host {host_id} (platform: {platform})")

        try:
            tables = await self._discover_tables_on_host(client, host_id, platform)

            # Cache the result
            self.host_tables[cache_key] = tables
            self.last_fetch[cache_key] = now

            return tables

        except Exception as e:
            logger.error(f"Failed to discover tables on host {host_id}: {e}")

            # Return cached data if available, even if expired
            if cache_key in self.host_tables:
                logger.warning(f"Returning stale cached data for host {host_id}")
                return self.host_tables[cache_key]

            # Last resort: return Fleet schemas filtered by platform
            return self._get_fleet_schemas_by_platform(platform)

    async def _discover_tables_on_host(
        self, client: FleetClient, host_id: int, platform: str
    ) -> list[dict[str, Any]]:
        """Discover tables on a live host and enrich with Fleet metadata.

        Args:
            client: Fleet API client
            host_id: Host ID to query
            platform: Host platform

        Returns:
            List of enriched table dictionaries
        """
        # Import here to avoid circular dependency
        # We'll use the client directly instead of the tool function

        # Step 1: Get list of all tables from osquery_registry
        registry_query = (
            "SELECT name FROM osquery_registry WHERE registry = 'table' ORDER BY name;"
        )

        # Execute query using client (use the simpler /hosts/{id}/query endpoint)
        async with client:
            query_response = await client.post(
                f"/hosts/{host_id}/query", json_data={"query": registry_query}
            )

            if not query_response.success:
                raise Exception(
                    f"Failed to query osquery_registry: {query_response.message}"
                )

            if not query_response.data:
                raise Exception("No data returned from query")

            rows = query_response.data.get("rows", [])

        table_names = [row["name"] for row in rows]
        logger.info(f"Discovered {len(table_names)} tables on host {host_id}")

        # Step 2: Create table list (we'll skip detailed schema for now for performance)
        # The schema will come from Fleet metadata enrichment
        tables_with_schema = []

        for table_name in table_names:
            tables_with_schema.append(
                {
                    "name": table_name,
                    "columns": [],  # Will be filled from Fleet metadata
                    "column_details": {},
                    "platform": platform,
                }
            )

        # Step 3: Enrich with Fleet metadata
        enriched_tables = []

        for table in tables_with_schema:
            name = table["name"]

            if name in self.fleet_schemas:
                # Known table: merge with Fleet metadata
                fleet_schema = self.fleet_schemas[name]

                enriched = {
                    **table,
                    "description": fleet_schema.get("description", ""),
                    "platforms": fleet_schema.get("platforms", [platform]),
                    "evented": fleet_schema.get("evented", False),
                    "examples": fleet_schema.get("examples", []),
                    "notes": fleet_schema.get("notes"),
                    "is_custom": False,
                    "metadata_source": "fleet_repository",
                    # Copy columns from Fleet schema
                    "columns": fleet_schema.get("columns", []),
                    "column_details": fleet_schema.get("column_details", {}),
                }

                # Merge schema overrides
                enriched = self._merge_overrides_with_schema(name, enriched)

                enriched_tables.append(enriched)
            else:
                # Custom/unknown table
                enriched_tables.append(
                    {
                        **table,
                        "description": f"Custom or extension table: {name}",
                        "platforms": [platform],
                        "evented": False,
                        "examples": [],
                        "notes": "This table was discovered on the host but is not in Fleet's schema repository. It may be from an osquery extension.",
                        "is_custom": True,
                        "metadata_source": "live_discovery_only",
                    }
                )

        return enriched_tables

    def _merge_overrides_with_schema(
        self, table_name: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge schema override data with base schema.

        Args:
            table_name: Name of the table
            schema: Base schema dictionary

        Returns:
            Merged schema with override data
        """
        merged = dict(schema)

        if table_name in self.schema_overrides:
            override = self.schema_overrides[table_name]

            # Add override notes prominently
            if "notes" in override:
                merged["override_notes"] = override["notes"]

            # Add override examples
            if "examples" in override:
                merged["override_examples"] = override["examples"]

            # Mark that this table has overrides
            merged["has_overrides"] = True
            merged["override_source"] = "fleet_yaml"

        return merged

    def _get_fleet_schemas_by_platform(self, platform: str) -> list[dict[str, Any]]:
        """Get Fleet schemas filtered by platform (fallback method).

        Args:
            platform: Platform to filter by

        Returns:
            List of table dictionaries
        """
        tables = []

        for name, schema in self.fleet_schemas.items():
            if platform in schema.get("platforms", []):
                merged_schema = self._merge_overrides_with_schema(name, schema)
                tables.append(
                    {
                        "name": name,
                        **merged_schema,
                        "is_custom": False,
                        "metadata_source": "fleet_repository_only",
                    }
                )

        return tables

    def invalidate_host(self, host_id: int) -> None:
        """Invalidate cache for a specific host.

        Args:
            host_id: Host ID to invalidate
        """
        keys_to_remove = [
            k for k in self.host_tables.keys() if k.startswith(f"{host_id}_")
        ]
        for key in keys_to_remove:
            del self.host_tables[key]
            if key in self.last_fetch:
                del self.last_fetch[key]

        logger.info(f"Invalidated cache for host {host_id}")

    async def refresh_fleet_schemas(self) -> bool:
        """Force refresh of Fleet schemas from GitHub.

        This bypasses the cache and downloads a fresh copy of the schema.
        Useful for getting the latest table definitions.

        Returns:
            True if refresh was successful, False otherwise
        """
        try:
            await self._load_fleet_schemas(force_refresh=True)
            return True
        except Exception as e:
            logger.error(f"Failed to refresh Fleet schemas: {e}")
            return False

    def get_cache_info(self) -> dict[str, Any]:
        """Get information about the current cache state.

        Returns:
            Dictionary with cache statistics and metadata
        """
        cache_exists = SCHEMA_CACHE_FILE.exists()
        cache_age = None
        cache_size = None

        if cache_exists:
            cache_age = time.time() - SCHEMA_CACHE_FILE.stat().st_mtime
            cache_size = SCHEMA_CACHE_FILE.stat().st_size

        # Detect potential issues
        table_count = len(self.fleet_schemas)
        warnings = list(self.loading_warnings)  # Copy the list

        # Add warning if table count is unexpectedly low
        if table_count > 0 and table_count < 50:
            warnings.append(
                f"Low table count ({table_count} tables) - expected 100+ tables. "
                "Cache may be incomplete or using test data."
            )

        # Add warning if no schemas loaded at all
        if table_count == 0 and self.fleet_schemas_loaded:
            warnings.append(
                "No schemas loaded - all loading attempts failed. "
                "Check network connectivity and cache file."
            )

        # Get override cache info
        overrides_cache_exists = SCHEMA_OVERRIDES_CACHE_FILE.exists()
        overrides_cache_age = None
        overrides_cache_size = None

        if overrides_cache_exists:
            overrides_cache_age = (
                time.time() - SCHEMA_OVERRIDES_CACHE_FILE.stat().st_mtime
            )
            overrides_cache_size = SCHEMA_OVERRIDES_CACHE_FILE.stat().st_size

        return {
            "schema_cache_file": str(SCHEMA_CACHE_FILE),
            "cache_exists": cache_exists,
            "cache_age_seconds": cache_age,
            "cache_age_hours": cache_age / 3600 if cache_age else None,
            "cache_size_bytes": cache_size,
            "cache_ttl_seconds": self.schema_cache_ttl,
            "cache_ttl_hours": self.schema_cache_ttl / 3600,
            "is_cache_valid": (
                cache_age < self.schema_cache_ttl if cache_age else False
            ),
            "loaded_schemas_count": table_count,
            "cached_hosts_count": len(self.host_tables),
            "schema_source": self.schema_source,
            "loading_errors": list(self.loading_errors),  # Copy the list
            "loading_warnings": warnings,
            # Override cache info
            "overrides_cache_file": str(SCHEMA_OVERRIDES_CACHE_FILE),
            "overrides_cache_exists": overrides_cache_exists,
            "overrides_cache_age_seconds": overrides_cache_age,
            "overrides_cache_age_hours": (
                overrides_cache_age / 3600 if overrides_cache_age else None
            ),
            "overrides_cache_size_bytes": overrides_cache_size,
            "loaded_overrides_count": len(self.schema_overrides),
            "overrides_source": self.overrides_source,
        }


# Global cache instance
_table_cache: TableSchemaCache | None = None


async def get_table_cache() -> TableSchemaCache:
    """Get or create the global table schema cache.

    Returns:
        TableSchemaCache instance
    """
    global _table_cache

    if _table_cache is None:
        _table_cache = TableSchemaCache()
        await _table_cache.initialize()

    return _table_cache
