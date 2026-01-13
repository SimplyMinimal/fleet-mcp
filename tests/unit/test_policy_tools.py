"""Tests for Fleet Policy management tools."""

from unittest.mock import MagicMock, patch

import pytest

from fleet_mcp.client import FleetClient, FleetResponse
from fleet_mcp.config import FleetConfig
from fleet_mcp.tools import policy_tools


@pytest.fixture
def fleet_config():
    """Create a test Fleet configuration."""
    return FleetConfig(
        server_url="https://test.fleet.com", api_token="test-token-123456789"
    )


@pytest.fixture
def fleet_client(fleet_config):
    """Create a test Fleet client."""
    return FleetClient(fleet_config)


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server."""
    mcp = MagicMock()
    mcp.tool = MagicMock(return_value=lambda f: f)
    return mcp


class TestFleetListPoliciesSearchAllTeams:
    """Test fleet_list_policies with search_all_teams parameter."""

    @pytest.mark.asyncio
    async def test_mutual_exclusion_error(self, fleet_client, mock_mcp):
        """Test that search_all_teams and team_id cannot be used together."""
        # We need to test the actual function behavior
        # Register tools and capture the fleet_list_policies function
        registered_tools = {}

        def mock_tool_decorator():
            def decorator(func):
                registered_tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = mock_tool_decorator
        policy_tools.register_read_tools(mock_mcp, fleet_client)

        # Get the fleet_list_policies function
        fleet_list_policies = registered_tools.get("fleet_list_policies")
        assert fleet_list_policies is not None

        # Test mutual exclusion
        result = await fleet_list_policies(team_id=10, search_all_teams=True)

        assert result["success"] is False
        assert "cannot be used together" in result["message"]
        assert result["policies"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_search_all_teams_deduplication(self, fleet_client, mock_mcp):
        """Test that duplicate policies are removed when searching all teams."""
        registered_tools = {}

        def mock_tool_decorator():
            def decorator(func):
                registered_tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = mock_tool_decorator
        policy_tools.register_read_tools(mock_mcp, fleet_client)

        # Mock teams response
        teams_response = FleetResponse(
            success=True,
            data={
                "teams": [
                    {"id": 1, "name": "Team A"},
                    {"id": 2, "name": "Team B"},
                ]
            },
            message="Success",
        )

        # Mock team 1 policies response
        team1_policies_response = FleetResponse(
            success=True,
            data={
                "policies": [
                    {"id": 1, "name": "Firewall Enabled", "team_id": 1},
                    {"id": 2, "name": "Disk Encryption Enabled", "team_id": 1},
                ],
                "inherited_policies": [
                    {"id": 10, "name": "Global Policy 1", "team_id": None},
                ],
            },
            message="Success",
        )

        # Mock team 2 policies response (includes duplicate global policy)
        team2_policies_response = FleetResponse(
            success=True,
            data={
                "policies": [
                    {"id": 3, "name": "Encryption Enabled", "team_id": 2},
                ],
                "inherited_policies": [
                    {"id": 10, "name": "Global Policy 1", "team_id": None},  # Duplicate
                ],
            },
            message="Success",
        )

        async def mock_get(endpoint, params=None):  # noqa: ARG001
            if endpoint == "/teams":
                return teams_response
            elif endpoint == "/teams/1/policies":
                return team1_policies_response
            elif endpoint == "/teams/2/policies":
                return team2_policies_response
            return FleetResponse(success=False, message="Not found", data=None)

        with patch.object(fleet_client, "get", side_effect=mock_get):
            fleet_list_policies = registered_tools.get("fleet_list_policies")
            assert fleet_list_policies is not None
            result = await fleet_list_policies(search_all_teams=True)

            assert result["success"] is True
            # Should have 4 unique policies (1, 2, 3, 10) - not 5
            assert result["count"] == 4
            assert result["total_count"] == 4

            # Verify policy IDs are unique
            policy_ids = [p["id"] for p in result["policies"]]
            assert len(policy_ids) == len(set(policy_ids))  # No duplicates
            assert set(policy_ids) == {1, 2, 3, 10}

    @pytest.mark.asyncio
    async def test_search_all_teams_with_query(self, fleet_client, mock_mcp):
        """Test search_all_teams with query filter."""
        registered_tools = {}

        def mock_tool_decorator():
            def decorator(func):
                registered_tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = mock_tool_decorator
        policy_tools.register_read_tools(mock_mcp, fleet_client)

        # Mock responses (same as above)
        teams_response = FleetResponse(
            success=True,
            data={"teams": [{"id": 1, "name": "Team A"}]},
            message="Success",
        )

        team1_policies_response = FleetResponse(
            success=True,
            data={
                "policies": [
                    {"id": 1, "name": "Firewall Enabled", "team_id": 1},
                    {"id": 2, "name": "Disk Encryption Enabled", "team_id": 1},
                ],
                "inherited_policies": [],
            },
            message="Success",
        )

        async def mock_get(endpoint, params=None):  # noqa: ARG001
            if endpoint == "/teams":
                return teams_response
            elif endpoint == "/teams/1/policies":
                return team1_policies_response
            return FleetResponse(success=False, message="Not found", data=None)

        with patch.object(fleet_client, "get", side_effect=mock_get):
            fleet_list_policies = registered_tools.get("fleet_list_policies")
            assert fleet_list_policies is not None
            result = await fleet_list_policies(
                search_all_teams=True, query="Disk Encryption"
            )

            assert result["success"] is True
            assert result["count"] == 1
            assert result["policies"][0]["name"] == "Disk Encryption Enabled"

    @pytest.mark.asyncio
    async def test_search_all_teams_pagination(self, fleet_client, mock_mcp):
        """Test pagination with search_all_teams."""
        registered_tools = {}

        def mock_tool_decorator():
            def decorator(func):
                registered_tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = mock_tool_decorator
        policy_tools.register_read_tools(mock_mcp, fleet_client)

        teams_response = FleetResponse(
            success=True,
            data={"teams": [{"id": 1, "name": "Team A"}]},
            message="Success",
        )

        # Create 5 policies for pagination testing
        team1_policies_response = FleetResponse(
            success=True,
            data={
                "policies": [
                    {"id": i, "name": f"Policy {i}", "team_id": 1} for i in range(1, 6)
                ],
                "inherited_policies": [],
            },
            message="Success",
        )

        async def mock_get(endpoint, params=None):  # noqa: ARG001
            if endpoint == "/teams":
                return teams_response
            elif endpoint == "/teams/1/policies":
                return team1_policies_response
            return FleetResponse(success=False, message="Not found", data=None)

        with patch.object(fleet_client, "get", side_effect=mock_get):
            fleet_list_policies = registered_tools.get("fleet_list_policies")
            assert fleet_list_policies is not None

            # Get first page (2 items per page)
            result_page1 = await fleet_list_policies(
                search_all_teams=True, page=0, per_page=2
            )

            assert result_page1["success"] is True
            assert result_page1["count"] == 2
            assert result_page1["total_count"] == 5
            assert result_page1["page"] == 0
            assert result_page1["per_page"] == 2

            # Get second page
            result_page2 = await fleet_list_policies(
                search_all_teams=True, page=1, per_page=2
            )

            assert result_page2["success"] is True
            assert result_page2["count"] == 2
            assert result_page2["total_count"] == 5
            assert result_page2["page"] == 1

    @pytest.mark.asyncio
    async def test_search_all_teams_failed_teams_fetch(self, fleet_client, mock_mcp):
        """Test error handling when fetching teams fails."""
        registered_tools = {}

        def mock_tool_decorator():
            def decorator(func):
                registered_tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = mock_tool_decorator
        policy_tools.register_read_tools(mock_mcp, fleet_client)

        # Mock failed teams response
        teams_response = FleetResponse(
            success=False,
            message="Failed to fetch teams",
            data=None,
        )

        async def mock_get(endpoint, params=None):  # noqa: ARG001
            if endpoint == "/teams":
                return teams_response
            return FleetResponse(success=False, message="Not found", data=None)

        with patch.object(fleet_client, "get", side_effect=mock_get):
            fleet_list_policies = registered_tools.get("fleet_list_policies")
            assert fleet_list_policies is not None
            result = await fleet_list_policies(search_all_teams=True)

            assert result["success"] is False
            assert "Failed to fetch teams" in result["message"]
            assert result["policies"] == []
            assert result["count"] == 0
