"""
Helper functions for database operations
Các hàm tiện ích cho thao tác database
"""
from db import ket_noi
from contextlib import contextmanager


@contextmanager
def db_transaction():
    """
    Context manager để xử lý transaction database tự động
    Tự động commit khi thành công, rollback khi có lỗi
    
    Sử dụng:
        with db_transaction() as (conn, cursor):
            cursor.execute(...)
            # Tự động commit khi kết thúc block
    """
    conn = ket_noi()
    cursor = conn.cursor()
    try:
        yield conn, cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
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
    """
    conn = ket_noi()
    cursor = conn.cursor()
    try:
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
    finally:
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
    conn = ket_noi()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Lỗi execute_update: {e}")
        return False
    finally:
        conn.close()


def safe_execute(func):
    """
    Decorator để bọc try/except cho các hàm database
    Tự động xử lý lỗi và đóng connection
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Lỗi trong {func.__name__}: {e}")
            return None
    return wrapper
