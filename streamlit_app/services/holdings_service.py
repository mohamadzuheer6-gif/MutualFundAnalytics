"""Business logic for Portfolio Holdings."""
from __future__ import annotations
import sqlite3
import pandas as pd
import numpy as np

from streamlit_app.config import DB_PATH
from streamlit_app.database import get_db_connection

def get_market_cap_category(stock_name: str) -> str:
    """Classify stocks by cap size based on name."""
    if not stock_name:
        return "Small Cap"
        
    name_lower = str(stock_name).lower()
    
    # Large Cap check
    large_keywords = ["hdfc", "icici", "infosys", "reliance", "tcs", "tata consultancy", 
                      "bharti airtel", "hcl", "larsen", "state bank", "sbi", "axis", "kotak", 
                      "itc", "hindustan unilever", "hul", "maruti", "ntpc", "power grid", "asian paints", 
                      "tata motors", "bajaj finance", "bajaj finserv", "ultratech", "l&t"]
    for kw in large_keywords:
        if kw in name_lower:
            return "Large Cap"
            
    # Mid Cap check
    mid_keywords = ["grasim", "dr. reddy", "divi", "cipla", "tata steel", "jsw", "hindalco", 
                    "apollo", "wipro", "tech mahindra", "sun pharma", "adani", "oil & natural", 
                    "ongc", "coal india", "bharat petroleum", "bpcl", "indian oil"]
    for kw in mid_keywords:
        if kw in name_lower:
            return "Mid Cap"
            
    return "Small Cap"


def get_asset_class(sector: str, stock_name: str) -> str:
    """Determine asset class (Equity, Debt, Cash)."""
    sec_lower = str(sector).lower() if sector else ""
    name_lower = str(stock_name).lower() if stock_name else ""
    
    if "cash" in sec_lower or "repo" in sec_lower or "call money" in sec_lower or "liquid" in sec_lower:
        return "Cash"
    elif "gilt" in sec_lower or "treasury" in sec_lower or "debt" in sec_lower or "sovereign" in sec_lower or "bond" in sec_lower:
        return "Debt"
    else:
        return "Equity"


