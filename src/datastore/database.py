import os
import sqlite3

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./orchestrator.db")

def get_db_connection():
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def execute_query(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def fetch_one(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return cursor.fetchone()
    finally:
        conn.close()

def fetch_all(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        conn.close()
