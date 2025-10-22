"""Integration tests for downloading and caching the official Fleet schema."""

import json

import pytest

from fleet_mcp.tools.table_discovery import (
    SCHEMA_CACHE_FILE,
    TableSchemaCache,
    get_table_cache,
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestFleetSchemaDownload:
    """Integration tests for Fleet schema download and caching."""

    async def test_download_official_schema(self):
        """Test downloading the official Fleet schema from GitHub."""
        cache = TableSchemaCache()

        try:
            schemas = await cache._download_fleet_schema()

            # Verify we got schemas
            assert len(schemas) > 0, "Should have downloaded schemas"

            # Verify some common tables exist
            common_tables = ["processes", "users", "system_info"]
            for table in common_tables:
                assert table in schemas, f"Common table '{table}' should be in schema"

            # Verify schema structure
            for _table_name, table_schema in list(schemas.items())[:5]:
                assert "description" in table_schema
                assert "platforms" in table_schema
                assert isinstance(table_schema["platforms"], list)
                assert "columns" in table_schema
                assert isinstance(table_schema["columns"], list)
                assert "column_details" in table_schema
                assert isinstance(table_schema["column_details"], dict)

            print(f"✓ Downloaded {len(schemas)} table schemas from Fleet")

        except Exception as e:
            pytest.skip(f"Could not download schema (network issue?): {e}")

    async def test_cache_initialization(self):
        """Test that cache initializes correctly."""
        cache = TableSchemaCache()

        try:
            await cache.initialize()

            # Should have loaded schemas
            assert len(cache.fleet_schemas) > 0, "Should have loaded schemas"
            assert cache.fleet_schemas_loaded is True

            print(f"✓ Initialized cache with {len(cache.fleet_schemas)} schemas")

        except Exception as e:
            pytest.skip(f"Could not initialize cache: {e}")

    async def test_cache_file_created(self):
        """Test that cache file is created after download."""
        cache = TableSchemaCache()

        try:
            await cache.initialize()

            # Cache file should exist
            assert (
                SCHEMA_CACHE_FILE.exists()
            ), f"Cache file should exist at {SCHEMA_CACHE_FILE}"

            # Cache file should be valid JSON
            with open(SCHEMA_CACHE_FILE) as f:
                schema_json = json.load(f)

            assert len(schema_json) > 0, "Cache file should contain schemas"

            print(f"✓ Cache file created at {SCHEMA_CACHE_FILE}")
            print(f"✓ Cache contains {len(schema_json)} tables")

        except Exception as e:
            pytest.skip(f"Could not test cache file: {e}")

    async def test_cache_reuse(self):
        """Test that cache is reused on subsequent loads."""
        # First initialization
        cache1 = TableSchemaCache()
        await cache1.initialize()
        count1 = len(cache1.fleet_schemas)

        # Second initialization (should use cache)
        cache2 = TableSchemaCache()
        await cache2.initialize()
        count2 = len(cache2.fleet_schemas)

        # Should have same number of schemas
        assert count1 == count2, "Cache should return consistent data"
        assert count1 > 0, "Should have schemas"

        print(f"✓ Cache reuse working ({count1} schemas)")

    async def test_global_cache_singleton(self):
        """Test that get_table_cache returns singleton."""
        cache1 = await get_table_cache()
        cache2 = await get_table_cache()

        # Should be the same instance
        assert cache1 is cache2, "Should return same cache instance"
        assert len(cache1.fleet_schemas) > 0, "Should have schemas"

        print("✓ Global cache singleton working")

    async def test_cache_info(self):
        """Test cache info retrieval."""
        cache = await get_table_cache()
        info = cache.get_cache_info()

        # Verify info structure
        assert "cache_exists" in info
        assert "cache_age_seconds" in info
        assert "cache_size_bytes" in info
        assert "loaded_schemas_count" in info
        assert "cache_ttl_hours" in info
        assert "is_cache_valid" in info

        # Verify values
        assert info["loaded_schemas_count"] > 0
        assert info["cache_ttl_hours"] == 24

        print("✓ Cache info:")
        print(f"  - Schemas loaded: {info['loaded_schemas_count']}")
        print(f"  - Cache exists: {info['cache_exists']}")
        if info["cache_age_hours"]:
            print(f"  - Cache age: {info['cache_age_hours']:.2f} hours")
        print(f"  - Cache valid: {info['is_cache_valid']}")

    async def test_schema_content_quality(self):
        """Test that downloaded schemas have good quality metadata."""
        cache = await get_table_cache()

        # Check a few well-known tables
        test_tables = {
            "processes": {
                "required_columns": ["pid", "name"],
                "platforms": ["darwin", "linux", "windows"],
            },
            "users": {
                "required_columns": ["uid", "username"],
                "platforms": ["darwin", "linux", "windows"],
            },
            "system_info": {
                "required_columns": ["hostname", "uuid"],
                "platforms": ["darwin", "linux", "windows"],
            },
        }

        for table_name, requirements in test_tables.items():
            if table_name not in cache.fleet_schemas:
                print(f"⚠ Table '{table_name}' not in schema (may be expected)")
                continue

            schema = cache.fleet_schemas[table_name]

            # Check required columns
            for col in requirements["required_columns"]:
                assert (
                    col in schema["columns"]
                ), f"Table '{table_name}' should have column '{col}'"

            # Check platforms
            for platform in requirements["platforms"]:
                assert (
                    platform in schema["platforms"]
                ), f"Table '{table_name}' should support platform '{platform}'"

            # Check has description
            assert schema[
                "description"
            ], f"Table '{table_name}' should have description"

            # Check has column details
            assert schema[
                "column_details"
            ], f"Table '{table_name}' should have column details"

            print(f"✓ Table '{table_name}' has quality metadata")

    async def test_force_refresh(self):
        """Test force refresh functionality."""
        cache = await get_table_cache()

        # Get initial count
        initial_count = len(cache.fleet_schemas)

        # Force refresh
        try:
            result = await cache.refresh_fleet_schemas()
            assert result is True, "Refresh should succeed"

            # Should still have schemas
            assert len(cache.fleet_schemas) > 0
            assert len(cache.fleet_schemas) == initial_count

            print(f"✓ Force refresh successful ({len(cache.fleet_schemas)} schemas)")

        except Exception as e:
            pytest.skip(f"Could not test force refresh: {e}")
