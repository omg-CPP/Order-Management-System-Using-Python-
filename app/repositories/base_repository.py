"""Base repository with common database operations."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator, Optional

from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursorDict

from app.repositories.db_pool import get_db_pool


class MySQLBaseRepository:
    """Base class for MySQL repositories with common operations."""

    def _get_connection(self) -> MySQLConnection:
        """Get a connection from the pool."""
        return get_db_pool().get_connection()

    def _execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        """Execute a SELECT query and return results as dicts."""
        conn = self._get_connection()
        cursor: MySQLCursorDict = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            results = cursor.fetchall()
            return [dict(row) for row in results]
        finally:
            cursor.close()
            conn.close()

    def _execute_insert(
        self,
        query: str,
        params: Optional[tuple] = None,
    ) -> Optional[int]:
        """Execute an INSERT query and return the last insert ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def _execute_update(
        self,
        query: str,
        params: Optional[tuple] = None,
    ) -> int:
        """Execute an UPDATE/DELETE query and return affected row count."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    @contextmanager
    def _transaction(self) -> Generator[tuple[MySQLConnection, MySQLCursorDict], None, None]:
        """Context manager for transactions with explicit commit/rollback."""
        conn = self._get_connection()
        cursor: MySQLCursorDict = conn.cursor(dictionary=True)
        try:
            yield conn, cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def _count(
        self,
        table: str,
        where_clause: str = "",
        params: Optional[tuple] = None,
    ) -> int:
        """Count rows in a table with optional WHERE clause."""
        query = f"SELECT COUNT(*) as count FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"

        result = self._execute_query(query, params, fetch_one=True)
        return result["count"] if result else 0
