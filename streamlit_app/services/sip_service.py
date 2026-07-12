"""Business logic for SIP & Market Trends."""
from __future__ import annotations
import sqlite3
import pandas as pd
import numpy as np

from streamlit_app.config import DB_PATH
from streamlit_app.database import get_db_connection

def load_sip_market_data() -> pd.DataFrame:
    """Fetch monthly SIP inflow figures and NIFTY 50 index closes."""
    conn = get_db_connection()
    query = """
    SELECT 
        strftime('%Y-%m', s.month) AS month_str,
        s.sip_inflow_crore,
        s.active_sip_accounts_crore,
        s.new_sip_accounts_lakh,
        s.sip_aum_lakh_crore,
        s.yoy_growth_pct,
        s.yoy_anomaly,
        n.nifty_close
    FROM stg_monthly_sip_inflows s
    LEFT JOIN (
        SELECT 
            strftime('%Y-%m', date) AS month_str,
            close_value AS nifty_close
        FROM stg_benchmark_indices b1
        WHERE index_name = 'NIFTY50'
          AND date = (
              SELECT MAX(date) 
              FROM stg_benchmark_indices b2 
              WHERE b2.index_name = 'NIFTY50' 
                AND strftime('%Y-%m', b2.date) = strftime('%Y-%m', b1.date)
          )
    ) n ON strftime('%Y-%m', s.month) = n.month_str
    ORDER BY s.month ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    for col in ["sip_inflow_crore", "active_sip_accounts_crore", "new_sip_accounts_lakh", "sip_aum_lakh_crore", "yoy_growth_pct", "nifty_close"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    if not df.empty and "month_str" in df.columns:
        dates = pd.to_datetime(df["month_str"] + "-01")
        df["year"] = dates.dt.strftime("%Y")
        df["quarter"] = dates.dt.to_period("Q").astype(str).str[-2:]
        
    return df


def load_category_inflows_data() -> pd.DataFrame:
    """Fetch category net inflows from SQLite."""
    conn = get_db_connection()
    query = """
    SELECT 
        strftime('%Y-%m', month) AS month_str,
        category,
        net_inflow_crore
    FROM stg_category_inflows
    ORDER BY month ASC, category ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df["net_inflow_crore"] = pd.to_numeric(df["net_inflow_crore"], errors="coerce")
        dates = pd.to_datetime(df["month_str"] + "-01")
        df["year"] = dates.dt.strftime("%Y")
        df["quarter"] = dates.dt.to_period("Q").astype(str).str[-2:]
        
    return df


def get_filter_options(sip_df: pd.DataFrame, cat_df: pd.DataFrame) -> dict:
    """Extract options for filters."""
    years = set()
    quarters = set()
    categories = set()
    
    for df in [sip_df, cat_df]:
        if not df.empty:
            if "year" in df.columns:
                years.update(df["year"].dropna().unique())
            if "quarter" in df.columns:
                quarters.update(df["quarter"].dropna().unique())
                
    if not cat_df.empty and "category" in cat_df.columns:
        categories.update(cat_df["category"].dropna().unique())
        
    return {
        "years": sorted(list(years)),
        "quarters": sorted(list(quarters)),
        "categories": sorted(list(categories))
    }


def filter_sip_data(
    sip_df: pd.DataFrame,
    years: list[str] = None,
    quarters: list[str] = None
) -> pd.DataFrame:
    """Filter SIP inflows by Year and Quarter."""
    filtered = sip_df.copy()
    if years:
        filtered = filtered[filtered["year"].isin(years)]
    if quarters:
        filtered = filtered[filtered["quarter"].isin(quarters)]
    return filtered


def filter_cat_data(
    cat_df: pd.DataFrame,
    years: list[str] = None,
    categories: list[str] = None,
    quarters: list[str] = None
) -> pd.DataFrame:
    """Filter Category net inflows."""
    filtered = cat_df.copy()
    if years:
        filtered = filtered[filtered["year"].isin(years)]
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]
    if quarters:
        filtered = filtered[filtered["quarter"].isin(quarters)]
    return filtered


def calculate_sip_kpis(sip_df: pd.DataFrame) -> dict:
    """Calculate standard KPIs for SIP data."""
    if sip_df.empty:
        return {
            "latest_inflow": 0.0,
            "total_inflow": 0.0,
            "highest_inflow_val": 0.0,
            "highest_inflow_month": "N/A",
            "yoy_growth": 0.0
        }
        
    latest_row = sip_df.iloc[-1]
    high_idx = sip_df["sip_inflow_crore"].idxmax()
    high_row = sip_df.loc[high_idx]
    
    return {
        "latest_inflow": float(latest_row["sip_inflow_crore"]) if not pd.isna(latest_row["sip_inflow_crore"]) else 0.0,
        "total_inflow": float(sip_df["sip_inflow_crore"].sum()),
        "highest_inflow_val": float(high_row["sip_inflow_crore"]),
        "highest_inflow_month": str(high_row["month_str"]),
        "yoy_growth": float(latest_row["yoy_growth_pct"]) if not pd.isna(latest_row["yoy_growth_pct"]) else 0.0
    }


