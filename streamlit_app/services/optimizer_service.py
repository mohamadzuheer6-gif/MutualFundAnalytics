"""Portfolio optimization service."""
from __future__ import annotations
import sqlite3
import pandas as pd
import numpy as np

from streamlit_app.config import DB_PATH
from streamlit_app.services.nav_service import load_nav_history, calculate_daily_returns

def load_multiple_funds_returns(fund_ids: list[int]) -> pd.DataFrame:
    """Load and align returns for multiple funds."""
    if not fund_ids:
        return pd.DataFrame()
        
    return_series = {}
    
    for fid in fund_ids:
        df_hist = load_nav_history(fid, filter_standard=True)
        if not df_hist.empty and len(df_hist) >= 5:
            df_ret = calculate_daily_returns(df_hist)
            df_ret["ret_frac"] = df_ret["daily_return_pct"] / 100.0
            series = df_ret.set_index("full_date")["ret_frac"]
            return_series[fid] = series
            
    if not return_series:
        return pd.DataFrame()
        
    aligned_df = pd.DataFrame(return_series).dropna()
    return aligned_df


def optimize_portfolio(
    fund_ids: list[int],
    fund_names: list[str],
    num_portfolios: int = 2000,
    rf_rate: float = 5.0,
    seed: int | None = 42
) -> dict:
    """Generate random portfolios for Efficient Frontier."""
    returns_df = load_multiple_funds_returns(fund_ids)
    if returns_df.empty or len(returns_df) < 5:
        return {}
        
    num_funds = len(fund_ids)
    if num_funds < 2:
        return {}
        
    rf_frac = rf_rate / 100.0
    trading_days = 252
    
    avg_daily_returns = returns_df.mean()
    expected_ann_returns = avg_daily_returns * trading_days
    
    cov_daily = returns_df.cov()
    cov_ann = cov_daily * trading_days
    
    if seed is not None:
        np.random.seed(seed)
        
    results = np.zeros((3, num_portfolios))
    weights_record = []
    
    for i in range(num_portfolios):
        w = np.random.random(num_funds)
        w /= np.sum(w)
        
        p_return = np.sum(w * expected_ann_returns)
        p_vol = np.sqrt(np.dot(w.T, np.dot(cov_ann, w)))
        p_sharpe = (p_return - rf_frac) / p_vol if p_vol > 0 else 0.0
        
        results[0, i] = p_vol
        results[1, i] = p_return
        results[2, i] = p_sharpe
        weights_record.append(w)
        
    max_sharpe_idx = np.argmax(results[2, :])
    min_vol_idx = np.argmin(results[0, :])
    
    max_sharpe_weights = weights_record[max_sharpe_idx]
    min_vol_weights = weights_record[min_vol_idx]
    
    max_sharpe_alloc = {fund_names[i]: float(max_sharpe_weights[i] * 100.0) for i in range(num_funds)}
    min_vol_alloc = {fund_names[i]: float(min_vol_weights[i] * 100.0) for i in range(num_funds)}
    
    funds_expected_returns = {fund_names[i]: float(expected_ann_returns.iloc[i] * 100.0) for i in range(num_funds)}
    
    return {
        "portfolio_vol": results[0, :],
        "portfolio_ret": results[1, :],
        "portfolio_sharpe": results[2, :],
        "weights": weights_record,
        
        "max_sharpe_return": float(results[1, max_sharpe_idx] * 100.0),
        "max_sharpe_vol": float(results[0, max_sharpe_idx] * 100.0),
        "max_sharpe_val": float(results[2, max_sharpe_idx]),
        "max_sharpe_alloc": max_sharpe_alloc,
        
        "min_vol_return": float(results[1, min_vol_idx] * 100.0),
        "min_vol_vol": float(results[0, min_vol_idx] * 100.0),
        "min_vol_val": float(results[2, min_vol_idx]),
        "min_vol_alloc": min_vol_alloc,
        
        "funds_expected_returns": funds_expected_returns,
        "fund_ids": fund_ids,
        "fund_names": fund_names,
        "ann_cov_matrix": cov_ann
    }


def calculate_custom_portfolio(
    weights_pct: list[float],
    expected_returns_pct: list[float],
    cov_ann: pd.DataFrame,
    rf_rate: float = 5.0
) -> dict:
    """Calculate returns/risk for a custom portfolio allocation."""
    w = np.array(weights_pct) / 100.0
    R = np.array(expected_returns_pct) / 100.0
    rf_frac = rf_rate / 100.0
    
    p_return = np.sum(w * R)
    p_vol = np.sqrt(np.dot(w.T, np.dot(cov_ann, w)))
    p_sharpe = (p_return - rf_frac) / p_vol if p_vol > 0 else 0.0
    
    return {
        "return_pct": float(p_return * 100.0),
        "vol_pct": float(p_vol * 100.0),
        "sharpe": float(p_sharpe)
    }
