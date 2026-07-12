"""Admin functions for DB stats and diagnostics."""
from __future__ import annotations
import os
import sqlite3
import pandas as pd
from pathlib import Path

from streamlit_app.config import DB_PATH
from streamlit_app.database import get_db_connection, get_last_etl_date

def get_database_statistics() -> dict:
    """Get database file size, row counts, and update timestamps."""
    stats = {
        "db_size_mb": 0.0,
        "total_tables": 0,
        "table_counts": {},
        "last_nav_update": "N/A",
        "last_transaction_date": "N/A",
        "last_etl_date": "N/A",
        "status": "Healthy"
    }
    
    # DB File Size
    if DB_PATH.exists():
        size_bytes = DB_PATH.stat().st_size
        stats["db_size_mb"] = size_bytes / (1024 * 1024)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total Tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        stats["total_tables"] = len(tables)
        
        # Row counts for core tables
        core_tables = [
            "dim_fund", "dim_date", "fact_nav", "fact_transactions", 
            "fact_performance", "stg_portfolio_holdings", "stg_monthly_sip_inflows", "stg_benchmark_indices"
        ]
        for tbl in core_tables:
            if tbl in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                stats["table_counts"][tbl] = cursor.fetchone()[0]
            else:
                stats["table_counts"][tbl] = 0
                
        # Last NAV Update
        if "fact_nav" in tables:
            cursor.execute("""
                SELECT MAX(d.full_date) 
                FROM fact_nav n
                JOIN dim_date d ON n.date_id = d.date_id
            """)
            val = cursor.fetchone()[0]
            if val:
                stats["last_nav_update"] = str(val).split(" ")[0]
            else:
                stats["last_nav_update"] = "N/A"
            
        # Last Transaction Date
        if "fact_transactions" in tables:
            cursor.execute("""
                SELECT MAX(d.full_date) 
                FROM fact_transactions t
                JOIN dim_date d ON t.date_id = d.date_id
            """)
            val = cursor.fetchone()[0]
            if val:
                stats["last_transaction_date"] = str(val).split(" ")[0]
            else:
                stats["last_transaction_date"] = "N/A"
            
        # Last ETL Date
        stats["last_etl_date"] = get_last_etl_date() or "N/A"
        
    except sqlite3.Error:
        stats["status"] = "Degraded"
    finally:
        conn.close()
        
    return stats


def load_system_logs() -> pd.DataFrame:
    """Load simulated platform system event logs."""
    logs_data = [
        {"Timestamp": "2026-07-09 10:00:00", "Component": "ETL Pipeline", "Level": "INFO", "Message": "ETL Scheduled Update finished successfully. Ingested 12 new NAV daily marks."},
        {"Timestamp": "2026-07-09 09:30:15", "Component": "Cache Handler", "Level": "INFO", "Message": "Cleared memory cache tables for pages/4_Risk_Analytics."},
        {"Timestamp": "2026-07-09 08:15:22", "Component": "DB Connection", "Level": "INFO", "Message": "Connection established with bluestock_mf.db successfully."},
        {"Timestamp": "2026-07-08 23:59:59", "Component": "ETL Pipeline", "Level": "INFO", "Message": "Database backup completed. Size: 5.2 MB."},
        {"Timestamp": "2026-07-08 14:22:01", "Component": "Reports Engine", "Level": "WARNING", "Message": "PDF generation warning: truncating column name 'daily_return_pct'."},
        {"Timestamp": "2026-07-08 12:10:44", "Component": "Platform Core", "Level": "INFO", "Message": "User login session verified successfully."}
    ]
    return pd.DataFrame(logs_data)


def recompute_analytics_cache() -> str:
    """Clear memory caches."""
    import streamlit as st
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
        return "Cache cleared successfully!"
    except Exception as e:
        return f"Error clearing cache: {str(e)}"
