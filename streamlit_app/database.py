"""Database connection and utilities."""
import sqlite3
import logging
import datetime
from typing import Optional
from streamlit_app.config import DB_PATH

logger = logging.getLogger(__name__)

def get_db_connection() -> sqlite3.Connection:
    """Connect to SQLite database."""
    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database at {DB_PATH}: {e}")
        raise

def check_db_status() -> bool:
    """Check if database is connected."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def format_etl_date(date_str: str) -> str:
    """Format date string to human-readable format."""
    if not date_str:
        return "Unknown"
        
    date_str = date_str.strip()
    
    # Try parsing full datetime
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.strftime("%d %b %Y • %I:%M %p")
        except ValueError:
            continue
            
    # Try parsing just date
    try:
        dt = datetime.datetime.strptime(date_str.split(" ")[0], "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except ValueError:
        pass
        
    return date_str

def get_last_etl_date() -> Optional[str]:
    """Get the last ETL run date."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check metadata table first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='etl_metadata'")
        table_exists = cursor.fetchone()
        
        date_str = None
        if table_exists:
            cursor.execute("SELECT value FROM etl_metadata WHERE key='last_etl_run'")
            row = cursor.fetchone()
            if row and row[0]:
                date_str = str(row[0])
                
        # Fallback to dim_date
        if not date_str:
            cursor.execute("SELECT MAX(full_date) FROM dim_date")
            row = cursor.fetchone()
            if row and row[0]:
                date_str = str(row[0])
                
        conn.close()
        
        if date_str:
            return format_etl_date(date_str)
        return None
    except Exception as e:
        logger.error(f"Failed to get last ETL date: {e}")
        return None