def get_top_categories_fy25(cat_df: pd.DataFrame) -> pd.DataFrame:
    """Find top 5 categories with largest net inflows in FY25."""
    if cat_df.empty:
        return pd.DataFrame(columns=["category", "total_inflow"])
        
    fy25_df = cat_df[(cat_df["month_str"] >= "2024-04") & (cat_df["month_str"] <= "2025-03")]
    
    if fy25_df.empty:
        last_12 = sorted(cat_df["month_str"].unique())[-12:]
        fy25_df = cat_df[cat_df["month_str"].isin(last_12)]
        
    grouped = fy25_df.groupby("category")["net_inflow_crore"].sum().reset_index(name="total_inflow")
    grouped = grouped.sort_values("total_inflow", ascending=False).head(5).reset_index(drop=True)
    return grouped


def generate_category_summary_table(cat_df: pd.DataFrame) -> pd.DataFrame:
    """Generate summary details by category."""
    if cat_df.empty:
        return pd.DataFrame(columns=["Category", "Net Inflow", "Avg Monthly Inflow", "YoY Growth", "Market Share"])
        
    total_inflow = cat_df.groupby("category")["net_inflow_crore"].sum().reset_index()
    total_all_categories = total_inflow["net_inflow_crore"].sum()
    
    avg_inflow = cat_df.groupby("category")["net_inflow_crore"].mean().reset_index(name="avg_inflow")
    
    unique_months = sorted(cat_df["month_str"].unique())
    yoy_growth_map = {}
    
    if len(unique_months) >= 24:
        last_12 = unique_months[-12:]
        prec_12 = unique_months[-24:-12]
        
        for cat in cat_df["category"].unique():
            cat_rows = cat_df[cat_df["category"] == cat]
            last_sum = cat_rows[cat_rows["month_str"].isin(last_12)]["net_inflow_crore"].sum()
            prec_sum = cat_rows[cat_rows["month_str"].isin(prec_12)]["net_inflow_crore"].sum()
            
            if prec_sum > 0:
                growth = (last_sum - prec_sum) / prec_sum * 100.0
            else:
                growth = 0.0
            yoy_growth_map[cat] = growth
    else:
        for cat in cat_df["category"].unique():
            yoy_growth_map[cat] = 0.0
            
    summary = total_inflow.merge(avg_inflow, on="category")
    summary["yoy_growth"] = summary["category"].map(lambda x: yoy_growth_map.get(x, 0.0))
    
    if total_all_categories > 0:
        summary["market_share"] = (summary["net_inflow_crore"] / total_all_categories) * 100.0
    else:
        summary["market_share"] = 0.0
        
    summary = summary.rename(columns={
        "category": "Category",
        "net_inflow_crore": "Net Inflow",
        "avg_inflow": "Avg Monthly Inflow",
        "yoy_growth": "YoY Growth",
        "market_share": "Market Share"
    })
    
    return summary.sort_values("Net Inflow", ascending=False).reset_index(drop=True)


def generate_sip_insights(sip_df: pd.DataFrame, cat_df: pd.DataFrame) -> dict:
    """Generate simple insights from SIP and Category data."""
    default_vals = {
        "highest_sip_month": "N/A", "highest_sip_val": 0.0,
        "lowest_sip_month": "N/A", "lowest_sip_val": 0.0,
        "highest_growth_month": "N/A", "highest_growth_val": 0.0,
        "best_performing_category": "N/A", "best_category_val": 0.0,
        "largest_net_inflow_category": "N/A", "largest_net_inflow_val": 0.0,
        "market_relationship": "Weak or No Correlation", "correlation_coef": 0.0
    }
    
    if sip_df.empty:
        return default_vals
        
    insights = default_vals.copy()
    
    high_idx = sip_df["sip_inflow_crore"].idxmax()
    high_row = sip_df.loc[high_idx]
    insights["highest_sip_month"] = str(high_row["month_str"])
    insights["highest_sip_val"] = float(high_row["sip_inflow_crore"])
    
    low_idx = sip_df["sip_inflow_crore"].idxmin()
    low_row = sip_df.loc[low_idx]
    insights["lowest_sip_month"] = str(low_row["month_str"])
    insights["lowest_sip_val"] = float(low_row["sip_inflow_crore"])
    
    if "yoy_growth_pct" in sip_df.columns and not sip_df["yoy_growth_pct"].isna().all():
        growth_idx = sip_df["yoy_growth_pct"].idxmax()
        growth_row = sip_df.loc[growth_idx]
        insights["highest_growth_month"] = str(growth_row["month_str"])
        insights["highest_growth_val"] = float(growth_row["yoy_growth_pct"])
        
    if not cat_df.empty:
        cat_sums = cat_df.groupby("category")["net_inflow_crore"].sum().reset_index()
        if not cat_sums.empty:
            cat_sums = cat_sums.sort_values("net_inflow_crore", ascending=False)
            top_cat = cat_sums.iloc[0]
            insights["best_performing_category"] = top_cat["category"]
            insights["best_category_val"] = float(top_cat["net_inflow_crore"])
            insights["largest_net_inflow_category"] = top_cat["category"]
            insights["largest_net_inflow_val"] = float(top_cat["net_inflow_crore"])
            
    valid_corr = sip_df.dropna(subset=["sip_inflow_crore", "nifty_close"])
    if len(valid_corr) >= 5:
        coef = valid_corr["sip_inflow_crore"].corr(valid_corr["nifty_close"])
        insights["correlation_coef"] = float(coef)
        
        if coef > 0.75:
            insights["market_relationship"] = "Strong Positive Correlation"
        elif coef > 0.4:
            insights["market_relationship"] = "Moderate Positive Correlation"
        elif coef < -0.4:
            insights["market_relationship"] = "Negative Correlation"
        else:
            insights["market_relationship"] = "Weak or No Correlation"
            
    return insights
