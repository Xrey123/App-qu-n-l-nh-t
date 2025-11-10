"""
Improved Database Connection Management with Connection Pooling

Features:
- Connection pooling to avoid creating new connections repeatedly
- Context manager for automatic connection cleanup
- Automatic retry on database lock
- Better error handling
"""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)

DB_NAME = "fapp.db"

# Connection pool
_connection_pool = []
_pool_lock = threading.Lock()
_pool_max_size = 10


class DatabaseError(Exception):
    """Base exception for database operations"""

    pass


class ConnectionPoolError(DatabaseError):
    """Exception for connection pool issues"""

    pass


def get_connection(timeout: float = 30.0) -> sqlite3.Connection:
    """
    Get a database connection from the pool or create a new one.

    Args:
        timeout: Database lock timeout in seconds

    Returns:
        sqlite3.Connection instance

    Raises:
        ConnectionPoolError: If unable to get connection
    """
    with _pool_lock:
        # Try to reuse existing connection from pool
        if _connection_pool:
            conn = _connection_pool.pop()
            try:
                # Test if connection is still valid
                conn.execute("SELECT 1")
                logger.debug("Reused connection from pool")
                return conn
            except sqlite3.Error as e:
                logger.warning(f"Stale connection in pool, creating new one: {e}")

        # Create new connection
        try:
            conn = sqlite3.connect(DB_NAME, timeout=timeout)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            logger.debug("Created new database connection")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to create database connection: {e}", exc_info=True)
            raise ConnectionPoolError(f"Unable to connect to database: {e}")


def release_connection(conn: sqlite3.Connection):
    """
    Release a connection back to the pool.

    Args:
        conn: Connection to release
    """
    if conn is None:
        return

    with _pool_lock:
        if len(_connection_pool) < _pool_max_size:
            _connection_pool.append(conn)
            logger.debug("Released connection back to pool")
        else:
            # Pool is full, close the connection
            try:
                conn.close()
                logger.debug("Closed connection (pool full)")
            except sqlite3.Error as e:
                logger.warning(f"Error closing connection: {e}")


@contextmanager
def get_db_connection(timeout: float = 30.0):
    """
    Context manager for database connections.
    Automatically releases connection when done.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Users")
            results = cursor.fetchall()

    Args:
        timeout: Database lock timeout in seconds

    Yields:
        sqlite3.Connection instance
    """
    conn = None
    try:
        conn = get_connection(timeout)
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}", exc_info=True)
        if conn:
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
        raise DatabaseError(f"Database operation failed: {e}")
    finally:
        if conn:
            release_connection(conn)


def ket_noi():
    """
    Legacy function for backward compatibility.
    Returns a connection that MUST be closed manually.

    DEPRECATED: Use get_db_connection() context manager instead.
    """
    return get_connection()


def clear_connection_pool():
    """Close all connections in the pool (for cleanup)"""
    with _pool_lock:
        while _connection_pool:
            conn = _connection_pool.pop()
            try:
                conn.close()
            except sqlite3.Error as e:
                logger.warning(f"Error closing pooled connection: {e}")
        logger.info("Connection pool cleared")


# Auto-cleanup on module unload
import atexit

atexit.register(clear_connection_pool)
