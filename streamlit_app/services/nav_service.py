"""Business logic for NAV Analytics."""
from __future__ import annotations
import sqlite3
import numpy as np
import pandas as pd
from streamlit_app.config import DB_PATH

def clean_nav_data(df: pd.DataFrame, filter_standard: bool = True) -> pd.DataFrame:
    """Clean NAV history by reindexing to continuous dates and forward filling."""
    if df.empty or len(df) < 2:
        return df

    data = df.copy().sort_values("full_date").reset_index(drop=True)

    min_date = data["full_date"].min()
    max_date = data["full_date"].max()
    all_dates = pd.date_range(start=min_date, end=max_date, freq="D")
    
    data = data.set_index("full_date").reindex(all_dates)
    data.index.name = "full_date"
    data = data.reset_index()
    
    data["nav"] = data["nav"].ffill()
    data = data.dropna(subset=["nav"]).reset_index(drop=True)

    # Filter out single-day outliers (spikes)
    if len(data) >= 3:
        nav = data["nav"]
        nav_prev = nav.shift(1)
        nav_next = nav.shift(-1)
        
        change_in = (nav - nav_prev) / nav_prev
        change_out = (nav_next - nav) / nav
        
        is_spike = (change_in.abs() > 0.15) & (change_out.abs() > 0.15) & (change_in * change_out < 0)
        data = data[~is_spike].reset_index(drop=True)

    # Restrict to Platform Standard Range if requested
    if filter_standard:
        data = data[(data["full_date"] >= "2022-01-03") & (data["full_date"] <= "2026-05-29")].reset_index(drop=True)
        if not data.empty:
            std_min = pd.to_datetime("2022-01-03")
            std_max = pd.to_datetime("2026-05-29")
            std_dates = pd.date_range(start=std_min, end=std_max, freq="D")
            data = data.set_index("full_date").reindex(std_dates)
            data.index.name = "full_date"
            data = data.reset_index()
            data["nav"] = data["nav"].ffill().bfill()

    return data


def load_nav_history(fund_id: int, filter_standard: bool = True) -> pd.DataFrame:
    """Load daily NAV history for a fund from SQLite."""
    conn = sqlite3.connect(str(DB_PATH))
    query = """
    SELECT d.full_date, n.nav
    FROM fact_nav n
    JOIN dim_date d ON n.date_id = d.date_id
    WHERE n.fund_id = ?
    ORDER BY d.full_date
    """
    df = pd.read_sql_query(query, conn, params=(fund_id,))
    conn.close()

    df["full_date"] = pd.to_datetime(df["full_date"])
    df = clean_nav_data(df, filter_standard)
    return df


def calculate_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily return percentage."""
    data = df.copy()
    data["daily_return_pct"] = data["nav"].pct_change() * 100
    return data


def daily_return_statistics(df: pd.DataFrame) -> dict:
    """Get stats for daily returns."""
    if "daily_return_pct" not in df.columns:
        df = calculate_daily_returns(df)
        
    clean_returns = df.dropna(subset=["daily_return_pct"])
    
    if clean_returns.empty:
        return {
            "best_pct": 0.0,
            "best_date": "N/A",
            "worst_pct": 0.0,
            "worst_date": "N/A",
            "avg_pct": 0.0
        }
        
    best_idx = clean_returns["daily_return_pct"].idxmax()
    worst_idx = clean_returns["daily_return_pct"].idxmin()
    
    best_row = clean_returns.loc[best_idx]
    worst_row = clean_returns.loc[worst_idx]
    
    return {
        "best_pct": best_row["daily_return_pct"],
        "best_date": best_row["full_date"].strftime("%d %b %Y"),
        "worst_pct": worst_row["daily_return_pct"],
        "worst_date": worst_row["full_date"].strftime("%d %b %Y"),
        "avg_pct": clean_returns["daily_return_pct"].mean()
    }


def calculate_rolling_returns(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Calculate rolling returns for a window."""
    if df.empty or len(df) < window + 1:
        empty_df = df.copy()
        empty_df["rolling_return_pct"] = pd.Series(dtype="float64")
        return empty_df.iloc[0:0]

    data = df.copy().sort_values("full_date").reset_index(drop=True)
    data["rolling_return_pct"] = data["nav"].pct_change(periods=window) * 100
    data = data.dropna(subset=["rolling_return_pct"]).reset_index(drop=True)
    return data


