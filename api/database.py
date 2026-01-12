import psycopg2
from psycopg2.extras import RealDictCursor
from django.conf import settings
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Database connection context manager"""
    conn = psycopg2.connect(settings.DATABASE_CONFIG['url'])
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_query(query, params=None, fetch_one=False):
    """Execute query and return results"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            if fetch_one:
                return dict(cursor.fetchone()) if cursor.rowcount > 0 else None
            return [dict(row) for row in cursor.fetchall()] if cursor.rowcount > 0 else []

def execute_insert(query, params=None):
    """Execute insert and return the created record (if RETURNING is used)"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())

            # RETURNING байвал л fetch хийнэ
            if cursor.description:
                row = cursor.fetchone()
                return dict(row) if row else None

            return None

def execute_update(query, params=None):
    """Execute update and return the affected rows count"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount

def execute_delete(query, params=None):
    """Execute delete and return the affected rows count"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount
