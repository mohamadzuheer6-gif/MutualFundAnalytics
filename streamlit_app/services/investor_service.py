"""Business logic for Investor Analytics."""
from __future__ import annotations
import sqlite3
import pandas as pd
import numpy as np

from streamlit_app.config import DB_PATH
from streamlit_app.database import get_db_connection

def load_investor_data() -> pd.DataFrame:
    """Fetch raw transaction and investor data."""
    conn = get_db_connection()
    query = """
    SELECT
        t.transaction_id,
        t.investor_id,
        t.transaction_type,
        t.amount_inr,
        t.state,
        t.city,
        t.city_tier,
        t.age_group,
        t.gender,
        t.annual_income_lakh,
        t.payment_mode,
        t.kyc_status,
        d.full_date,
        f.scheme_name
    FROM fact_transactions t
    JOIN dim_date d ON t.date_id = d.date_id
    JOIN dim_fund f ON t.fund_id = f.fund_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if "full_date" in df.columns:
        df["full_date"] = pd.to_datetime(df["full_date"])
        
    return df


def get_filter_options(df: pd.DataFrame) -> dict:
    """Extract filter dropdown options."""
    if df.empty:
        return {
            "states": [],
            "age_groups": [],
            "city_tiers": []
        }
    return {
        "states": sorted(df["state"].dropna().unique().tolist()),
        "age_groups": sorted(df["age_group"].dropna().unique().tolist()),
        "city_tiers": sorted(df["city_tier"].dropna().unique().tolist())
    }


def filter_investor_data(
    df: pd.DataFrame,
    states: list[str] = None,
    age_groups: list[str] = None,
    city_tiers: list[str] = None
) -> pd.DataFrame:
    """Filter investor dataframe by selected values."""
    filtered = df.copy()
    if states:
        filtered = filtered[filtered["state"].isin(states)]
    if age_groups:
        filtered = filtered[filtered["age_group"].isin(age_groups)]
    if city_tiers:
        filtered = filtered[filtered["city_tier"].isin(city_tiers)]
    return filtered


def calculate_investor_kpis(df: pd.DataFrame) -> dict:
    """Calculate key investor metrics."""
    if df.empty:
        return {
            "total_investors": 0,
            "total_transactions": 0,
            "avg_sip_amount": 0.0,
            "avg_transaction_amount": 0.0
        }
        
    sip_df = df[df["transaction_type"].str.upper() == "SIP"]
    avg_sip = float(sip_df["amount_inr"].mean()) if not sip_df.empty else 0.0
    avg_tx = float(df["amount_inr"].mean()) if "amount_inr" in df.columns else 0.0
    
    return {
        "total_investors": int(df["investor_id"].nunique()) if "investor_id" in df.columns else 0,
        "total_transactions": len(df),
        "avg_sip_amount": avg_sip,
        "avg_transaction_amount": avg_tx
    }


def aggregate_transaction_by_state(df: pd.DataFrame) -> pd.DataFrame:
    """Group transactions by State (in Crores)."""
    if df.empty:
        return pd.DataFrame(columns=["state", "total_amount_cr"])
        
    grouped = df.groupby("state")["amount_inr"].sum().reset_index()
    grouped["total_amount_cr"] = grouped["amount_inr"] / 10000000.0  # 1 Crore = 10,000,000
    grouped = grouped.sort_values("total_amount_cr", ascending=False).reset_index(drop=True)
    return grouped[["state", "total_amount_cr"]]


def aggregate_investment_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Group transactions by type."""
    if df.empty:
        return pd.DataFrame(columns=["transaction_type", "total_amount_cr"])
        
    grouped = df.groupby("transaction_type")["amount_inr"].sum().reset_index()
    grouped["total_amount_cr"] = grouped["amount_inr"] / 10000000.0
    return grouped


