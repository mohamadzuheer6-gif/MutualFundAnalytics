"""Monte Carlo simulation for NAV projections."""
from __future__ import annotations
import numpy as np
import pandas as pd

from streamlit_app.services.nav_service import load_nav_history, calculate_daily_returns

def simulate_monte_carlo(
    fund_id: int,
    horizon_years: int = 5,
    num_paths: int = 1000,
    seed: int | None = None
) -> dict:
    """Project future NAV paths using GBM."""
    history_df = load_nav_history(fund_id, filter_standard=True)
    if history_df.empty or len(history_df) < 5:
        return {}
        
    df_returns = calculate_daily_returns(history_df)
    clean_returns = df_returns["daily_return_pct"].dropna() / 100.0
    
    if clean_returns.empty:
        return {}
        
    daily_mean = clean_returns.mean()
    daily_var = clean_returns.var()
    daily_std = clean_returns.std()
    
    if daily_std == 0:
        daily_std = 0.0001
        
    start_price = float(history_df["nav"].iloc[-1])
    start_date = pd.to_datetime(history_df["full_date"].iloc[-1])
    
    trading_days_per_year = 252
    steps = horizon_years * trading_days_per_year
    
    if seed is not None:
        np.random.seed(seed)
        
    # GBM calculation
    drift = daily_mean - 0.5 * daily_var
    shocks = np.random.normal(0, 1, size=(steps, num_paths))
    daily_log_returns = drift + daily_std * shocks
    
    cum_log_returns = np.vstack([np.zeros(num_paths), np.cumsum(daily_log_returns, axis=0)])
    sim_prices = start_price * np.exp(cum_log_returns)
    
    future_dates = pd.bdate_range(start=start_date + pd.Timedelta(days=1), periods=steps)
    date_series = [start_date] + list(future_dates)
    
    final_prices = sim_prices[-1, :]
    mean_final = float(np.mean(final_prices))
    median_final = float(np.median(final_prices))
    p5_final = float(np.percentile(final_prices, 5))
    p95_final = float(np.percentile(final_prices, 95))
    
    prob_positive = float(np.sum(final_prices > start_price) / num_paths) * 100.0
    ann_return = float(daily_mean * trading_days_per_year) * 100.0
    ann_volatility = float(daily_std * np.sqrt(trading_days_per_year)) * 100.0
    
    return {
        "prices": sim_prices,
        "dates": date_series,
        "start_price": start_price,
        "mean_final": mean_final,
        "median_final": median_final,
        "p5_final": p5_final,
        "p95_final": p95_final,
        "prob_positive": prob_positive,
        "ann_return": ann_return,
        "ann_volatility": ann_volatility,
        "num_paths": num_paths,
        "horizon_years": horizon_years
    }


def generate_mc_insights(results: dict) -> dict:
    """Generate simple insights from Monte Carlo simulation."""
    if not results:
        return {}
        
    start_val = results["start_price"]
    mean_val = results["mean_final"]
    p5_val = results["p5_final"]
    
    expected_gain_pct = ((mean_val - start_val) / start_val) * 100.0
    downside_risk_pct = ((start_val - p5_val) / start_val) * 100.0
    if downside_risk_pct < 0:
        downside_risk_pct = 0.0
        
    return {
        "expected_growth_pct": expected_gain_pct,
        "downside_risk_pct": downside_risk_pct,
        "prob_of_loss": 100.0 - results["prob_positive"],
        "annual_return_est": results["ann_return"],
        "annual_vol_est": results["ann_volatility"]
    }
