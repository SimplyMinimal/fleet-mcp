"""Osquery table reference tools for Fleet MCP."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import FleetClient
from .table_discovery import get_table_cache

logger = logging.getLogger(__name__)


def _get_default_platform() -> str:
    """Get the default platform when detection fails.

    Returns:
        Default platform string
    """
    return "linux"


def _get_host_platform_with_fallback(
    host_response: dict[str, Any] | None, host_id: int
) -> str:
    """Extract platform from host response with proper fallback and logging.

    Args:
        host_response: Fleet API response data
        host_id: Host ID for logging context

    Returns:
        Platform string (detected or default)
    """
    if host_response and host_response.get("host", {}).get("platform"):
        platform = host_response["host"]["platform"]
        if isinstance(platform, str):
            return platform

    default_platform = _get_default_platform()
    logger.warning(
        f"Failed to get platform for host {host_id}: "
        f"no platform data in response, defaulting to {default_platform}"
    )
    return default_platform


# Keyword aliases for better suggestion matching
KEYWORD_ALIASES = {
    "software": [
        "applications",
        "programs",
        "packages",
        "apps",
        "installed",
        "install",
    ],
    "network": ["connections", "sockets", "ports", "interfaces", "net", "tcp", "udp"],
    "users": ["accounts", "logins", "logged", "sessions"],
    "processes": ["running", "tasks", "services", "procs"],
    "files": ["filesystem", "directories", "paths", "folders"],
    "security": ["certificates", "keys", "encryption", "auth", "certs"],
    "browser": ["chrome", "firefox", "safari", "extensions", "addons"],
    "packages": ["rpm", "deb", "apt", "yum", "dnf"],
}


def _expand_keywords(query_intent: str) -> list[str]:
    """Expand query keywords with aliases for better matching.

    Args:
        query_intent: Natural language query intent

    Returns:
        List of expanded keywords including aliases
    """
    keywords = query_intent.lower().split()
    expanded = set(keywords)

    for keyword in keywords:
        for main_term, aliases in KEYWORD_ALIASES.items():
            if keyword in aliases or keyword == main_term:
                expanded.add(main_term)
                expanded.update(aliases)

    return list(expanded)


def register_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register all table reference tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """
    register_read_tools(mcp, client)


