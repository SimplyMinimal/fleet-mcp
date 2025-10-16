"""SQL query validation utilities for Fleet MCP.

This module provides utilities to validate SQL queries to ensure they are
read-only (SELECT statements only) and don't contain any data modification
operations.
"""

import re

# SQL keywords that indicate write operations
WRITE_KEYWORDS = {
    # Data modification
    "INSERT",
    "UPDATE",
    "DELETE",
    "REPLACE",
    "MERGE",
    "TRUNCATE",
    # Schema modification
    "CREATE",
    "ALTER",
    "DROP",
    "RENAME",
    # Transaction control (can be used for writes)
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    # Other potentially dangerous operations
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "CALL",
    # Pragma statements (SQLite-specific, can modify settings)
    "PRAGMA",
}


def is_select_only_query(query: str) -> bool:
    """Check if a SQL query is SELECT-only (read-only).

    This function validates that a query only contains SELECT statements
    and doesn't include any data or schema modification operations.

    Args:
        query: SQL query string to validate

    Returns:
        True if the query is SELECT-only, False otherwise

    Examples:
        >>> is_select_only_query("SELECT * FROM users")
        True
        >>> is_select_only_query("SELECT * FROM users; DELETE FROM users")
        False
        >>> is_select_only_query("INSERT INTO users VALUES (1, 'test')")
        False
    """
    if not query or not query.strip():
        return False

    # Normalize the query: remove comments and extra whitespace
    normalized = _normalize_query(query)

    # Split by semicolons to handle multiple statements
    statements = [s.strip() for s in normalized.split(";") if s.strip()]

    if not statements:
        return False

    # Check each statement
    for statement in statements:
        # Get the first keyword (should be SELECT)
        first_keyword = _get_first_keyword(statement)

        if first_keyword != "SELECT":
            return False

        # Check for write keywords anywhere in the statement
        if _contains_write_keywords(statement):
            return False

    return True


def validate_select_query(query: str) -> tuple[bool, str]:
    """Validate that a SQL query is SELECT-only and return detailed result.

    Args:
        query: SQL query string to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if query is SELECT-only, False otherwise
        - error_message: Empty string if valid, error description if invalid

    Examples:
        >>> validate_select_query("SELECT * FROM users")
        (True, "")
        >>> validate_select_query("DELETE FROM users")
        (False, "Query contains forbidden keyword: DELETE")
    """
    if not query or not query.strip():
        return False, "Query is empty"

    # Normalize the query
    normalized = _normalize_query(query)

    # Split by semicolons
    statements = [s.strip() for s in normalized.split(";") if s.strip()]

    if not statements:
        return False, "Query contains no valid statements"

    # Check each statement
    for _i, statement in enumerate(statements):
        # Get the first keyword
        first_keyword = _get_first_keyword(statement)

        if first_keyword != "SELECT":
            if first_keyword in WRITE_KEYWORDS:
                return False, f"Query contains forbidden keyword: {first_keyword}"
            else:
                return (
                    False,
                    f"Query must start with SELECT, found: {first_keyword or 'unknown'}",
                )

        # Check for write keywords in the statement
        found_keyword = _find_write_keyword(statement)
        if found_keyword:
            return False, f"Query contains forbidden keyword: {found_keyword}"

    return True, ""


def _normalize_query(query: str) -> str:
    """Normalize a SQL query by removing comments and extra whitespace.

    Args:
        query: Raw SQL query string

    Returns:
        Normalized query string
    """
    # Remove single-line comments (-- comment)
    query = re.sub(r"--[^\n]*", " ", query)

    # Remove multi-line comments (/* comment */)
    query = re.sub(r"/\*.*?\*/", " ", query, flags=re.DOTALL)

    # Replace multiple whitespace with single space
    query = re.sub(r"\s+", " ", query)

    return query.strip()


def _get_first_keyword(statement: str) -> str:
    """Extract the first SQL keyword from a statement.

    Args:
        statement: SQL statement string

    Returns:
        First keyword in uppercase, or empty string if none found
    """
    # Match the first word (alphanumeric + underscore)
    match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)", statement)
    if match:
        keyword = match.group(1).upper()
        # WITH is allowed as it's used for CTEs (Common Table Expressions) in SELECT queries
        if keyword == "WITH":
            return "SELECT"  # Treat WITH as SELECT since it's part of a SELECT query
        return keyword
    return ""


def _contains_write_keywords(statement: str) -> bool:
    """Check if a statement contains any write keywords.

    Args:
        statement: SQL statement string

    Returns:
        True if any write keywords are found, False otherwise
    """
    return _find_write_keyword(statement) is not None


def _find_write_keyword(statement: str) -> str | None:
    """Find the first write keyword in a statement.

    Args:
        statement: SQL statement string

    Returns:
        The first write keyword found, or None if none found
    """
    # Convert to uppercase for comparison
    upper_statement = statement.upper()

    # Check for each write keyword as a whole word
    for keyword in WRITE_KEYWORDS:
        # Use word boundaries to match whole words only
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, upper_statement):
            return keyword

    return None
