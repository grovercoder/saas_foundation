import os
import sqlite3


def get_db_connection(logger):
    db_path = os.getenv("DB_PATH", "./data")
    db_name = os.getenv("DB_NAME", "application.db")

    if db_name == ":memory:":
        full_db_path = ":memory:"
    elif db_path == "":  # Handle empty DB_PATH for non-memory databases
        # If DB_PATH is empty and DB_NAME is not :memory:, it implies an attempt to create a file-based DB in the current directory.
        # This is likely unintended during testing, so we raise an error.
        raise ValueError(
            "DB_PATH cannot be empty for file-based databases. Set DB_PATH or use :memory: for DB_NAME."
        )
    else:
        # Ensure the directory exists only for file-based databases
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        full_db_path = os.path.join(db_path, db_name)

    conn = sqlite3.connect(full_db_path)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn


def execute_query(query, params=(), conn=None, logger=None):
    if conn is None:
        conn = get_db_connection(logger)
        close_conn = True
    else:
        close_conn = False

    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        if close_conn:
            conn.close()


def fetch_one(query, params=(), conn=None, logger=None):
    if conn is None:
        conn = get_db_connection(logger)
        close_conn = True
    else:
        close_conn = False

    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return cursor.fetchone()
    finally:
        if close_conn:
            conn.close()


def fetch_all(query, params=(), conn=None, logger=None):
    if conn is None:
        conn = get_db_connection(logger)
        close_conn = True
    else:
        close_conn = False

    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        if close_conn:
            conn.close()
