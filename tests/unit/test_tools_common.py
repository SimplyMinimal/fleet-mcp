"""Unit tests for common tool utilities."""

import pytest

from fleet_mcp.client import FleetAPIError
from fleet_mcp.tools.common import (
    build_pagination_params,
    format_error_response,
    format_list_response,
    format_success_response,
    handle_fleet_api_errors,
)


class TestErrorHandlingDecorator:
    """Test the handle_fleet_api_errors decorator."""

    @pytest.mark.asyncio
    async def test_decorator_success_passthrough(self):
        """Test that decorator passes through successful results unchanged."""

        @handle_fleet_api_errors("test operation", {"default": "value"})
        async def successful_function() -> dict[str, str]:
            return {"success": True, "message": "Operation succeeded", "data": "test"}

        result = await successful_function()
        assert result["success"] is True
        assert result["message"] == "Operation succeeded"
        assert result["data"] == "test"
        assert "default" not in result  # Default fields only added on error

    @pytest.mark.asyncio
    async def test_decorator_catches_fleet_api_error(self):
        """Test that decorator catches FleetAPIError and returns error response."""

        @handle_fleet_api_errors("test operation", {"items": [], "count": 0})
        async def failing_function() -> dict[str, str]:
            raise FleetAPIError("API request failed", status_code=500)

        result = await failing_function()
        assert result["success"] is False
        assert "Failed to test operation" in result["message"]
        assert "API request failed" in result["message"]
        assert result["items"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_decorator_with_no_default_fields(self):
        """Test decorator with no default fields specified."""

        @handle_fleet_api_errors("test operation")
        async def failing_function() -> dict[str, str]:
            raise FleetAPIError("API error")

        result = await failing_function()
        assert result["success"] is False
        assert "Failed to test operation" in result["message"]
        assert len(result) == 2  # Only success and message

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""

        @handle_fleet_api_errors("test operation")
        async def test_function() -> dict[str, str]:
            """Test function docstring."""
            return {"success": True}

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."

    @pytest.mark.asyncio
    async def test_decorator_with_function_arguments(self):
        """Test decorator works with functions that have arguments."""

        @handle_fleet_api_errors("process item", {"result": None})
        async def process_item(item_id: int, name: str) -> dict[str, str]:
            if item_id < 0:
                raise FleetAPIError("Invalid item ID")
            return {"success": True, "item_id": item_id, "name": name}

        # Test success case
        result = await process_item(123, "test")
        assert result["success"] is True
        assert result["item_id"] == 123
        assert result["name"] == "test"

        # Test error case
        result = await process_item(-1, "invalid")
        assert result["success"] is False
        assert "Failed to process item" in result["message"]
        assert result["result"] is None


class TestResponseFormatting:
    """Test response formatting utilities."""

    def test_format_success_response_basic(self):
        """Test basic success response formatting."""
        result = format_success_response("Operation completed")
        assert result["success"] is True
        assert result["message"] == "Operation completed"
        assert len(result) == 2

    def test_format_success_response_with_data(self):
        """Test success response with data field."""
        data = {"id": 123, "name": "test"}
        result = format_success_response("Created successfully", data=data)
        assert result["success"] is True
        assert result["message"] == "Created successfully"
        assert result["data"] == data

    def test_format_success_response_with_additional_fields(self):
        """Test success response with additional fields."""
        result = format_success_response(
            "Updated successfully",
            data={"id": 456},
            updated_count=5,
            timestamp="2024-01-01",
        )
        assert result["success"] is True
        assert result["message"] == "Updated successfully"
        assert result["data"] == {"id": 456}
        assert result["updated_count"] == 5
        assert result["timestamp"] == "2024-01-01"

    def test_format_success_response_data_none_not_included(self):
        """Test that data field is not included when None."""
        result = format_success_response("Success", data=None)
        assert "data" not in result
        assert result["success"] is True

    def test_format_list_response_basic(self):
        """Test basic list response formatting."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = format_list_response(items, "hosts")
        assert result["success"] is True
        assert result["hosts"] == items
        assert result["count"] == 3
        assert result["message"] == "Found 3 hosts"

    def test_format_list_response_with_pagination(self):
        """Test list response with pagination metadata."""
        items = [{"id": 1}, {"id": 2}]
        result = format_list_response(items, "labels", page=2, per_page=10)
        assert result["success"] is True
        assert result["labels"] == items
        assert result["count"] == 2
        assert result["page"] == 2
        assert result["per_page"] == 10
        assert "Found 2 labels" in result["message"]

    def test_format_list_response_with_total_count(self):
        """Test list response with total count different from current page count."""
        items = [{"id": 1}, {"id": 2}]
        result = format_list_response(
            items, "policies", page=0, per_page=2, total_count=50
        )
        assert result["count"] == 2  # Current page count
        assert result["total_count"] == 50  # Total across all pages

    def test_format_list_response_empty_list(self):
        """Test list response with empty list."""
        result = format_list_response([], "queries")
        assert result["success"] is True
        assert result["queries"] == []
        assert result["count"] == 0
        assert result["message"] == "Found 0 queries"

    def test_format_list_response_with_additional_fields(self):
        """Test list response with additional custom fields."""
        items = [{"id": 1}]
        result = format_list_response(items, "packs", query="test", team_id=5)
        assert result["packs"] == items
        assert result["query"] == "test"
        assert result["team_id"] == 5

    def test_format_error_response_basic(self):
        """Test basic error response formatting."""
        result = format_error_response("Operation failed")
        assert result["success"] is False
        assert result["message"] == "Operation failed"
        assert len(result) == 2

    def test_format_error_response_with_default_fields(self):
        """Test error response with default fields."""
        result = format_error_response(
            "Failed to list items",
            items=[],
            count=0,
        )
        assert result["success"] is False
        assert result["message"] == "Failed to list items"
        assert result["items"] == []
        assert result["count"] == 0

    def test_format_error_response_with_context(self):
        """Test error response with contextual information."""
        result = format_error_response(
            "Resource not found",
            resource_id=123,
            resource_type="label",
        )
        assert result["success"] is False
        assert result["resource_id"] == 123
        assert result["resource_type"] == "label"


class TestPaginationParams:
    """Test pagination parameter building utility."""

    def test_build_pagination_params_all_fields(self):
        """Test building params with all standard fields."""
        params = build_pagination_params(
            page=2,
            per_page=50,
            order_key="name",
            order_direction="desc",
            team_id=10,
            query="test",
        )
        assert params["page"] == 2
        assert params["per_page"] == 50
        assert params["order_key"] == "name"
        assert params["order_direction"] == "desc"
        assert params["team_id"] == 10
        assert params["query"] == "test"

    def test_build_pagination_params_minimal(self):
        """Test building params with only required fields."""
        params = build_pagination_params(page=0, per_page=100)
        assert params["page"] == 0
        assert params["per_page"] == 100
        assert len(params) == 2

    def test_build_pagination_params_none_values_excluded(self):
        """Test that None values are not included in params."""
        params = build_pagination_params(
            page=0,
            per_page=100,
            order_key=None,
            team_id=None,
            query=None,
        )
        assert "order_key" not in params
        assert "team_id" not in params
        assert "query" not in params
        assert len(params) == 2

    def test_build_pagination_params_empty(self):
        """Test building params with no arguments."""
        params = build_pagination_params()
        assert params == {}

    def test_build_pagination_params_with_additional_params(self):
        """Test building params with additional custom parameters."""
        params = build_pagination_params(
            page=0,
            per_page=10,
            status="active",
            platform="darwin",
        )
        assert params["page"] == 0
        assert params["per_page"] == 10
        assert params["status"] == "active"
        assert params["platform"] == "darwin"

    def test_build_pagination_params_zero_values_included(self):
        """Test that zero values are included (not treated as None)."""
        params = build_pagination_params(page=0, per_page=0)
        assert params["page"] == 0
        assert params["per_page"] == 0

    def test_build_pagination_params_empty_string_included(self):
        """Test that empty strings are included (not treated as None)."""
        params = build_pagination_params(query="")
        assert params["query"] == ""