def get_rolling_return_statistics(rolling_df: pd.DataFrame) -> dict:
    """Get rolling returns stats."""
    if rolling_df.empty or "rolling_return_pct" not in rolling_df.columns:
        return {
            "average": 0.0,
            "max_return": 0.0,
            "max_date": "N/A",
            "min_return": 0.0,
            "min_date": "N/A",
            "current_return": 0.0,
            "current_date": "N/A",
            "volatility": 0.0
        }
        
    returns = rolling_df["rolling_return_pct"]
    max_idx = returns.idxmax()
    min_idx = returns.idxmin()
    
    max_row = rolling_df.loc[max_idx]
    min_row = rolling_df.loc[min_idx]
    
    return {
        "average": float(returns.mean()),
        "max_return": float(returns.max()),
        "max_date": max_row["full_date"].strftime("%d %b %Y"),
        "min_return": float(returns.min()),
        "min_date": min_row["full_date"].strftime("%d %b %Y"),
        "current_return": float(returns.iloc[-1]),
        "current_date": rolling_df["full_date"].iloc[-1].strftime("%d %b %Y"),
        "volatility": float(returns.std()) if len(returns) >= 2 else 0.0
    }


def calculate_drawdown(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate peak NAV, drawdown percentage, and duration."""
    if df.empty:
        return df

    data = df.copy().sort_values("full_date").reset_index(drop=True)
    data["peak_nav"] = data["nav"].cummax()
    data["drawdown_pct"] = (data["nav"] - data["peak_nav"]) / data["peak_nav"] * 100

    durations = []
    current_duration = 0
    for dd in data["drawdown_pct"]:
        if dd >= 0:
            current_duration = 0
        else:
            current_duration += 1
        durations.append(current_duration)
    data["drawdown_duration"] = durations

    return data


def get_drawdown_statistics(drawdown_df: pd.DataFrame) -> dict:
    """Get drawdown statistics."""
    if drawdown_df.empty or "drawdown_pct" not in drawdown_df.columns:
        return {
            "current_drawdown": 0.0,
            "max_drawdown": 0.0,
            "max_dd_date": "N/A",
            "highest_nav": 0.0,
            "highest_nav_date": "N/A",
            "is_recovering": False,
            "days_in_drawdown": 0,
            "recovery_needed_pct": 0.0
        }

    current_dd = drawdown_df["drawdown_pct"].iloc[-1]
    max_dd = drawdown_df["drawdown_pct"].min()

    max_dd_idx = drawdown_df["drawdown_pct"].idxmin()
    max_dd_row = drawdown_df.loc[max_dd_idx]
    max_dd_date = max_dd_row["full_date"].strftime("%d %b %Y")

    highest_nav_idx = drawdown_df["nav"].idxmax()
    highest_nav_row = drawdown_df.loc[highest_nav_idx]
    highest_nav = highest_nav_row["nav"]
    highest_nav_date = highest_nav_row["full_date"].strftime("%d %b %Y")

    days_in_dd = int(drawdown_df["drawdown_duration"].iloc[-1])
    is_recovering = current_dd == 0.0

    last_nav = drawdown_df["nav"].iloc[-1]
    last_peak = drawdown_df["peak_nav"].iloc[-1]
    recovery_needed = 0.0
    if last_nav < last_peak:
        recovery_needed = (last_peak - last_nav) / last_nav * 100

    return {
        "current_drawdown": float(current_dd),
        "max_drawdown": float(max_dd),
        "max_dd_date": max_dd_date,
        "highest_nav": float(highest_nav),
        "highest_nav_date": highest_nav_date,
        "is_recovering": is_recovering,
        "days_in_drawdown": days_in_dd,
        "recovery_needed_pct": float(recovery_needed)
    }


def monthly_nav(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate mean monthly NAV."""
    data = df.copy()
    data["month"] = data["full_date"].dt.to_period("M").astype(str)
    return data.groupby("month")["nav"].mean().reset_index()


def nav_statistics(df: pd.DataFrame) -> dict:
    """Get overall statistics for NAV."""
    if df.empty:
        return {
            "latest": 0.0,
            "highest": 0.0,
            "lowest": 0.0,
            "average": 0.0,
            "median": 0.0,
            "std": 0.0,
            "volatility": 0.0,
            "observations": 0,
            "start_date": "N/A",
            "end_date": "N/A"
        }

    vol = 0.0
    if len(df) >= 2:
        vol_val = df["nav"].pct_change().std()
        if not pd.isna(vol_val):
            vol = vol_val * np.sqrt(252) * 100

    return {
        "latest": df["nav"].iloc[-1],
        "highest": df["nav"].max(),
        "lowest": df["nav"].min(),
        "average": df["nav"].mean(),
        "median": df["nav"].median(),
        "std": df["nav"].std() if len(df) >= 2 else 0.0,
        "volatility": vol,
        "observations": len(df),
        "start_date": df["full_date"].min().strftime("%d %b %Y"),
        "end_date": df["full_date"].max().strftime("%d %b %Y")
    }


def calculate_monthly_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate month-over-month returns."""
    if df.empty or len(df) < 2:
        empty_df = df.copy()
        empty_df["monthly_return_pct"] = pd.Series(dtype="float64")
        empty_df["month_str"] = pd.Series(dtype="str")
        return empty_df.iloc[0:0]
        
    data = df.copy().sort_values("full_date").reset_index(drop=True)
    data["year_month"] = data["full_date"].dt.to_period("M")
    
    monthly_last = data.groupby("year_month").last().reset_index()
    monthly_last["monthly_return_pct"] = monthly_last["nav"].pct_change() * 100
    monthly_last = monthly_last.dropna(subset=["monthly_return_pct"]).reset_index(drop=True)
    monthly_last["month_str"] = monthly_last["year_month"].astype(str)
    
    return monthly_last


def get_monthly_return_statistics(monthly_returns_df: pd.DataFrame) -> dict:
    """Get stats for monthly returns."""
    if monthly_returns_df.empty or "monthly_return_pct" not in monthly_returns_df.columns:
        return {
            "best_month": "N/A",
            "best_pct": 0.0,
            "worst_month": "N/A",
            "worst_pct": 0.0,
            "avg_pct": 0.0,
            "profitable_ratio": "0/0"
        }
        
    rets = monthly_returns_df["monthly_return_pct"]
    
    best_idx = rets.idxmax()
    worst_idx = rets.idxmin()
    
    best_row = monthly_returns_df.loc[best_idx]
    worst_row = monthly_returns_df.loc[worst_idx]
    
    profitable_count = int((rets > 0).sum())
    total_months = len(rets)
    
    return {
        "best_month": best_row["year_month"].strftime("%b %Y"),
        "best_pct": float(best_row["monthly_return_pct"]),
        "worst_month": worst_row["year_month"].strftime("%b %Y"),
        "worst_pct": float(worst_row["monthly_return_pct"]),
        "avg_pct": float(rets.mean()),
        "profitable_ratio": f"{profitable_count}/{total_months}"
    }


def generate_dynamic_insights(df: pd.DataFrame) -> dict:
    """Generate dynamic NAV portfolio insights."""
    if df.empty or len(df) < 2:
        return {
            "highest_nav": 0.0,
            "highest_nav_date": "N/A",
            "lowest_nav": 0.0,
            "lowest_nav_date": "N/A",
            "total_return": 0.0,
            "trend": "N/A",
            "max_drawdown": 0.0,
            "max_dd_date": "N/A",
            "avg_daily_return": 0.0,
            "best_month": "N/A",
            "best_month_pct": 0.0,
            "worst_month": "N/A",
            "worst_month_pct": 0.0,
            "profitable_ratio": "0/0"
        }
        
    stats = nav_statistics(df)
    total_return = (df["nav"].iloc[-1] - df["nav"].iloc[0]) / df["nav"].iloc[0] * 100
    
    r_df = calculate_rolling_returns(df, window=30)
    if not r_df.empty:
        last_roll = r_df["rolling_return_pct"].iloc[-1]
        if last_roll > 5.0:
            trend = "Bullish (Strong short-term growth)"
        elif last_roll > 0.0:
            trend = "Moderately Bullish (Steady upward gains)"
        elif last_roll > -5.0:
            trend = "Moderately Bearish (Consolidating / Sideways)"
        else:
            trend = "Bearish (Downside correction)"
    else:
        trend = "Neutral (Insufficient window history)"
        
    dd_df = calculate_drawdown(df)
    dd_stats = get_drawdown_statistics(dd_df)
    
    ret_df = calculate_daily_returns(df)
    ret_stats = daily_return_statistics(ret_df)
    
    m_ret_df = calculate_monthly_returns(df)
    m_stats = get_monthly_return_statistics(m_ret_df)
    
    max_idx = df["nav"].idxmax()
    min_idx = df["nav"].idxmin()
    max_date = df.loc[max_idx, "full_date"].strftime("%d %b %Y")
    min_date = df.loc[min_idx, "full_date"].strftime("%d %b %Y")
    
    return {
        "highest_nav": stats["highest"],
        "highest_nav_date": max_date,
        "lowest_nav": stats["lowest"],
        "lowest_nav_date": min_date,
        "total_return": total_return,
        "trend": trend,
        "max_drawdown": dd_stats["max_drawdown"],
        "max_dd_date": dd_stats["max_dd_date"],
        "avg_daily_return": ret_stats["avg_pct"],
        "best_month": m_stats["best_month"],
        "best_month_pct": m_stats["best_pct"],
        "worst_month": m_stats["worst_month"],
        "worst_month_pct": m_stats["worst_pct"],
        "profitable_ratio": m_stats["profitable_ratio"]
    }


def prepare_nav_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Sort NAV dataframe by date."""
    return df.copy().sort_values("full_date")