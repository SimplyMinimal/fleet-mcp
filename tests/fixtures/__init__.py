"""Shared test fixtures for Fleet MCP tests."""

from .test_data import (
    NONEXISTENT_IDENTIFIERS,
    TEST_ENCRYPTION_KEYS,
    TEST_ERROR_MESSAGES,
    TEST_HOSTS,
    TEST_QUERY_RESULTS,
    get_test_host,
    get_test_query_result,
)

__all__ = [
    "TEST_HOSTS",
    "TEST_ENCRYPTION_KEYS",
    "TEST_QUERY_RESULTS",
    "TEST_ERROR_MESSAGES",
    "NONEXISTENT_IDENTIFIERS",
    "get_test_host",
    "get_test_query_result",
]
