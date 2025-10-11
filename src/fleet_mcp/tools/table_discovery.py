"""Dynamic osquery table discovery and schema management."""

import asyncio
import logging
import time
from typing import Any

import httpx
import yaml

from ..client import FleetClient

logger = logging.getLogger(__name__)


class TableSchemaCache:
    """Multi-level cache for osquery table schemas.
    
    This cache manages:
    1. Fleet schemas (loaded once at startup from GitHub)
    2. Per-host table lists (cached with 1-hour TTL)
    3. Bundled fallback schemas (for offline operation)
    """
    
    def __init__(self):
        self.fleet_schemas: dict[str, dict[str, Any]] = {}
        self.host_tables: dict[str, list[dict[str, Any]]] = {}
        self.last_fetch: dict[str, float] = {}
        self.fleet_schemas_loaded = False
        self.cache_ttl = 3600  # 1 hour
        
    async def initialize(self):
        """Initialize the cache by loading Fleet schemas."""
        if not self.fleet_schemas_loaded:
            await self._load_fleet_schemas()
            self.fleet_schemas_loaded = True
    
    async def _load_fleet_schemas(self):
        """Load table schemas from Fleet's GitHub repository."""
        logger.info("Loading Fleet table schemas from GitHub...")
        
        try:
            # Try to fetch from GitHub
            schemas = await self._fetch_from_github()
            if schemas:
                self.fleet_schemas = schemas
                logger.info(f"Loaded {len(schemas)} table schemas from Fleet GitHub")
                return
        except Exception as e:
            logger.warning(f"Failed to fetch Fleet schemas from GitHub: {e}")
        
        # Fall back to bundled schemas
        try:
            schemas = await self._load_bundled_schemas()
            self.fleet_schemas = schemas
            logger.info(f"Loaded {len(schemas)} bundled table schemas")
        except Exception as e:
            logger.error(f"Failed to load bundled schemas: {e}")
            self.fleet_schemas = {}
    
    async def _fetch_from_github(self) -> dict[str, dict[str, Any]]:
        """Fetch table schemas from Fleet's GitHub repository.
        
        Returns:
            Dictionary mapping table names to schema dictionaries
        """
        base_url = "https://api.github.com/repos/fleetdm/fleet/contents/schema/tables"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get list of schema files
            response = await client.get(base_url)
            response.raise_for_status()
            files = response.json()
            
            schemas = {}

            # Fetch each YAML file (limit to avoid rate limits)
            # GitHub API allows 60 requests/hour for unauthenticated, 5000 for authenticated
            # We'll fetch up to 200 schemas (most important ones)
            yaml_files = [f for f in files if f['name'].endswith('.yml')][:200]
            
            for file_info in yaml_files:
                try:
                    table_name = file_info['name'].replace('.yml', '')
                    
                    # Fetch the YAML content
                    yaml_response = await client.get(file_info['download_url'])
                    yaml_response.raise_for_status()
                    
                    # Parse YAML
                    schema_data = yaml.safe_load(yaml_response.text)
                    
                    # Convert to our format
                    schemas[table_name] = self._parse_fleet_schema(schema_data)
                    
                except Exception as e:
                    logger.debug(f"Failed to fetch schema for {file_info['name']}: {e}")
                    continue
            
            return schemas
    
    async def _load_bundled_schemas(self) -> dict[str, dict[str, Any]]:
        """Load bundled fallback schemas.
        
        Returns:
            Dictionary mapping table names to schema dictionaries
        """
        # For now, return a minimal set of critical tables
        # In production, this would load from a bundled JSON/YAML file
        return {
            "rpm_packages": {
                "description": "RPM packages installed on RHEL/CentOS/Fedora systems",
                "platforms": ["linux"],
                "evented": False,
                "columns": ["name", "version", "release", "arch", "epoch", "install_time", "vendor"],
                "examples": [
                    "SELECT name, version FROM rpm_packages WHERE name = 'platform-python';"
                ],
                "notes": "Use version_compare() function with 'RHEL' flavor for version comparisons"
            },
            "processes": {
                "description": "All running processes on the host system",
                "platforms": ["darwin", "linux", "windows"],
                "evented": False,
                "columns": ["pid", "name", "path", "cmdline", "state", "uid", "gid"],
                "examples": [
                    "SELECT pid, name, cmdline FROM processes WHERE name = 'chrome';"
                ],
                "notes": None
            },
        }
    
    def _parse_fleet_schema(self, yaml_data: dict) -> dict[str, Any]:
        """Parse Fleet's YAML schema format into our internal format.
        
        Args:
            yaml_data: Parsed YAML data from Fleet schema file
            
        Returns:
            Schema dictionary in our internal format
        """
        columns = []
        column_details = {}
        
        if 'columns' in yaml_data:
            for col in yaml_data['columns']:
                col_name = col.get('name', '')
                columns.append(col_name)
                column_details[col_name] = {
                    'type': col.get('type', 'TEXT'),
                    'description': col.get('description', ''),
                    'required': col.get('required', False)
                }
        
        return {
            'description': yaml_data.get('description', '').strip(),
            'platforms': yaml_data.get('platforms', []),
            'evented': yaml_data.get('evented', False),
            'columns': columns,
            'column_details': column_details,
            'examples': yaml_data.get('examples', '').strip().split('\n') if yaml_data.get('examples') else [],
            'notes': yaml_data.get('notes', '').strip() if yaml_data.get('notes') else None,
        }
    
    async def get_tables_for_host(
        self, 
        client: FleetClient,
        host_id: int, 
        platform: str
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
        self,
        client: FleetClient,
        host_id: int,
        platform: str
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
        registry_query = "SELECT name FROM osquery_registry WHERE registry = 'table' ORDER BY name;"

        # Execute query using client (use the simpler /hosts/{id}/query endpoint)
        async with client:
            query_response = await client.post(
                f"/hosts/{host_id}/query",
                json_data={"query": registry_query}
            )

            if not query_response.success:
                raise Exception(f"Failed to query osquery_registry: {query_response.message}")

            if not query_response.data:
                raise Exception("No data returned from query")

            rows = query_response.data.get("rows", [])

        table_names = [row['name'] for row in rows]
        logger.info(f"Discovered {len(table_names)} tables on host {host_id}")

        # Step 2: Create table list (we'll skip detailed schema for now for performance)
        # The schema will come from Fleet metadata enrichment
        tables_with_schema = []

        for table_name in table_names:
            tables_with_schema.append({
                'name': table_name,
                'columns': [],  # Will be filled from Fleet metadata
                'column_details': {},
                'platform': platform,
            })
        
        # Step 3: Enrich with Fleet metadata
        enriched_tables = []
        
        for table in tables_with_schema:
            name = table['name']
            
            if name in self.fleet_schemas:
                # Known table: merge with Fleet metadata
                fleet_schema = self.fleet_schemas[name]
                
                enriched = {
                    **table,
                    'description': fleet_schema.get('description', ''),
                    'platforms': fleet_schema.get('platforms', [platform]),
                    'evented': fleet_schema.get('evented', False),
                    'examples': fleet_schema.get('examples', []),
                    'notes': fleet_schema.get('notes'),
                    'is_custom': False,
                    'metadata_source': 'fleet_repository'
                }
                
                # Merge column details (prefer Fleet's descriptions)
                for col_name, col_info in fleet_schema.get('column_details', {}).items():
                    if col_name in enriched['column_details']:
                        enriched['column_details'][col_name].update(col_info)
                
                enriched_tables.append(enriched)
            else:
                # Custom/unknown table
                enriched_tables.append({
                    **table,
                    'description': f"Custom or extension table: {name}",
                    'platforms': [platform],
                    'evented': False,
                    'examples': [],
                    'notes': "This table was discovered on the host but is not in Fleet's schema repository. It may be from an osquery extension.",
                    'is_custom': True,
                    'metadata_source': 'live_discovery_only'
                })
        
        return enriched_tables
    
    def _get_fleet_schemas_by_platform(self, platform: str) -> list[dict[str, Any]]:
        """Get Fleet schemas filtered by platform (fallback method).
        
        Args:
            platform: Platform to filter by
            
        Returns:
            List of table dictionaries
        """
        tables = []
        
        for name, schema in self.fleet_schemas.items():
            if platform in schema.get('platforms', []):
                tables.append({
                    'name': name,
                    **schema,
                    'is_custom': False,
                    'metadata_source': 'fleet_repository_only'
                })
        
        return tables
    
    def invalidate_host(self, host_id: int):
        """Invalidate cache for a specific host.
        
        Args:
            host_id: Host ID to invalidate
        """
        keys_to_remove = [k for k in self.host_tables.keys() if k.startswith(f"{host_id}_")]
        for key in keys_to_remove:
            del self.host_tables[key]
            if key in self.last_fetch:
                del self.last_fetch[key]
        
        logger.info(f"Invalidated cache for host {host_id}")


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

