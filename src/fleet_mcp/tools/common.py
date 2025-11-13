"""Common utilities for Fleet MCP tools.

This module provides shared utilities to reduce code duplication across tool modules:
- Error handling decorator for consistent FleetAPIError handling
- Response formatting utilities for standardized API responses
- Parameter building utilities for common patterns like pagination
"""

import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from ..client import FleetAPIError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def handle_fleet_api_errors(
    operation_name: str,
    default_fields: dict[str, Any] | None = None,
) -> Callable[
    [Callable[..., Awaitable[dict[str, Any]]]], Callable[..., Awaitable[dict[str, Any]]]
]:
    """Decorator to handle FleetAPIError exceptions consistently across tools.

    This decorator wraps async tool functions to catch FleetAPIError exceptions,
    log them appropriately, and return a standardized error response.

    Args:
        operation_name: Human-readable operation name for error messages (e.g., "list labels")
        default_fields: Default fields to include in error response (e.g., {"labels": [], "count": 0})

    Returns:
        Decorator function that wraps the tool function

    Example:
        @mcp.tool()
        @handle_fleet_api_errors("list labels", {"labels": [], "count": 0})
        async def fleet_list_labels(...) -> dict[str, Any]:
            async with client:
                response = await client.get("/labels", params=params)
                # ... success handling ...
    """
    if default_fields is None:
        default_fields = {}

    def decorator(
        func: Callable[..., Awaitable[dict[str, Any]]],
    ) -> Callable[..., Awaitable[dict[str, Any]]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            try:
                return await func(*args, **kwargs)
            except FleetAPIError as e:
                logger.error(f"Failed to {operation_name}: {e}")
                error_response = {
                    "success": False,
                    "message": f"Failed to {operation_name}: {str(e)}",
                }
                error_response.update(default_fields)
                return error_response

        return wrapper

    return decorator


def format_success_response(
    message: str,
    data: Any = None,
    **additional_fields: Any,
) -> dict[str, Any]:
    """Format a successful API response with consistent structure.

    Args:
        message: Success message describing the operation result
        data: Response data (optional, included only if not None)
        **additional_fields: Additional fields to include in the response

    Returns:
        Formatted success response dict with "success": True

    Example:
        return format_success_response(
            "Label created successfully",
            data={"label": label_data},
            label_id=123
        )
    """
    response: dict[str, Any] = {
        "success": True,
        "message": message,
    }

    if data is not None:
        response["data"] = data

    response.update(additional_fields)
    return response


def format_list_response(
    items: list[Any],
    item_name: str,
    page: int | None = None,
    per_page: int | None = None,
    total_count: int | None = None,
    **additional_fields: Any,
) -> dict[str, Any]:
    """Format a list response with pagination metadata and consistent structure.

    Args:
        items: List of items to return
        item_name: Name of the items field (e.g., "hosts", "labels", "policies")
        page: Current page number (optional)
        per_page: Items per page (optional)
        total_count: Total count across all pages (optional, different from len(items))
        **additional_fields: Additional fields to include in the response

    Returns:
        Formatted list response dict with success, items, count, and pagination metadata

    Example:
        return format_list_response(
            labels,
            "labels",
            page=0,
            per_page=100,
            total_count=250
        )
    """
    response: dict[str, Any] = {
        "success": True,
        item_name: items,
        "count": len(items),
        "message": f"Found {len(items)} {item_name}",
    }

    if page is not None:
        response["page"] = page
    if per_page is not None:
        response["per_page"] = per_page
    if total_count is not None:
        response["total_count"] = total_count

    response.update(additional_fields)
    return response


def format_error_response(
    message: str,
    **default_fields: Any,
) -> dict[str, Any]:
    """Format an error response with consistent structure.

    Args:
        message: Error message describing what went wrong
        **default_fields: Default fields to include in error response (e.g., labels=[], count=0)

    Returns:
        Formatted error response dict with "success": False

    Example:
        return format_error_response(
            "Resource not found",
            label=None,
            label_id=label_id
        )
    """
    response: dict[str, Any] = {
        "success": False,
        "message": message,
    }
    response.update(default_fields)
    return response


def build_pagination_params(
    page: int | None = None,
    per_page: int | None = None,
    order_key: str | None = None,
    order_direction: str | None = None,
    team_id: int | None = None,
    query: str | None = None,
    **additional_params: Any,
) -> dict[str, Any]:
    """Build pagination and filtering parameters for Fleet API requests.

    This utility constructs the common parameter dict used across many list endpoints,
    including only non-None values to avoid sending unnecessary parameters.

    Args:
        page: Page number for pagination (0-based)
        per_page: Number of items per page
        order_key: Field to order by (e.g., "name", "created_at")
        order_direction: Sort direction ("asc" or "desc")
        team_id: Filter by team ID (optional)
        query: Search query string (optional)
        **additional_params: Additional parameters to include

    Returns:
        Dict containing only the non-None parameters

    Example:
        params = build_pagination_params(
            page=0,
            per_page=100,
            order_key="name",
            order_direction="asc",
            team_id=5
        )
        response = await client.get("/labels", params=params)
    """
    params: dict[str, Any] = {}

    if page is not None:
        params["page"] = page
    if per_page is not None:
        params["per_page"] = per_page
    if order_key is not None:
        params["order_key"] = order_key
    if order_direction is not None:
        params["order_direction"] = order_direction
    if team_id is not None:
        params["team_id"] = team_id
    if query is not None:
        params["query"] = query

    params.update(additional_params)
    return params
