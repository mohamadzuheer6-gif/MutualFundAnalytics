"""Script to compute mutual fund performance metrics from raw NAV data in SQLite."""
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

# Resolve project base directory
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"

def compute_metrics():
    print("=" * 60)
    print("MUTUAL FUND METRICS COMPUTATION ENGINE")
    print("=" * 60)

    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    # Connect to the database
    conn = sqlite3.connect(str(DB_PATH))
    
    # Read NAV data
    print("\nReading fact_nav and dim_fund data...")
    query = """
        SELECT f.scheme_name, f.amfi_code, d.full_date, fn.nav
        FROM fact_nav fn
        JOIN dim_fund f ON fn.fund_id = f.fund_id
        JOIN dim_date d ON fn.date_id = d.date_id
        ORDER BY f.amfi_code, d.full_date
    """
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        print("No NAV data found in database.")
        return

    df['full_date'] = pd.to_datetime(df['full_date'])
    
    # Compute metrics for each fund
    funds = df['scheme_name'].unique()
    print(f"Computing risk and return metrics for {len(funds)} funds...\n")

    results = []
    for fund in funds:
        fund_df = df[df['scheme_name'] == fund].copy().sort_values('full_date')
        if len(fund_df) < 2:
            continue
            
        # Calculate daily returns
        fund_df['daily_return'] = fund_df['nav'].pct_change()
        
        # Calculate performance statistics
        total_days = (fund_df['full_date'].max() - fund_df['full_date'].min()).days
        years = total_days / 365.25 if total_days > 0 else 1.0
        
        start_nav = fund_df['nav'].iloc[0]
        end_nav = fund_df['nav'].iloc[-1]
        cagr = ((end_nav / start_nav) ** (1.0 / years) - 1.0) * 100.0 if start_nav > 0 and years > 0 else 0.0
        
        # Risk indicators
        volatility = fund_df['daily_return'].std() * np.sqrt(252) * 100.0 if len(fund_df) > 10 else 0.0
        
        # Sharpe Ratio (6% risk free rate)
        rf_rate = 6.0
        sharpe = (cagr - rf_rate) / volatility if volatility > 0 else 0.0
        
        # Max Drawdown
        fund_df['cum_max'] = fund_df['nav'].cummax()
        fund_df['drawdown'] = (fund_df['nav'] - fund_df['cum_max']) / fund_df['cum_max'] * 100.0
        max_dd = fund_df['drawdown'].min()
        
        results.append({
            "Scheme Name": fund,
            "AMFI Code": fund_df['amfi_code'].iloc[0],
            "CAGR (%)": f"{cagr:.2f}%",
            "Ann. Volatility (%)": f"{volatility:.2f}%",
            "Sharpe Ratio (Rf=6%)": f"{sharpe:.2f}",
            "Max Drawdown (%)": f"{max_dd:.2f}%"
        })
        
    metrics_df = pd.DataFrame(results)
    print(metrics_df.to_string(index=False))
    print("\nComputation complete!")

if __name__ == "__main__":
    compute_metrics()
