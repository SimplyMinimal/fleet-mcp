"""Utility functions for host identifier resolution and fuzzy matching.

This module provides helper functions for resolving host identifiers (hostname, UUID,
serial number) with automatic fuzzy matching support.
"""

import logging
from typing import Any

from ..client import FleetAPIError, FleetClient

logger = logging.getLogger(__name__)


class HostLookupResult:
    """Result of a host identifier lookup operation.

    Attributes:
        success: Whether the lookup was successful
        host: The matched host data (if found)
        identifier: The original identifier used for lookup
        matched_hostname: The full hostname that was matched (if fuzzy matched)
        error_message: Error message with suggestions (if not found)
    """

    def __init__(
        self,
        success: bool,
        host: dict[str, Any] | None = None,
        identifier: str = "",
        matched_hostname: str | None = None,
        error_message: str | None = None,
    ):
        self.success = success
        self.host = host
        self.identifier = identifier
        self.matched_hostname = matched_hostname
        self.error_message = error_message

    @property
    def host_id(self) -> int | None:
        """Get the host ID from the matched host."""
        return self.host.get("id") if self.host else None

    @property
    def hostname(self) -> str | None:
        """Get the hostname from the matched host."""
        return self.host.get("hostname") if self.host else None


async def resolve_host_identifier(
    client: FleetClient, identifier: str
) -> HostLookupResult:
    """Resolve a host identifier with automatic fuzzy matching.

    This function attempts to find a host by identifier using the following strategy:
    1. First tries an exact lookup via /hosts/identifier/{identifier}
    2. If that fails, lists all hosts and tries fuzzy matching:
       - Hostname prefix match (case-insensitive)
       - UUID exact match (case-insensitive)
       - Serial number exact match (case-insensitive)
    3. If still not found, generates helpful error message with suggestions

    Args:
        client: Fleet API client instance
        identifier: Host identifier (hostname, UUID, or hardware serial)

    Returns:
        HostLookupResult containing the matched host or error information

    Example:
        >>> result = await resolve_host_identifier(client, "host-abc123")
        >>> if result.success:
        ...     print(f"Found host: {result.hostname}")
        ...     print(f"Host ID: {result.host_id}")
    """
    # First try the identifier as-is
    try:
        response = await client.get(f"/hosts/identifier/{identifier}")
        lookup_failed = not response.success or not response.data
    except FleetAPIError:
        # Identifier not found - will try fuzzy matching
        lookup_failed = True
        response = None

    # If exact lookup succeeded, return immediately
    if not lookup_failed and response and response.data:
        host = response.data.get("host", {})
        return HostLookupResult(
            success=True, host=host, identifier=identifier, matched_hostname=None
        )

    # Exact lookup failed - try fuzzy matching
    try:
        hosts_response = await client.get("/hosts")
        if not hosts_response.success or not hosts_response.data:
            return HostLookupResult(
                success=False,
                identifier=identifier,
                error_message=f"Host not found: {identifier}",
            )

        hosts = hosts_response.data.get("hosts", [])
        matched_host = _fuzzy_match_host(identifier, hosts)

        if matched_host:
            # Successfully matched via fuzzy matching
            matched_hostname = matched_host.get("hostname", "")
            logger.info(
                f"Matched identifier '{identifier}' to hostname '{matched_hostname}'"
            )
            return HostLookupResult(
                success=True,
                host=matched_host,
                identifier=identifier,
                matched_hostname=matched_hostname,
            )
        else:
            # No match found - generate helpful error message
            error_message = _generate_suggestions_message(identifier, hosts)
            return HostLookupResult(
                success=False, identifier=identifier, error_message=error_message
            )

    except FleetAPIError as e:
        logger.error(f"Failed to resolve host identifier {identifier}: {e}")
        return HostLookupResult(
            success=False,
            identifier=identifier,
            error_message=f"Failed to resolve host: {str(e)}",
        )


def _fuzzy_match_host(
    identifier: str, hosts: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Attempt to fuzzy match an identifier against a list of hosts.

    Matching rules (in order of precedence):
    1. Hostname starts with identifier (case-insensitive)
    2. UUID equals identifier (case-insensitive)
    3. Hardware serial equals identifier (case-insensitive)

    Args:
        identifier: The identifier to match
        hosts: List of host dictionaries from Fleet API

    Returns:
        The first matching host, or None if no match found
    """
    identifier_lower = identifier.lower()

    for host in hosts:
        hostname = host.get("hostname", "")
        uuid = host.get("uuid", "")
        serial = host.get("hardware_serial", "")

        # Check if identifier matches start of hostname
        if hostname.lower().startswith(identifier_lower):
            return host

        # Check if identifier matches UUID (case-insensitive)
        if uuid.lower() == identifier_lower:
            return host

        # Check if identifier matches serial
        if serial and serial.lower() == identifier_lower:
            return host

    return None


def _generate_suggestions_message(
    identifier: str, hosts: list[dict[str, Any]], max_suggestions: int = 5
) -> str:
    """Generate a helpful error message with host suggestions.

    Args:
        identifier: The identifier that was not found
        hosts: List of all hosts
        max_suggestions: Maximum number of suggestions to include

    Returns:
        Formatted error message with suggestions
    """
    online_hosts = [h for h in hosts if h.get("status") == "online"]
    suggestions = []

    for host in online_hosts[:max_suggestions]:
        hostname = host.get("hostname", "N/A")
        uuid = host.get("uuid", "N/A")
        serial = host.get("hardware_serial") or "N/A"
        suggestions.append(f"  - {hostname} (UUID: {uuid}, Serial: {serial})")

    suggestion_text = (
        "\n".join(suggestions) if suggestions else "  (No online hosts available)"
    )

    return f"Host not found: {identifier}\n\nAvailable online hosts (limit {max_suggestions} shown):\n{suggestion_text}"
