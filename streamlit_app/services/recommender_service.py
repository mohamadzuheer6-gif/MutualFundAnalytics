"""Fund recommendation service."""
from __future__ import annotations
import sqlite3
import pandas as pd
import numpy as np

from streamlit_app.config import DB_PATH
from streamlit_app.database import get_db_connection

def load_recommender_universe() -> pd.DataFrame:
    """Fetch fund characteristics and performance metrics from DB."""
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
        p.benchmark_3yr_pct,
        p.alpha,
        p.beta,
        p.sharpe_ratio,
        p.sortino_ratio,
        p.std_dev_ann_pct AS std_dev,
        p.max_drawdown_pct AS max_drawdown,
        p.aum_crore AS aum,
        p.expense_ratio_pct AS expense_ratio,
        p.morningstar_rating
    FROM dim_fund f
    JOIN fact_performance p ON f.fund_id = p.fund_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_recommendations(
    goal: str,
    risk_appetite: str,
    horizon: str,
    category: str = "All",
    fund_house: str = "All",
    min_rating: str = "All",
    max_expense: float | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate scored fund recommendations based on user profile."""
    df = load_recommender_universe()
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    global_df = df.copy()

    # Handle missing values
    for col in ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "alpha", "sharpe_ratio", "sortino_ratio"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        global_df[col] = pd.to_numeric(global_df[col], errors="coerce").fillna(0.0)

    for col in ["beta", "std_dev"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(1.0)
        global_df[col] = pd.to_numeric(global_df[col], errors="coerce").fillna(1.0)

    df["max_drawdown"] = pd.to_numeric(df["max_drawdown"], errors="coerce").fillna(0.0)
    global_df["max_drawdown"] = pd.to_numeric(global_df["max_drawdown"], errors="coerce").fillna(0.0)
    
    df["expense_ratio"] = pd.to_numeric(df["expense_ratio"], errors="coerce").fillna(1.2)
    global_df["expense_ratio"] = pd.to_numeric(global_df["expense_ratio"], errors="coerce").fillna(1.2)

    df["aum"] = pd.to_numeric(df["aum"], errors="coerce").fillna(100.0)
    global_df["aum"] = pd.to_numeric(global_df["aum"], errors="coerce").fillna(100.0)

    df["morningstar_rating"] = pd.to_numeric(df["morningstar_rating"], errors="coerce").fillna(3)
    global_df["morningstar_rating"] = pd.to_numeric(global_df["morningstar_rating"], errors="coerce").fillna(3)

    # Apply filters
    if category != "All":
        df = df[df["category"].str.lower() == category.lower()]

    if fund_house != "All":
        df = df[df["fund_house"] == fund_house]

    if min_rating != "All":
        try:
            rating_val = int(min_rating)
            df = df[df["morningstar_rating"] >= rating_val]
        except ValueError:
            pass

    if max_expense is not None:
        df = df[df["expense_ratio"] <= max_expense]

    # Goal filtering
    if goal == "Tax Saving":
        df = df[df["sub_category"].str.upper() == "ELSS"]
    elif goal == "Regular Income":
        if category == "All":
            df = df[df["category"].str.lower() == "debt"]

    # Risk mapping
    risk_map = {
        "low": ["low", "moderate"],
        "moderate": ["moderate", "moderately high"],
        "high": ["moderately high", "high", "very high"]
    }
    allowed_risks = risk_map.get(risk_appetite.lower(), ["moderate", "moderately high"])
    df = df[df["risk_category"].str.lower().isin(allowed_risks)]

    # Horizon filtering
    if category == "All":
        if horizon == "Less than 1 Year":
            df = df[df["category"].str.lower() == "debt"]
        elif horizon == "1–3 Years":
            df = df[df["category"].str.lower().isin(["debt", "equity"])]

    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Normalization helper
    def normalize_series(series: pd.Series, global_series: pd.Series, invert: bool = False) -> pd.Series:
        g_min, g_max = global_series.min(), global_series.max()
        if g_max == g_min:
            return pd.Series(1.0, index=series.index)
        norm = (series - g_min) / (g_max - g_min)
        if invert:
            return 1.0 - norm
        return norm

    # Choose return column
    if horizon == "Less than 1 Year":
        ret_col = "return_1yr_pct"
    elif horizon == "1–3 Years":
        ret_col = "return_3yr_pct"
    else:
        ret_col = "return_5yr_pct"

    # Normalize metrics
    norm_return = normalize_series(df[ret_col], global_df[ret_col])
    norm_sharpe = normalize_series(df["sharpe_ratio"], global_df["sharpe_ratio"])
    norm_sortino = normalize_series(df["sortino_ratio"], global_df["sortino_ratio"])
    norm_alpha = normalize_series(df["alpha"], global_df["alpha"])
    norm_std_dev = normalize_series(df["std_dev"], global_df["std_dev"], invert=True)
    norm_expense = normalize_series(df["expense_ratio"], global_df["expense_ratio"], invert=True)
    norm_aum = normalize_series(df["aum"], global_df["aum"])

    # Determine scoring weights
    if goal == "Wealth Creation":
        w = {"return": 0.35, "sharpe": 0.25, "alpha": 0.20, "expense": 0.10, "volatility": 0.05, "aum": 0.05}
    elif goal == "Tax Saving":
        w = {"return": 0.30, "sharpe": 0.25, "alpha": 0.15, "expense": 0.15, "volatility": 0.10, "aum": 0.05}
    elif goal == "Retirement":
        w = {"return": 0.20, "sharpe": 0.30, "sortino": 0.25, "volatility": 0.15, "expense": 0.05, "aum": 0.05}
    elif goal == "Regular Income":
        w = {"return": 0.15, "sharpe": 0.20, "sortino": 0.30, "volatility": 0.20, "expense": 0.10, "aum": 0.05}
    else:
        w = {"return": 0.25, "sharpe": 0.25, "alpha": 0.20, "expense": 0.15, "volatility": 0.10, "aum": 0.05}

    w_ret = w.get("return", 0.0)
    w_shp = w.get("sharpe", 0.0)
    w_srt = w.get("sortino", 0.0)
    w_alp = w.get("alpha", 0.0)
    w_vol = w.get("volatility", 0.0)
    w_exp = w.get("expense", 0.0)
    w_aum = w.get("aum", 0.0)

    # Calculate final score
    score = (
        norm_return * w_ret +
        norm_sharpe * w_shp +
        norm_sortino * w_srt +
        norm_alpha * w_alp +
        norm_std_dev * w_vol +
        norm_expense * w_exp +
        norm_aum * w_aum
    ) * 100.0

    df["recommendation_score"] = score.round(2)
    df_sorted = df.sort_values(by="recommendation_score", ascending=False).reset_index(drop=True)

    # Generate explanations compared to global averages
    avg_sharpe = global_df["sharpe_ratio"].mean()
    avg_expense = global_df["expense_ratio"].mean()
    avg_alpha = global_df["alpha"].mean()
    avg_std = global_df["std_dev"].mean()
    avg_ret_col = global_df[ret_col].mean()

    def generate_explanation(row: pd.Series) -> str:
        reasons = []
        if row["sharpe_ratio"] > avg_sharpe * 1.2:
            reasons.append("Strong risk-adjusted performance with a high Sharpe Ratio.")
        if row["expense_ratio"] < avg_expense * 0.8:
            reasons.append("Highly cost-efficient with a very low expense ratio.")
        if row[ret_col] > avg_ret_col * 1.25:
            reasons.append("Outstanding returns over the relevant investment horizon.")
        if row["alpha"] > avg_alpha * 1.15 and row["alpha"] > 0:
            reasons.append("Consistently beats its benchmark, showing high alpha generation.")
        if row["std_dev"] < avg_std * 0.85:
            reasons.append("Low historical volatility and downside deviation.")
        if row["sub_category"].upper() == "ELSS":
            reasons.append("Offers tax benefits under Section 80C with equity upside.")
        if row["morningstar_rating"] >= 4:
            reasons.append(f"Rated {int(row['morningstar_rating'])} stars by Morningstar for historical performance.")
        if row["aum"] > 10000:
            reasons.append("Large fund size (high AUM) indicating high liquidity and investor trust.")

        if not reasons:
            reasons.append("Favorable combination of returns and risk indicators for your goal.")
            reasons.append("Maintains cost-effective fee structures and solid management.")

        return " ".join(reasons[:2])

    df_sorted["explanation"] = df_sorted.apply(generate_explanation, axis=1)
    top3 = df_sorted.head(3).copy()

    return top3, df_sorted


def get_recommendation_insights(top_df: pd.DataFrame, match_df: pd.DataFrame) -> dict[str, str]:
    """Compute dynamic recommendation insights."""
    insights = {
        "best_overall_name": "N/A", "best_overall_val": "0.00% Match",
        "best_low_risk_name": "N/A", "best_low_risk_val": "N/A",
        "best_high_return_name": "N/A", "best_high_return_val": "0.00%",
        "best_value_name": "N/A", "best_value_val": "0.00% Expense",
        "highest_sharpe_name": "N/A", "highest_sharpe_val": "0.00",
        "lowest_expense_name": "N/A", "lowest_expense_val": "0.00%",
        "best_long_term_name": "N/A", "best_long_term_val": "0.00%"
    }

    if match_df.empty:
        return insights

    best_overall = match_df.iloc[0]
    insights["best_overall_name"] = best_overall["scheme_name"]
    insights["best_overall_val"] = f"{best_overall['recommendation_score']:.2f}% Match"

    low_risk_funds = match_df[match_df["risk_category"].str.lower().isin(["low", "moderate"])]
    if not low_risk_funds.empty:
        best_lr = low_risk_funds.iloc[0]
        insights["best_low_risk_name"] = best_lr["scheme_name"]
        insights["best_low_risk_val"] = f"{best_lr['recommendation_score']:.2f}% Match"
    else:
        best_lr = match_df.sort_values(by="std_dev").iloc[0]
        insights["best_low_risk_name"] = best_lr["scheme_name"]
        insights["best_low_risk_val"] = f"Std Dev: {best_lr['std_dev']:.2f}%"

    best_hr = match_df.sort_values(by="return_3yr_pct", ascending=False).iloc[0]
    insights["best_high_return_name"] = best_hr["scheme_name"]
    insights["best_high_return_val"] = f"{best_hr['return_3yr_pct']:.2f}% (3Y)"

    match_df_copy = match_df.copy()
    match_df_copy["value_metric"] = match_df_copy["recommendation_score"] / match_df_copy["expense_ratio"]
    best_val = match_df_copy.sort_values(by="value_metric", ascending=False).iloc[0]
    insights["best_value_name"] = best_val["scheme_name"]
    insights["best_value_val"] = f"Exp: {best_val['expense_ratio']:.2f}%"

    best_shp = match_df.sort_values(by="sharpe_ratio", ascending=False).iloc[0]
    insights["highest_sharpe_name"] = best_shp["scheme_name"]
    insights["highest_sharpe_val"] = f"{best_shp['sharpe_ratio']:.2f}"

    best_exp = match_df.sort_values(by="expense_ratio", ascending=True).iloc[0]
    insights["lowest_expense_name"] = best_exp["scheme_name"]
    insights["lowest_expense_val"] = f"{best_exp['expense_ratio']:.2f}%"

    best_lt = match_df.sort_values(by="return_5yr_pct", ascending=False).iloc[0]
    insights["best_long_term_name"] = best_lt["scheme_name"]
    insights["best_long_term_val"] = f"{best_lt['return_5yr_pct']:.2f}% (5Y)"

    return insights