def load_holdings_data() -> pd.DataFrame:
    """Load holdings data from SQLite."""
    conn = get_db_connection()
    query = """
    SELECT
        h.holding_id,
        h.amfi_code,
        h.stock_symbol,
        h.stock_name,
        h.sector,
        h.weight_pct,
        h.market_value_cr,
        h.current_price_inr,
        h.portfolio_date,
        f.scheme_name,
        f.fund_house,
        f.category,
        f.plan
    FROM stg_portfolio_holdings h
    JOIN dim_fund f ON h.amfi_code = f.amfi_code
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df["weight_pct"] = pd.to_numeric(df["weight_pct"], errors="coerce").fillna(0.0)
        df["market_value_cr"] = pd.to_numeric(df["market_value_cr"], errors="coerce").fillna(0.0)
        df["current_price_inr"] = pd.to_numeric(df["current_price_inr"], errors="coerce").fillna(0.0)
        
        df["market_cap"] = df["stock_name"].apply(get_market_cap_category)
        df["asset_class"] = df.apply(lambda row: get_asset_class(row["sector"], row["stock_name"]), axis=1)
        
    return df


def get_filter_options(df: pd.DataFrame) -> dict:
    """Extract filter dropdown items."""
    if df.empty:
        return {
            "fund_houses": [],
            "schemes": [],
            "categories": [],
            "market_caps": []
        }
    return {
        "fund_houses": sorted(df["fund_house"].dropna().unique().tolist()),
        "schemes": sorted(df["scheme_name"].dropna().unique().tolist()),
        "categories": sorted(df["category"].dropna().unique().tolist()),
        "market_caps": sorted(df["market_cap"].dropna().unique().tolist())
    }


def filter_holdings_data(
    df: pd.DataFrame,
    fund_houses: list[str] = None,
    schemes: list[str] = None,
    categories: list[str] = None,
    market_caps: list[str] = None
) -> pd.DataFrame:
    """Filter holdings dataframe."""
    filtered = df.copy()
    if fund_houses:
        filtered = filtered[filtered["fund_house"].isin(fund_houses)]
    if schemes:
        filtered = filtered[filtered["scheme_name"].isin(schemes)]
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]
    if market_caps:
        filtered = filtered[filtered["market_cap"].isin(market_caps)]
    return filtered


def calculate_holdings_kpis(df: pd.DataFrame) -> dict:
    """Compute holdings KPIs."""
    if df.empty:
        return {
            "total_holdings": 0,
            "largest_holding_weight": 0.0,
            "avg_holding_weight": 0.0,
            "num_sectors": 0
        }
        
    return {
        "total_holdings": int(df["stock_name"].nunique()),
        "largest_holding_weight": float(df["weight_pct"].max()),
        "avg_holding_weight": float(df["weight_pct"].mean()),
        "num_sectors": int(df["sector"].nunique())
    }


def get_top_10_holdings(df: pd.DataFrame) -> pd.DataFrame:
    """Get top 10 holdings by weight."""
    if df.empty:
        return pd.DataFrame(columns=["stock_name", "weight_pct"])
        
    grouped = df.groupby("stock_name")["weight_pct"].sum().reset_index()
    grouped = grouped.sort_values("weight_pct", ascending=False).head(10).reset_index(drop=True)
    return grouped


def get_sector_allocation(df: pd.DataFrame) -> pd.DataFrame:
    """Get sector allocation weights."""
    if df.empty:
        return pd.DataFrame(columns=["sector", "weight_pct"])
        
    grouped = df.groupby("sector")["weight_pct"].sum().reset_index()
    total_w = grouped["weight_pct"].sum()
    if total_w > 0:
        grouped["percentage"] = (grouped["weight_pct"] / total_w) * 100.0
    else:
        grouped["percentage"] = 0.0
    return grouped.sort_values("percentage", ascending=False).reset_index(drop=True)


def get_asset_allocation(df: pd.DataFrame) -> pd.DataFrame:
    """Get asset allocation weights."""
    if df.empty:
        return pd.DataFrame(columns=["asset_class", "weight_pct"])
        
    grouped = df.groupby("asset_class")["weight_pct"].sum().reset_index()
    total_w = grouped["weight_pct"].sum()
    if total_w > 0:
        grouped["percentage"] = (grouped["weight_pct"] / total_w) * 100.0
    else:
        grouped["percentage"] = 0.0
    return grouped


def get_market_cap_allocation(df: pd.DataFrame) -> pd.DataFrame:
    """Get market cap allocation weights."""
    if df.empty:
        return pd.DataFrame(columns=["market_cap", "weight_pct"])
        
    grouped = df.groupby("market_cap")["weight_pct"].sum().reset_index()
    total_w = grouped["weight_pct"].sum()
    if total_w > 0:
        grouped["percentage"] = (grouped["weight_pct"] / total_w) * 100.0
    else:
        grouped["percentage"] = 0.0
    return grouped


def generate_holdings_insights(df: pd.DataFrame) -> dict:
    """Generate portfolio holdings insights."""
    default_vals = {
        "largest_holding_name": "N/A", "largest_holding_val": 0.0,
        "most_common_sector": "N/A", "most_common_sector_val": 0.0,
        "most_diversified_fund": "N/A", "most_diversified_count": 0,
        "highest_sector_concentration_name": "N/A", "highest_sector_concentration_val": 0.0,
        "largest_market_cap": "N/A", "largest_market_cap_val": 0.0
    }
    
    if df.empty:
        return default_vals
        
    insights = default_vals.copy()
    
    # 1. Largest Portfolio Holding
    grouped_holdings = df.groupby("stock_name")["weight_pct"].sum().reset_index()
    if not grouped_holdings.empty:
        grouped_holdings = grouped_holdings.sort_values("weight_pct", ascending=False)
        top_h = grouped_holdings.iloc[0]
        insights["largest_holding_name"] = top_h["stock_name"]
        insights["largest_holding_val"] = float(top_h["weight_pct"])
        
    # 2. Most Common Sector
    sector_alloc = get_sector_allocation(df)
    if not sector_alloc.empty:
        top_sec = sector_alloc.iloc[0]
        insights["most_common_sector"] = top_sec["sector"]
        insights["most_common_sector_val"] = float(top_sec["percentage"])
        insights["highest_sector_concentration_name"] = top_sec["sector"]
        insights["highest_sector_concentration_val"] = float(top_sec["percentage"])
        
    # 3. Most Diversified Fund
    if "scheme_name" in df.columns:
        fund_counts = df.groupby("scheme_name")["stock_name"].nunique()
        if not fund_counts.empty:
            top_fund = fund_counts.idxmax()
            insights["most_diversified_fund"] = top_fund
            insights["most_diversified_count"] = int(fund_counts[top_fund])
            
    # 4. Largest Market Cap Allocation
    mcap_alloc = get_market_cap_allocation(df)
    if not mcap_alloc.empty:
        mcap_alloc = mcap_alloc.sort_values("percentage", ascending=False)
        top_mcap = mcap_alloc.iloc[0]
        insights["largest_market_cap"] = top_mcap["market_cap"]
        insights["largest_market_cap_val"] = float(top_mcap["percentage"])
        
    return insights