def register_read_tools(mcp: FastMCP, client: FleetClient) -> None:
    """Register read-only table reference tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: Fleet API client
    """

    @mcp.tool()
    async def fleet_list_osquery_tables(
        host_id: int | None = None,
        platform: str | None = None,
        search: str | None = None,
        evented_only: bool = False,
        limit: int = 100,
        include_custom: bool = True,
    ) -> dict[str, Any]:
        """List all available osquery tables with their schemas and descriptions.

        This tool dynamically discovers tables from:
        1. Live osquery hosts (if host_id provided) - most accurate
        2. Fleet's curated schema repository - rich metadata
        3. Bundled schemas - offline fallback

        The tool uses a hybrid approach that combines live table discovery with
        Fleet's curated metadata to provide both accuracy and rich documentation.

        Args:
            host_id: Optional host ID to discover tables from (recommended for accuracy)
            platform: Filter tables by platform (darwin, linux, windows, chrome)
            search: Search tables by name or description (case-insensitive)
            evented_only: If True, only return evented tables
            limit: Maximum number of tables to return (default: 100)
            include_custom: Include custom/extension tables (default: True)

        Returns:
            Dict containing list of tables with detailed schema information.
        """
        try:
            # Get table cache
            cache = await get_table_cache()

            # Get tables (either from host or Fleet schemas)
            if host_id:
                # Get host info to determine platform
                if not platform:
                    try:
                        async with client:
                            host_response = await client.get(f"/hosts/{host_id}")
                            if host_response.success and host_response.data:
                                platform = _get_host_platform_with_fallback(
                                    host_response.data, host_id
                                )
                            else:
                                default_platform = _get_default_platform()
                                logger.warning(
                                    f"Failed to get host platform for host {host_id}: "
                                    f"API response unsuccessful, defaulting to {default_platform}"
                                )
                                platform = default_platform
                    except Exception as e:
                        default_platform = _get_default_platform()
                        logger.warning(
                            f"Failed to get host platform for host {host_id}: {e}, "
                            f"defaulting to {default_platform}"
                        )
                        platform = default_platform

                # Discover tables on live host
                tables = await cache.get_tables_for_host(client, host_id, platform)
                discovery_method = "live_host_discovery"
            else:
                # Use Fleet schemas only
                if not platform:
                    platform = "linux"  # Default platform

                tables = cache._get_fleet_schemas_by_platform(platform)
                discovery_method = "fleet_schemas_only"

            # Apply filters
            filtered_tables = []
            for table in tables:
                # Custom table filter
                if not include_custom and table.get("is_custom", False):
                    continue

                # Platform filter (additional filtering if specified)
                if platform and platform.lower() not in [
                    p.lower() for p in table.get("platforms", [])
                ]:
                    continue

                # Evented filter
                if evented_only and not table.get("evented", False):
                    continue

                # Search filter
                if search:
                    search_lower = search.lower()
                    table_name = table.get("name", "").lower()
                    description = table.get("description", "").lower()
                    columns = [col.lower() for col in table.get("columns", [])]

                    if not (
                        search_lower in table_name
                        or search_lower in description
                        or any(search_lower in col for col in columns)
                    ):
                        continue

                filtered_tables.append(table)

                # Apply limit
                if len(filtered_tables) >= limit:
                    break

            # Count custom vs known tables
            custom_count = len(
                [t for t in filtered_tables if t.get("is_custom", False)]
            )
            known_count = len(filtered_tables) - custom_count

            return {
                "success": True,
                "tables": filtered_tables,
                "count": len(filtered_tables),
                "total_available": len(tables),
                "custom_tables": custom_count,
                "known_tables": known_count,
                "discovery_method": discovery_method,
                "filters_applied": {
                    "host_id": host_id,
                    "platform": platform,
                    "search": search,
                    "evented_only": evented_only,
                    "include_custom": include_custom,
                    "limit": limit,
                },
                "message": f"Found {len(filtered_tables)} osquery tables ({known_count} known, {custom_count} custom)",
            }

        except Exception as e:
            logger.error(f"Failed to list osquery tables: {e}")
            return {
                "success": False,
                "message": f"Failed to list osquery tables: {str(e)}",
                "tables": [],
                "count": 0,
            }

    @mcp.tool()
    async def fleet_get_osquery_table_schema(
        table_name: str, host_id: int | None = None
    ) -> dict[str, Any]:
        """Get detailed schema information for a specific osquery table.

        This tool retrieves comprehensive schema information including:
        - Column names, types, and descriptions
        - Platform availability
        - Usage examples
        - Special requirements and notes from Fleet's schema overrides

        Args:
            table_name: Name of the osquery table to get schema for
            host_id: Optional host ID to get live schema from (recommended)

        Returns:
            Dict containing detailed table schema, columns, types, usage examples,
            and any special requirements or notes from Fleet's schema overrides.
        """
        try:
            # Get table cache
            cache = await get_table_cache()

            # Get tables
            if host_id:
                # Get host platform
                platform = "linux"  # Default
                try:
                    async with client:
                        host_response = await client.get(f"/hosts/{host_id}")
                        if host_response.success and host_response.data:
                            platform = host_response.data.get("host", {}).get(
                                "platform", "linux"
                            )
                except Exception as e:
                    logger.warning(f"Failed to get host platform: {e}")

                tables = await cache.get_tables_for_host(client, host_id, platform)
            else:
                # Use all Fleet schemas
                tables = []
                for name, schema in cache.fleet_schemas.items():
                    # Merge with overrides
                    merged_schema = cache._merge_overrides_with_schema(name, schema)
                    tables.append({"name": name, **merged_schema, "is_custom": False})

            # Find the specific table
            table_info = None
            for table in tables:
                if table.get("name", "").lower() == table_name.lower():
                    table_info = table
                    break

            if not table_info:
                return {
                    "success": False,
                    "message": f"Table '{table_name}' not found. Try using fleet_list_osquery_tables to see available tables.",
                    "table": None,
                }

            # Build response with prominent override information
            response = {
                "success": True,
                "table": table_info,
                "message": f"Retrieved schema for table '{table_name}'",
            }

            # Add prominent section for override notes if present
            if table_info.get("has_overrides"):
                response["usage_requirements"] = {
                    "has_special_requirements": True,
                    "notes": table_info.get("override_notes"),
                    "examples": table_info.get("override_examples"),
                }

            return response

        except Exception as e:
            logger.error(f"Failed to get table schema for {table_name}: {e}")
            return {
                "success": False,
                "message": f"Failed to get table schema: {str(e)}",
                "table": None,
            }

    @mcp.tool()
    async def fleet_suggest_tables_for_query(
        query_intent: str,
        host_id: int | None = None,
        platform: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Suggest relevant osquery tables based on query intent or keywords.

        This tool helps you find the right osquery tables for your query by:
        1. Analyzing your intent (e.g., "find installed software", "check network connections")
        2. Matching keywords against table names, descriptions, and columns
        3. Providing relevance scores to rank suggestions
        4. Including usage examples and metadata

        BEST PRACTICES:
        - Describe what you want to find, not how to find it
        - Use natural language (e.g., "running processes" not "SELECT * FROM processes")
        - Specify host_id for most accurate results (discovers custom tables)
        - Specify platform if known (darwin/linux/windows) for better suggestions

        EXAMPLES:
        - "find all installed Python packages" → suggests rpm_packages, deb_packages, programs
        - "check which processes are listening on ports" → suggests processes, listening_ports
        - "list browser extensions" → suggests chrome_extensions, firefox_addons

        Args:
            query_intent: Natural language description of what you want to query
            host_id: Optional host ID to discover tables from (recommended)
            platform: Target platform (darwin, linux, windows, chrome) - filters suggestions
            limit: Maximum number of suggestions (default: 10)

        Returns:
            Ranked list of relevant tables with relevance scores, schemas, and examples.
        """
        try:
            # Get table cache
            cache = await get_table_cache()

            # Get tables
            if host_id:
                # Get host platform
                if not platform:
                    try:
                        async with client:
                            host_response = await client.get(f"/hosts/{host_id}")
                            if host_response.success and host_response.data:
                                platform = host_response.data.get("host", {}).get(
                                    "platform", "linux"
                                )
                    except Exception as e:
                        logger.warning(f"Failed to get host platform: {e}")
                        platform = "linux"

                # Ensure platform is set (should always be set by now)
                if not platform:
                    platform = "linux"

                tables = await cache.get_tables_for_host(client, host_id, platform)
            else:
                # Use Fleet schemas
                if platform:
                    tables = cache._get_fleet_schemas_by_platform(platform)
                else:
                    # All tables
                    tables = []
                    for name, schema in cache.fleet_schemas.items():
                        tables.append({"name": name, **schema, "is_custom": False})

            # Expand keywords with synonyms
            query_keywords = _expand_keywords(query_intent)

            suggestions = []

            for table in tables:
                # Platform filter (if specified and not already filtered)
                if platform and platform.lower() not in [
                    p.lower() for p in table.get("platforms", [])
                ]:
                    continue

                # Calculate relevance score
                score = 0
                table_name = table.get("name", "").lower()
                description = table.get("description", "").lower()
                columns = [col.lower() for col in table.get("columns", [])]

                # Score based on keyword matches
                for keyword in query_keywords:
                    if keyword in table_name:
                        score += 10
                    if keyword in description:
                        score += 5
                    for col in columns:
                        if keyword in col:
                            score += 3

                if score > 0:
                    suggestions.append({**table, "relevance_score": score})

            # Sort by relevance score and limit results
            suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
            suggestions = suggestions[:limit]

            return {
                "success": True,
                "suggestions": suggestions,
                "count": len(suggestions),
                "query_intent": query_intent,
                "platform": platform,
                "host_id": host_id,
                "message": f"Found {len(suggestions)} relevant tables for '{query_intent}'",
            }

        except Exception as e:
            logger.error(f"Failed to suggest tables for query: {e}")
            return {
                "success": False,
                "message": f"Failed to suggest tables: {str(e)}",
                "suggestions": [],
                "count": 0,
            }


# Note: The old _get_osquery_tables() function with hardcoded tables has been removed.
# Tables are now dynamically discovered using the TableSchemaCache in table_discovery.py
# This provides:
# - Live discovery from osquery_registry table
# - Rich metadata from Fleet's GitHub schema repository
# - Support for custom tables and extensions
# - Platform-aware filtering
# - Smart caching with 1-hour TTL


async def _get_osquery_tables_legacy() -> list[dict[str, Any]]:
    """Get comprehensive osquery table information.

    Returns a comprehensive list of commonly used osquery tables with their
    schema information, descriptions, and examples.

    Returns:
        List of table dictionaries with schema information.
    """
    return [
        {
            "name": "processes",
            "description": "All running processes on the host system",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": [
                "pid",
                "name",
                "path",
                "cmdline",
                "state",
                "cwd",
                "root",
                "uid",
                "gid",
                "euid",
                "egid",
                "suid",
                "sgid",
                "on_disk",
                "wired_size",
                "resident_size",
                "total_size",
                "user_time",
                "system_time",
                "disk_bytes_read",
                "disk_bytes_written",
                "start_time",
                "parent",
                "pgroup",
                "threads",
                "nice",
            ],
            "column_details": {
                "pid": {
                    "type": "bigint",
                    "description": "Process (or thread) ID",
                    "required": False,
                },
                "name": {
                    "type": "text",
                    "description": "The process name",
                    "required": False,
                },
                "path": {
                    "type": "text",
                    "description": "Path to executed binary",
                    "required": False,
                },
                "cmdline": {
                    "type": "text",
                    "description": "Complete argv",
                    "required": False,
                },
                "state": {
                    "type": "text",
                    "description": "Process state",
                    "required": False,
                },
                "uid": {
                    "type": "bigint",
                    "description": "Unsigned user ID",
                    "required": False,
                },
                "gid": {
                    "type": "bigint",
                    "description": "Unsigned group ID",
                    "required": False,
                },
            },
            "examples": [
                "SELECT pid, name, cmdline FROM processes WHERE name = 'chrome';",
                "SELECT * FROM processes WHERE pid = 1234;",
                "SELECT name, COUNT(*) as count FROM processes GROUP BY name ORDER BY count DESC;",
            ],
        },
        {
            "name": "users",
            "description": "Local user accounts (including domain accounts that have logged on locally (Windows), or local accounts (other platforms))",
            "platforms": ["darwin", "linux", "windows", "chrome"],
            "evented": False,
            "columns": [
                "uid",
                "gid",
                "uid_signed",
                "gid_signed",
                "username",
                "description",
                "directory",
                "shell",
                "uuid",
                "type",
                "is_hidden",
                "pid_with_namespace",
            ],
            "column_details": {
                "uid": {"type": "bigint", "description": "User ID", "required": False},
                "username": {
                    "type": "text",
                    "description": "Username",
                    "required": False,
                },
                "description": {
                    "type": "text",
                    "description": "Optional user description",
                    "required": False,
                },
                "directory": {
                    "type": "text",
                    "description": "User's home directory",
                    "required": False,
                },
                "shell": {
                    "type": "text",
                    "description": "User's configured default shell",
                    "required": False,
                },
            },
            "examples": [
                "SELECT uid, username, description FROM users;",
                "SELECT * FROM users WHERE username = 'admin';",
                "SELECT username, directory, shell FROM users WHERE uid >= 1000;",
            ],
        },
        {
            "name": "file",
            "description": "Interactive filesystem attributes and metadata",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": [
                "path",
                "directory",
                "filename",
                "inode",
                "uid",
                "gid",
                "mode",
                "device",
                "size",
                "block_size",
                "atime",
                "mtime",
                "ctime",
                "btime",
                "hard_links",
                "symlink",
                "type",
                "attributes",
                "volume_serial",
                "file_id",
                "file_version",
                "product_version",
                "original_filename",
            ],
            "column_details": {
                "path": {
                    "type": "text",
                    "description": "Absolute file path",
                    "required": True,
                },
                "filename": {
                    "type": "text",
                    "description": "Name portion of file path",
                    "required": False,
                },
                "size": {
                    "type": "bigint",
                    "description": "Size of file in bytes",
                    "required": False,
                },
                "mtime": {
                    "type": "bigint",
                    "description": "Last modification time",
                    "required": False,
                },
                "type": {
                    "type": "text",
                    "description": "File type (regular, directory, etc.)",
                    "required": False,
                },
            },
            "examples": [
                "SELECT * FROM file WHERE path = '/etc/passwd';",
                "SELECT path, size, mtime FROM file WHERE path LIKE '/tmp/%';",
                "SELECT filename, size FROM file WHERE directory = '/Applications';",
            ],
        },
        {
            "name": "network_interfaces",
            "description": "Details of the system's network interfaces and their configuration",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": [
                "interface",
                "mac",
                "ip_address",
                "mask",
                "broadcast",
                "point_to_point",
                "type",
                "mtu",
                "metric",
                "flags",
                "ipackets",
                "opackets",
                "ibytes",
                "obytes",
                "ierrors",
                "oerrors",
                "idrops",
                "odrops",
                "collisions",
                "last_change",
                "link_speed",
                "pci_slot",
                "friendly_name",
                "description",
                "manufacturer",
                "connection_id",
                "connection_status",
                "enabled",
                "physical_adapter",
                "speed",
                "service",
                "dhcp_enabled",
                "dhcp_lease_expires",
                "dhcp_lease_obtained",
                "dhcp_server",
                "dns_domain",
                "dns_domain_suffix_search_order",
                "dns_host_name",
                "dns_server_search_order",
            ],
            "column_details": {
                "interface": {
                    "type": "text",
                    "description": "Interface name",
                    "required": False,
                },
                "mac": {
                    "type": "text",
                    "description": "MAC address",
                    "required": False,
                },
                "ip_address": {
                    "type": "text",
                    "description": "IP address",
                    "required": False,
                },
                "type": {
                    "type": "integer",
                    "description": "Interface type",
                    "required": False,
                },
            },
            "examples": [
                "SELECT interface, mac, ip_address FROM network_interfaces;",
                "SELECT * FROM network_interfaces WHERE ip_address != '';",
                "SELECT interface, type, enabled FROM network_interfaces WHERE enabled = 1;",
            ],
        },
        {
            "name": "listening_ports",
            "description": "Processes with listening (bound) network sockets/ports",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": [
                "pid",
                "port",
                "protocol",
                "family",
                "address",
                "fd",
                "socket",
                "path",
                "net_namespace",
            ],
            "column_details": {
                "pid": {
                    "type": "integer",
                    "description": "Process (or thread) ID",
                    "required": False,
                },
                "port": {
                    "type": "integer",
                    "description": "Transport layer port",
                    "required": False,
                },
                "protocol": {
                    "type": "integer",
                    "description": "Transport protocol (TCP/UDP)",
                    "required": False,
                },
                "address": {
                    "type": "text",
                    "description": "Specific address for bind",
                    "required": False,
                },
            },
            "examples": [
                "SELECT pid, port, protocol, address FROM listening_ports;",
                "SELECT * FROM listening_ports WHERE port = 80;",
                "SELECT p.name, lp.port, lp.address FROM listening_ports lp JOIN processes p ON lp.pid = p.pid;",
            ],
        },
        {
            "name": "system_info",
            "description": "System information for identification",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": [
                "hostname",
                "uuid",
                "cpu_type",
                "cpu_subtype",
                "cpu_brand",
                "cpu_physical_cores",
                "cpu_logical_cores",
                "cpu_microcode",
                "physical_memory",
                "hardware_vendor",
                "hardware_model",
                "hardware_version",
                "hardware_serial",
                "computer_name",
                "local_hostname",
                "cpu_sockets",
            ],
            "column_details": {
                "hostname": {
                    "type": "text",
                    "description": "Network hostname",
                    "required": False,
                },
                "cpu_brand": {
                    "type": "text",
                    "description": "CPU brand string",
                    "required": False,
                },
                "physical_memory": {
                    "type": "bigint",
                    "description": "Total physical memory in bytes",
                    "required": False,
                },
                "hardware_vendor": {
                    "type": "text",
                    "description": "Hardware vendor",
                    "required": False,
                },
            },
            "examples": [
                "SELECT hostname, cpu_brand, physical_memory FROM system_info;",
                "SELECT * FROM system_info;",
                "SELECT hardware_vendor, hardware_model FROM system_info;",
            ],
        },
        {
            "name": "os_version",
            "description": "A single row containing the operating system name and version",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": [
                "name",
                "version",
                "major",
                "minor",
                "patch",
                "build",
                "platform",
                "platform_like",
                "codename",
                "arch",
                "install_date",
                "pid_with_namespace",
            ],
            "column_details": {
                "name": {
                    "type": "text",
                    "description": "Distribution or product name",
                    "required": False,
                },
                "version": {
                    "type": "text",
                    "description": "Pretty, suitable for presentation, OS version",
                    "required": False,
                },
                "platform": {
                    "type": "text",
                    "description": "OS Platform or ID",
                    "required": False,
                },
                "arch": {
                    "type": "text",
                    "description": "OS Architecture",
                    "required": False,
                },
            },
            "examples": [
                "SELECT name, version, platform, arch FROM os_version;",
                "SELECT * FROM os_version;",
                "SELECT name, major, minor, patch FROM os_version;",
            ],
        },
        {
            "name": "installed_applications",
            "description": "macOS applications installed in known search paths (e.g., /Applications)",
            "platforms": ["darwin"],
            "evented": False,
            "columns": [
                "name",
                "path",
                "bundle_executable",
                "bundle_identifier",
                "bundle_name",
                "bundle_short_version",
                "bundle_version",
                "bundle_package_type",
                "environment",
                "element",
                "compiler",
                "development_region",
                "display_name",
                "info_string",
                "minimum_system_version",
                "category",
                "applescript_enabled",
                "copyright",
            ],
            "column_details": {
                "name": {
                    "type": "text",
                    "description": "Name of the application",
                    "required": False,
                },
                "path": {
                    "type": "text",
                    "description": "Path to application bundle",
                    "required": False,
                },
                "bundle_identifier": {
                    "type": "text",
                    "description": "Application bundle identifier",
                    "required": False,
                },
                "bundle_version": {
                    "type": "text",
                    "description": "Application bundle version",
                    "required": False,
                },
            },
            "examples": [
                "SELECT name, bundle_identifier, bundle_version FROM installed_applications;",
                "SELECT * FROM installed_applications WHERE name LIKE '%Chrome%';",
                "SELECT name, path FROM installed_applications ORDER BY name;",
            ],
        },
        {
            "name": "programs",
            "description": "Represents products as they are installed by Windows Installer. A product generally correlates to one installation package on Windows",
            "platforms": ["windows"],
            "evented": False,
            "columns": [
                "name",
                "version",
                "install_location",
                "install_source",
                "language",
                "publisher",
                "uninstall_string",
                "install_date",
                "identifying_number",
            ],
            "column_details": {
                "name": {
                    "type": "text",
                    "description": "Commonly used product name",
                    "required": False,
                },
                "version": {
                    "type": "text",
                    "description": "Product version information",
                    "required": False,
                },
                "publisher": {
                    "type": "text",
                    "description": "Name of the product supplier",
                    "required": False,
                },
                "install_date": {
                    "type": "text",
                    "description": "Date that this product was installed",
                    "required": False,
                },
            },
            "examples": [
                "SELECT name, version, publisher FROM programs;",
                "SELECT * FROM programs WHERE name LIKE '%Microsoft%';",
                "SELECT name, install_date FROM programs ORDER BY install_date DESC;",
            ],
        },
        {
            "name": "deb_packages",
            "description": "The installed DEB package database",
            "platforms": ["linux"],
            "evented": False,
            "columns": [
                "name",
                "version",
                "source",
                "size",
                "arch",
                "revision",
                "status",
                "maintainer",
                "section",
                "priority",
                "admindir",
                "pid_with_namespace",
            ],
            "column_details": {
                "name": {
                    "type": "text",
                    "description": "Package name",
                    "required": False,
                },
                "version": {
                    "type": "text",
                    "description": "Package version",
                    "required": False,
                },
                "status": {
                    "type": "text",
                    "description": "Package status",
                    "required": False,
                },
                "maintainer": {
                    "type": "text",
                    "description": "Package maintainer",
                    "required": False,
                },
            },
            "examples": [
                "SELECT name, version, status FROM deb_packages;",
                "SELECT * FROM deb_packages WHERE name = 'openssh-server';",
                "SELECT name, maintainer FROM deb_packages WHERE status = 'install ok installed';",
            ],
        },
        {
            "name": "startup_items",
            "description": "Applications and binaries set as user/login startup items",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": ["name", "path", "args", "type", "source", "status", "username"],
            "column_details": {
                "name": {
                    "type": "text",
                    "description": "Name of startup item",
                    "required": False,
                },
                "path": {
                    "type": "text",
                    "description": "Path of startup executable",
                    "required": False,
                },
                "type": {
                    "type": "text",
                    "description": "Startup Item or Login Item",
                    "required": False,
                },
                "status": {
                    "type": "text",
                    "description": "Startup status; either enabled or disabled",
                    "required": False,
                },
            },
            "examples": [
                "SELECT name, path, status FROM startup_items;",
                "SELECT * FROM startup_items WHERE status = 'enabled';",
                "SELECT name, type, username FROM startup_items;",
            ],
        },
        {
            "name": "logged_in_users",
            "description": "Users with an active shell on the system",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": [
                "type",
                "user",
                "tty",
                "host",
                "time",
                "pid",
                "sid",
                "registry_hive",
            ],
            "column_details": {
                "user": {
                    "type": "text",
                    "description": "User login name",
                    "required": False,
                },
                "tty": {
                    "type": "text",
                    "description": "Device name",
                    "required": False,
                },
                "host": {
                    "type": "text",
                    "description": "Remote hostname",
                    "required": False,
                },
                "time": {
                    "type": "integer",
                    "description": "Time entry was made",
                    "required": False,
                },
            },
            "examples": [
                "SELECT user, tty, host, time FROM logged_in_users;",
                "SELECT * FROM logged_in_users;",
                "SELECT user, COUNT(*) as sessions FROM logged_in_users GROUP BY user;",
            ],
        },
        {
            "name": "hash",
            "description": "Filesystem hash data",
            "platforms": ["darwin", "linux", "windows"],
            "evented": False,
            "columns": [
                "path",
                "directory",
                "md5",
                "sha1",
                "sha256",
                "ssdeep",
                "pid_with_namespace",
            ],
            "column_details": {
                "path": {
                    "type": "text",
                    "description": "Must provide a path or directory",
                    "required": True,
                },
                "md5": {
                    "type": "text",
                    "description": "MD5 hash of provided filesystem data",
                    "required": False,
                },
                "sha1": {
                    "type": "text",
                    "description": "SHA1 hash of provided filesystem data",
                    "required": False,
                },
                "sha256": {
                    "type": "text",
                    "description": "SHA256 hash of provided filesystem data",
                    "required": False,
                },
            },
            "examples": [
                "SELECT path, md5, sha256 FROM hash WHERE path = '/bin/ls';",
                "SELECT * FROM hash WHERE directory = '/usr/bin';",
                "SELECT path, sha1 FROM hash WHERE path LIKE '/etc/%';",
            ],
        },
        {
            "name": "process_events",
            "description": "Track time/action process executions",
            "platforms": ["darwin", "linux"],
            "evented": True,
            "columns": [
                "pid",
                "path",
                "mode",
                "cmdline",
                "cmdline_size",
                "env",
                "env_count",
                "env_size",
                "cwd",
                "auid",
                "uid",
                "euid",
                "gid",
                "egid",
                "owner_uid",
                "owner_gid",
                "atime",
                "mtime",
                "ctime",
                "btime",
                "overflows",
                "parent",
                "time",
                "uptime",
                "eid",
                "status",
                "syscall",
                "exit_code",
            ],
            "column_details": {
                "pid": {
                    "type": "bigint",
                    "description": "Process (or thread) ID",
                    "required": False,
                },
                "path": {
                    "type": "text",
                    "description": "Path of executed file",
                    "required": False,
                },
                "cmdline": {
                    "type": "text",
                    "description": "Command line arguments",
                    "required": False,
                },
                "time": {
                    "type": "bigint",
                    "description": "Time of execution in UNIX time",
                    "required": False,
                },
            },
            "examples": [
                "SELECT pid, path, cmdline, time FROM process_events WHERE time > (strftime('%s', 'now') - 3600);",
                "SELECT * FROM process_events WHERE path LIKE '%bash%';",
                "SELECT path, COUNT(*) as executions FROM process_events GROUP BY path ORDER BY executions DESC;",
            ],
        },
    ]
