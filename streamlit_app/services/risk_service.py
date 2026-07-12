"""Risk Analytics business logic."""
from __future__ import annotations
import sqlite3
import pandas as pd
import numpy as np

from streamlit_app.config import DB_PATH
from streamlit_app.database import get_db_connection

def load_risk_data() -> pd.DataFrame:
    """Load fund risk metrics and performance details."""
    conn = get_db_connection()
    query = """
    SELECT
        f.fund_id,
        f.amfi_code,
        f.fund_house,
        f.scheme_name,
        f.category,
        f.sub_category,
        f.plan,
        f.benchmark,
        f.fund_manager,
        f.risk_category,
        p.return_1yr_pct,
        p.return_3yr_pct,
        p.return_5yr_pct,
        p.alpha,
        p.beta,
        p.sharpe_ratio,
        p.sortino_ratio,
        p.std_dev_ann_pct AS std_dev,
        p.max_drawdown_pct AS max_drawdown,
        p.aum_crore AS aum,
        p.expense_ratio_pct AS expense_ratio
    FROM dim_fund f
    JOIN fact_performance p ON f.fund_id = p.fund_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_filter_options(df: pd.DataFrame) -> dict:
    """Extract filter dropdown choices from risk dataset."""
    if df.empty:
        return {
            "fund_houses": [],
            "categories": [],
            "plans": [],
            "risk_categories": []
        }
    return {
        "fund_houses": sorted(df["fund_house"].dropna().unique().tolist()),
        "categories": sorted(df["category"].dropna().unique().tolist()),
        "plans": sorted(df["plan"].dropna().unique().tolist()),
        "risk_categories": sorted(df["risk_category"].dropna().unique().tolist())
    }


def filter_risk_data(
    df: pd.DataFrame,
    fund_houses: list[str] = None,
    categories: list[str] = None,
    plans: list[str] = None,
    risk_categories: list[str] = None
) -> pd.DataFrame:
    """Filter risk dataset in memory."""
    filtered = df.copy()
    if fund_houses:
        filtered = filtered[filtered["fund_house"].isin(fund_houses)]
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]
    if plans:
        filtered = filtered[filtered["plan"].isin(plans)]
    if risk_categories:
        filtered = filtered[filtered["risk_category"].isin(risk_categories)]
    return filtered


def calculate_risk_summary_statistics(df: pd.DataFrame) -> dict:
    """Calculate averages across standard risk metrics."""
    if df.empty:
        return {
            "avg_std_dev": 0.0,
            "avg_volatility": 0.0,
            "avg_sharpe": 0.0,
            "avg_sortino": 0.0,
            "avg_alpha": 0.0,
            "avg_beta": 0.0,
            "avg_max_drawdown": 0.0,
            "observations": 0
        }
        
    return {
        "avg_std_dev": float(df["std_dev"].mean()) if "std_dev" in df.columns and not df["std_dev"].isna().all() else 0.0,
        "avg_volatility": float(df["std_dev"].mean()) if "std_dev" in df.columns and not df["std_dev"].isna().all() else 0.0,
        "avg_sharpe": float(df["sharpe_ratio"].mean()) if "sharpe_ratio" in df.columns and not df["sharpe_ratio"].isna().all() else 0.0,
        "avg_sortino": float(df["sortino_ratio"].mean()) if "sortino_ratio" in df.columns and not df["sortino_ratio"].isna().all() else 0.0,
        "avg_alpha": float(df["alpha"].mean()) if "alpha" in df.columns and not df["alpha"].isna().all() else 0.0,
        "avg_beta": float(df["beta"].mean()) if "beta" in df.columns and not df["beta"].isna().all() else 0.0,
        "avg_max_drawdown": float(df["max_drawdown"].mean()) if "max_drawdown" in df.columns and not df["max_drawdown"].isna().all() else 0.0,
        "observations": len(df)
    }


def generate_risk_insights(df: pd.DataFrame) -> dict:
    """Extract standard performance risk highlights."""
    default_vals = {
        "lowest_risk_fund": "N/A", "lowest_risk_val": 0.0,
        "highest_sharpe_fund": "N/A", "highest_sharpe_val": 0.0,
        "highest_alpha_fund": "N/A", "highest_alpha_val": 0.0,
        "lowest_dd_fund": "N/A", "lowest_dd_val": 0.0,
        "best_risk_adj_fund": "N/A", "best_risk_adj_val": 0.0,
        "highest_vol_fund": "N/A", "highest_vol_val": 0.0,
        "highest_beta_fund": "N/A", "highest_beta_val": 0.0
    }
    
    if df.empty:
        return default_vals
        
    has_std = "std_dev" in df.columns and not df["std_dev"].isna().all()
    has_sharpe = "sharpe_ratio" in df.columns and not df["sharpe_ratio"].isna().all()
    has_alpha = "alpha" in df.columns and not df["alpha"].isna().all()
    has_dd = "max_drawdown" in df.columns and not df["max_drawdown"].isna().all()
    has_beta = "beta" in df.columns and not df["beta"].isna().all()
    has_sortino = "sortino_ratio" in df.columns and not df["sortino_ratio"].isna().all()
    
    insights = default_vals.copy()
    
    # Volatility
    if has_std:
        low_risk_idx = df["std_dev"].idxmin()
        insights["lowest_risk_fund"] = df.loc[low_risk_idx, "scheme_name"]
        insights["lowest_risk_val"] = float(df.loc[low_risk_idx, "std_dev"])
        
        high_vol_idx = df["std_dev"].idxmax()
        insights["highest_vol_fund"] = df.loc[high_vol_idx, "scheme_name"]
        insights["highest_vol_val"] = float(df.loc[high_vol_idx, "std_dev"])
        
    # Sharpe Ratio
    if has_sharpe:
        high_sharpe_idx = df["sharpe_ratio"].idxmax()
        insights["highest_sharpe_fund"] = df.loc[high_sharpe_idx, "scheme_name"]
        insights["highest_sharpe_val"] = float(df.loc[high_sharpe_idx, "sharpe_ratio"])
        
    # Alpha
    if has_alpha:
        high_alpha_idx = df["alpha"].idxmax()
        insights["highest_alpha_fund"] = df.loc[high_alpha_idx, "scheme_name"]
        insights["highest_alpha_val"] = float(df.loc[high_alpha_idx, "alpha"])
        
    # Max Drawdown
    if has_dd:
        low_dd_idx = df["max_drawdown"].idxmax()
        insights["lowest_dd_fund"] = df.loc[low_dd_idx, "scheme_name"]
        insights["lowest_dd_val"] = float(df.loc[low_dd_idx, "max_drawdown"])
        
    # Best Risk-adjusted (Sortino then Sharpe)
    if has_sortino:
        high_sortino_idx = df["sortino_ratio"].idxmax()
        insights["best_risk_adj_fund"] = df.loc[high_sortino_idx, "scheme_name"]
        insights["best_risk_adj_val"] = float(df.loc[high_sortino_idx, "sortino_ratio"])
    elif has_sharpe:
        insights["best_risk_adj_fund"] = insights["highest_sharpe_fund"]
        insights["best_risk_adj_val"] = insights["highest_sharpe_val"]
        
    # Beta
    if has_beta:
        high_beta_idx = df["beta"].idxmax()
        insights["highest_beta_fund"] = df.loc[high_beta_idx, "scheme_name"]
        insights["highest_beta_val"] = float(df.loc[high_beta_idx, "beta"])
        
    return insights