def aggregate_age_group_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Get average SIP amount by age group."""
    if df.empty:
        return pd.DataFrame(columns=["age_group", "avg_sip"])
        
    sip_df = df[df["transaction_type"].str.upper() == "SIP"]
    if sip_df.empty:
        return pd.DataFrame(columns=["age_group", "avg_sip"])
        
    grouped = sip_df.groupby("age_group")["amount_inr"].mean().reset_index(name="avg_sip")
    grouped = grouped.sort_values("age_group").reset_index(drop=True)
    return grouped


def aggregate_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Get transaction count and amount monthly trends."""
    if df.empty:
        return pd.DataFrame(columns=["month_str", "transaction_count", "total_amount_cr"])
        
    df_copy = df.copy()
    df_copy["month_str"] = df_copy["full_date"].dt.strftime("%Y-%m")
    
    grouped = df_copy.groupby("month_str").agg(
        transaction_count=("transaction_id", "count"),
        total_amount=("amount_inr", "sum")
    ).reset_index()
    
    grouped["total_amount_cr"] = grouped["total_amount"] / 10000000.0
    grouped = grouped.sort_values("month_str").reset_index(drop=True)
    return grouped


def generate_investor_insights(df: pd.DataFrame) -> dict:
    """Generate investor analytics insights."""
    default_vals = {
        "highest_investing_state": "N/A", "highest_state_amount_cr": 0.0,
        "most_active_age_group": "N/A", "most_active_age_count": 0,
        "preferred_investment_type": "N/A", "preferred_type_pct": 0.0,
        "highest_avg_sip_age_group": "N/A", "highest_avg_sip_val": 0.0,
        "top_contributing_city_tier": "N/A", "top_city_tier_pct": 0.0,
        "monthly_growth_rate": 0.0
    }
    
    if df.empty:
        return default_vals
        
    insights = default_vals.copy()
    
    # 1. Highest Investing State
    state_df = aggregate_transaction_by_state(df)
    if not state_df.empty:
        top_state = state_df.iloc[0]
        insights["highest_investing_state"] = top_state["state"]
        insights["highest_state_amount_cr"] = float(top_state["total_amount_cr"])
        
    # 2. Most Active Age Group
    if "age_group" in df.columns and not df["age_group"].dropna().empty:
        age_counts = df["age_group"].value_counts()
        insights["most_active_age_group"] = age_counts.index[0]
        insights["most_active_age_count"] = int(age_counts.iloc[0])
        
    # 3. Preferred Investment Type
    type_df = aggregate_investment_type_distribution(df)
    if not type_df.empty:
        type_df = type_df.sort_values("total_amount_cr", ascending=False)
        total_sum = type_df["total_amount_cr"].sum()
        if total_sum > 0:
            top_type = type_df.iloc[0]
            insights["preferred_investment_type"] = top_type["transaction_type"]
            insights["preferred_type_pct"] = float(top_type["total_amount_cr"] / total_sum * 100)
            
    # 4. Highest Average SIP by Age Group
    age_sip_df = aggregate_age_group_analysis(df)
    if not age_sip_df.empty:
        age_sip_df = age_sip_df.sort_values("avg_sip", ascending=False)
        top_age_sip = age_sip_df.iloc[0]
        insights["highest_avg_sip_age_group"] = top_age_sip["age_group"]
        insights["highest_avg_sip_val"] = float(top_age_sip["avg_sip"])
        
    # 5. Top Contributing City Tier
    if "city_tier" in df.columns and not df["city_tier"].dropna().empty:
        city_tier_amounts = df.groupby("city_tier")["amount_inr"].sum()
        total_city_sum = city_tier_amounts.sum()
        if total_city_sum > 0:
            top_city = city_tier_amounts.idxmax()
            insights["top_contributing_city_tier"] = top_city
            insights["top_city_tier_pct"] = float(city_tier_amounts[top_city] / total_city_sum * 100)
            
    # 6. Monthly Growth Rate
    monthly_df = aggregate_monthly_trend(df)
    if len(monthly_df) >= 2:
        last_month = monthly_df.iloc[-1]["total_amount_cr"]
        prev_month = monthly_df.iloc[-2]["total_amount_cr"]
        if prev_month > 0:
            growth = (last_month - prev_month) / prev_month * 100.0
            insights["monthly_growth_rate"] = float(growth)
            
    return insights
