"""MySQL connection pool singleton.

Provides a shared pool of database connections for efficient resource usage.
Connections are borrowed from and returned to the pool automatically.
"""

import logging
import threading
import time
from contextlib import contextmanager
from typing import Optional

import mysql.connector.pooling
from mysql.connector import MySQLConnection
from mysql.connector.pooling import PooledMySQLConnection

from app.config import settings

logger = logging.getLogger(__name__)


class DatabasePool:
    """Thread-safe singleton connection pool for MySQL."""

    _instance: Optional["DatabasePool"] = None
    _lock: threading.Lock = threading.Lock()
    _pool: Optional[mysql.connector.pooling.MySQLConnectionPool] = None
    _initialized: bool = False

    _active_connections: int = 0
    _total_connections_served: int = 0
    _connections_lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "DatabasePool":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def is_available(self) -> bool:
        """Check if the pool is available and ready for connections."""
        return self._pool is not None

    def initialize(self) -> None:
        """Create the underlying MySQL connection pool."""
        if DatabasePool._initialized:
            return

        with DatabasePool._lock:
            if DatabasePool._initialized:
                return

            try:
                self._pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name=settings.DB_POOL_NAME,
                    pool_size=settings.DB_POOL_SIZE,
                    pool_reset_session=True,
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USERNAME,
                    password=settings.DB_PASSWORD,
                    connection_timeout=settings.DB_CONNECTION_TIMEOUT,
                    charset="utf8mb4",
                    collation="utf8mb4_unicode_ci",
                    autocommit=False,
                    init_command="SET time_zone = '+00:00'",
                )
                DatabasePool._initialized = True
                logger.info(
                    "Database pool '%s' initialized (size=%s)",
                    settings.DB_POOL_NAME,
                    settings.DB_POOL_SIZE,
                )
            except Exception as exc:
                logger.warning("Database pool init failed: %s", exc)
                if not settings.ALLOW_DB_FAILURE:
                    raise

    def get_connection(self) -> MySQLConnection:
        """Get a connection from the pool."""
        if not self.is_available or not self._pool:
            raise RuntimeError("Database pool not available")

        conn = self._pool.get_connection()

        if settings.DB_POOL_LOG_CONNECTIONS:
            with self._connections_lock:
                DatabasePool._active_connections += 1
                DatabasePool._total_connections_served += 1
                active = DatabasePool._active_connections
                total = DatabasePool._total_connections_served

            thread_id = threading.current_thread().ident
            conn_id = id(conn)
            logger.debug(
                "BORROW conn_id=%d thread=%s pool=%s active=%d/%d total_served=%d",
                conn_id,
                thread_id,
                settings.DB_POOL_NAME,
                active,
                settings.DB_POOL_SIZE,
                total,
            )
            conn._pool_conn_id = conn_id
            conn._pool_borrow_time = time.time()

        return conn  # type: ignore[return-value]

    def return_connection(self, conn: PooledMySQLConnection) -> None:
        """Return a connection to the pool (called by conn.close())."""
        if conn is None:
            return

        if settings.DB_POOL_LOG_CONNECTIONS:
            with self._connections_lock:
                DatabasePool._active_connections = max(0, DatabasePool._active_connections - 1)
                active = DatabasePool._active_connections

            thread_id = threading.current_thread().ident
            conn_id = getattr(conn, "_pool_conn_id", id(conn))
            borrow_time = getattr(conn, "_pool_borrow_time", None)
            duration_ms = (time.time() - borrow_time) * 1000 if borrow_time else 0
            logger.debug(
                "RETURN conn_id=%d thread=%s pool=%s active=%d/%d held_for=%.1fms",
                conn_id,
                thread_id,
                settings.DB_POOL_NAME,
                active,
                settings.DB_POOL_SIZE,
                duration_ms,
            )

        try:
            conn.close()
        except Exception as e:
            logger.warning("Error returning connection to pool: %s", e)

    @contextmanager
    def connection(self):
        """Context manager for safely borrowing and returning connections."""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            if conn:
                self.return_connection(conn)

    def get_pool_stats(self) -> dict:
        """Get pool statistics for monitoring."""
        if not self._pool:
            return {
                "pool_name": None,
                "pool_size": 0,
                "is_available": False,
                "active_connections": 0,
                "total_connections_served": 0,
            }

        with self._connections_lock:
            active = DatabasePool._active_connections
            total = DatabasePool._total_connections_served

        return {
            "pool_name": settings.DB_POOL_NAME,
            "pool_size": settings.DB_POOL_SIZE,
            "is_available": self.is_available,
            "active_connections": active,
            "total_connections_served": total,
        }

    def close(self) -> None:
        """Close the pool and release resources."""
        with DatabasePool._lock:
            if settings.DB_POOL_LOG_CONNECTIONS:
                logger.info(
                    "Closing pool '%s'. Stats: total_served=%d",
                    settings.DB_POOL_NAME,
                    DatabasePool._total_connections_served,
                )
            self._pool = None
            DatabasePool._initialized = False
            DatabasePool._active_connections = 0
            logger.info("Database pool closed")


_db_pool: Optional[DatabasePool] = None


def get_db_pool() -> DatabasePool:
    """Get the global database pool instance (lazy initialization)."""
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool()
        _db_pool.initialize()
    return _db_pool


def close_db_pool() -> None:
    """Close the global database pool."""
    global _db_pool
    if _db_pool is not None:
        _db_pool.close()
        _db_pool = None
