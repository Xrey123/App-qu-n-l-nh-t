"""
Helper functions for database operations
Các hàm tiện ích cho thao tác database
"""

import sqlite3
from db import ket_noi
from contextlib import contextmanager
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseOperationError(Exception):
    """Raised when database operation fails"""
    pass


@contextmanager
def db_transaction():
    """
    Context manager để xử lý transaction database tự động
    Tự động commit khi thành công, rollback khi có lỗi

    Sử dụng:
        with db_transaction() as (conn, cursor):
            cursor.execute(...)
            # Tự động commit khi kết thúc block
    
    Raises:
        DatabaseOperationError: When database operation fails
    """
    conn = None
    try:
        conn = ket_noi()
        cursor = conn.cursor()
        yield conn, cursor
        conn.commit()
    except sqlite3.IntegrityError as e:
        if conn:
            conn.rollback()
        logger.error(f"Database integrity error: {e}", exc_info=True)
        raise DatabaseOperationError(f"Integrity constraint violated: {e}")
    except sqlite3.OperationalError as e:
        if conn:
            conn.rollback()
        logger.error(f"Database operational error: {e}", exc_info=True)
        raise DatabaseOperationError(f"Database operation failed: {e}")
    except sqlite3.DatabaseError as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise DatabaseOperationError(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Thực thi query đơn giản và trả về kết quả

    Args:
        query: SQL query string
        params: Tuple các tham số cho query
        fetch_one: True nếu muốn lấy 1 dòng kết quả
        fetch_all: True nếu muốn lấy tất cả kết quả

    Returns:
        Kết quả query hoặc None
    
    Raises:
        DatabaseOperationError: When query fails
    """
    conn = None
    try:
        conn = ket_noi()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None

        return result
    except sqlite3.Error as e:
        logger.error(f"Query execution failed: {e}\nQuery: {query}", exc_info=True)
        raise DatabaseOperationError(f"Query failed: {e}")
    finally:
        if conn:
            conn.close()


def execute_update(query, params=None):
    """
    Thực thi UPDATE/INSERT/DELETE query

    Args:
        query: SQL query string
        params: Tuple các tham số cho query

    Returns:
        True nếu thành công, False nếu thất bại
    """
    conn = None
    try:
        conn = ket_noi()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        logger.debug(f"Update successful: {query[:100]}")
        return True
    except sqlite3.IntegrityError as e:
        if conn:
            conn.rollback()
        logger.error(f"Integrity error in execute_update: {e}\nQuery: {query}", exc_info=True)
        return False
    except sqlite3.OperationalError as e:
        if conn:
            conn.rollback()
        logger.error(f"Operational error in execute_update: {e}\nQuery: {query}", exc_info=True)
        return False
    except sqlite3.DatabaseError as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error in execute_update: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()


def safe_execute(func):
    """
    Decorator để bọc try/except cho các hàm database
    Tự động xử lý lỗi và đóng connection
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DatabaseOperationError as e:
            logger.error(f"Database operation error in {func.__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return None

    return wrapper

