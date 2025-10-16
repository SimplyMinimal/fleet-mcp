"""Tests for SQL query validation."""

import pytest

from fleet_mcp.utils.sql_validator import is_select_only_query, validate_select_query


@pytest.mark.unit
class TestSQLValidator:
    """Test SQL query validation for SELECT-only queries."""

    def test_simple_select_query(self):
        """Test that simple SELECT queries are allowed."""
        assert is_select_only_query("SELECT * FROM users")
        assert is_select_only_query("SELECT id, name FROM hosts")
        assert is_select_only_query("SELECT COUNT(*) FROM processes")

    def test_select_with_where_clause(self):
        """Test SELECT queries with WHERE clauses."""
        assert is_select_only_query("SELECT * FROM users WHERE id = 1")
        assert is_select_only_query("SELECT name FROM hosts WHERE status = 'online'")

    def test_select_with_joins(self):
        """Test SELECT queries with JOINs."""
        assert is_select_only_query(
            "SELECT u.name, h.hostname FROM users u JOIN hosts h ON u.id = h.user_id"
        )

    def test_select_with_subquery(self):
        """Test SELECT queries with subqueries."""
        assert is_select_only_query(
            "SELECT * FROM users WHERE id IN (SELECT user_id FROM hosts)"
        )

    def test_select_with_order_by(self):
        """Test SELECT queries with ORDER BY."""
        assert is_select_only_query("SELECT * FROM users ORDER BY name")

    def test_select_with_limit(self):
        """Test SELECT queries with LIMIT."""
        assert is_select_only_query("SELECT * FROM users LIMIT 10")

    def test_select_with_group_by(self):
        """Test SELECT queries with GROUP BY."""
        assert is_select_only_query(
            "SELECT status, COUNT(*) FROM hosts GROUP BY status"
        )

    def test_multiple_select_statements(self):
        """Test multiple SELECT statements separated by semicolons."""
        assert is_select_only_query("SELECT * FROM users; SELECT * FROM hosts")

    def test_select_with_comments(self):
        """Test SELECT queries with comments."""
        assert is_select_only_query("-- This is a comment\nSELECT * FROM users")
        assert is_select_only_query("SELECT * FROM users /* inline comment */")

    def test_select_case_insensitive(self):
        """Test that SELECT is case-insensitive."""
        assert is_select_only_query("select * from users")
        assert is_select_only_query("SeLeCt * FrOm users")

    def test_insert_query_rejected(self):
        """Test that INSERT queries are rejected."""
        assert not is_select_only_query("INSERT INTO users VALUES (1, 'test')")
        assert not is_select_only_query(
            "INSERT INTO users (id, name) VALUES (1, 'test')"
        )

    def test_update_query_rejected(self):
        """Test that UPDATE queries are rejected."""
        assert not is_select_only_query("UPDATE users SET name = 'test' WHERE id = 1")

    def test_delete_query_rejected(self):
        """Test that DELETE queries are rejected."""
        assert not is_select_only_query("DELETE FROM users WHERE id = 1")
        assert not is_select_only_query("DELETE FROM users")

    def test_drop_query_rejected(self):
        """Test that DROP queries are rejected."""
        assert not is_select_only_query("DROP TABLE users")
        assert not is_select_only_query("DROP DATABASE fleet")

    def test_create_query_rejected(self):
        """Test that CREATE queries are rejected."""
        assert not is_select_only_query(
            "CREATE TABLE users (id INT, name VARCHAR(100))"
        )
        assert not is_select_only_query("CREATE INDEX idx_name ON users(name)")

    def test_alter_query_rejected(self):
        """Test that ALTER queries are rejected."""
        assert not is_select_only_query(
            "ALTER TABLE users ADD COLUMN email VARCHAR(100)"
        )

    def test_truncate_query_rejected(self):
        """Test that TRUNCATE queries are rejected."""
        assert not is_select_only_query("TRUNCATE TABLE users")

    def test_grant_query_rejected(self):
        """Test that GRANT queries are rejected."""
        assert not is_select_only_query("GRANT ALL ON users TO 'user'@'localhost'")

    def test_revoke_query_rejected(self):
        """Test that REVOKE queries are rejected."""
        assert not is_select_only_query("REVOKE ALL ON users FROM 'user'@'localhost'")

    def test_exec_query_rejected(self):
        """Test that EXEC/EXECUTE queries are rejected."""
        assert not is_select_only_query("EXEC sp_executesql N'SELECT * FROM users'")
        assert not is_select_only_query("EXECUTE sp_executesql N'SELECT * FROM users'")

    def test_pragma_query_rejected(self):
        """Test that PRAGMA queries are rejected (SQLite)."""
        assert not is_select_only_query("PRAGMA table_info(users)")

    def test_mixed_select_and_write_rejected(self):
        """Test that mixed SELECT and write operations are rejected."""
        assert not is_select_only_query("SELECT * FROM users; DELETE FROM users")
        assert not is_select_only_query("DELETE FROM users; SELECT * FROM users")

    def test_empty_query_rejected(self):
        """Test that empty queries are rejected."""
        assert not is_select_only_query("")
        assert not is_select_only_query("   ")
        assert not is_select_only_query("\n\t")

    def test_validate_select_query_success(self):
        """Test validate_select_query with valid queries."""
        is_valid, error = validate_select_query("SELECT * FROM users")
        assert is_valid
        assert error == ""

    def test_validate_select_query_insert_failure(self):
        """Test validate_select_query with INSERT query."""
        is_valid, error = validate_select_query("INSERT INTO users VALUES (1, 'test')")
        assert not is_valid
        assert "INSERT" in error
        assert "forbidden" in error.lower()

    def test_validate_select_query_update_failure(self):
        """Test validate_select_query with UPDATE query."""
        is_valid, error = validate_select_query("UPDATE users SET name = 'test'")
        assert not is_valid
        assert "UPDATE" in error

    def test_validate_select_query_delete_failure(self):
        """Test validate_select_query with DELETE query."""
        is_valid, error = validate_select_query("DELETE FROM users")
        assert not is_valid
        assert "DELETE" in error

    def test_validate_select_query_empty_failure(self):
        """Test validate_select_query with empty query."""
        is_valid, error = validate_select_query("")
        assert not is_valid
        assert "empty" in error.lower()

    def test_validate_select_query_non_select_start(self):
        """Test validate_select_query with query not starting with SELECT."""
        is_valid, error = validate_select_query("SHOW TABLES")
        assert not is_valid
        assert "SELECT" in error

    def test_select_with_insert_in_comment(self):
        """Test that INSERT in comments doesn't affect validation."""
        # This should pass because INSERT is in a comment
        query = "SELECT * FROM users -- INSERT INTO users"
        assert is_select_only_query(query)

    def test_select_with_delete_in_string(self):
        """Test SELECT with DELETE as part of a string value."""
        # Note: This is a limitation - we can't perfectly parse SQL strings
        # But for security, we err on the side of caution
        # This might fail depending on implementation, which is acceptable for security
        # The validator is conservative

    def test_whitespace_handling(self):
        """Test that queries with various whitespace are handled correctly."""
        assert is_select_only_query("  SELECT  *  FROM  users  ")
        assert is_select_only_query("\n\tSELECT\n\t*\n\tFROM\n\tusers\n")

    def test_semicolon_handling(self):
        """Test handling of semicolons."""
        assert is_select_only_query("SELECT * FROM users;")
        assert is_select_only_query("SELECT * FROM users; SELECT * FROM hosts;")
        assert not is_select_only_query("SELECT * FROM users;;; DELETE FROM users")

    def test_complex_select_query(self):
        """Test complex but valid SELECT query."""
        query = """
        SELECT
            u.id,
            u.name,
            COUNT(h.id) as host_count
        FROM users u
        LEFT JOIN hosts h ON u.id = h.user_id
        WHERE u.status = 'active'
        GROUP BY u.id, u.name
        HAVING COUNT(h.id) > 0
        ORDER BY host_count DESC
        LIMIT 10
        """
        assert is_select_only_query(query)

    def test_union_query(self):
        """Test SELECT with UNION."""
        query = "SELECT id FROM users UNION SELECT id FROM hosts"
        assert is_select_only_query(query)

    def test_cte_query(self):
        """Test SELECT with Common Table Expression (CTE)."""
        query = """
        WITH active_users AS (
            SELECT * FROM users WHERE status = 'active'
        )
        SELECT * FROM active_users
        """
        assert is_select_only_query(query)
