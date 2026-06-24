import pandas as pd
import numpy as np
from pathlib import Path



RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("MUTUAL FUND DATA CLEANING STARTED")
print("=" * 60)

# Helper Function

summary = []

def save_clean(df, filename, original_rows):
    output_path = PROCESSED_DIR / filename
    df.to_csv(output_path, index=False)

    summary.append({
        "file": filename,
        "before": original_rows,
        "after": len(df)
    })


# 01 FUND MASTER


df = pd.read_csv(RAW_DIR / "01_fund_master.csv")
original_rows = len(df)

df = df.drop_duplicates()

df["launch_date"] = pd.to_datetime(
    df["launch_date"],
    errors="coerce"
)

text_cols = [
    "fund_house",
    "scheme_name",
    "category",
    "sub_category",
    "plan",
    "benchmark",
    "fund_manager",
    "risk_category",
    "sebi_category_code"
]

for col in text_cols:
    df[col] = (
        df[col]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

df = df[df["expense_ratio_pct"].between(0, 5)]
df = df[df["exit_load_pct"].between(0, 5)]
df = df[df["min_sip_amount"] > 0]
df = df[df["min_lumpsum_amount"] > 0]

save_clean(df, "01_fund_master_clean.csv", original_rows)

valid_amfi_codes = set(df["amfi_code"])


# 02 NAV HISTORY


df = pd.read_csv(RAW_DIR / "02_nav_history.csv")
original_rows = len(df)

df["date"] = pd.to_datetime(df["date"], errors="coerce")

df = df.sort_values(
    ["amfi_code", "date"]
)

df = df.drop_duplicates(
    subset=["amfi_code", "date"]
)

df["nav"] = (
    df.groupby("amfi_code")["nav"]
    .ffill()
)

df = df[df["nav"] > 0]

df = df[df["amfi_code"].isin(valid_amfi_codes)]

save_clean(df, "02_nav_history_clean.csv", original_rows)


# 03 AUM BY FUND HOUSE


df = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv")
original_rows = len(df)

df["date"] = pd.to_datetime(df["date"])

df["fund_house"] = (
    df["fund_house"]
    .astype(str)
    .str.strip()
)

df = df.drop_duplicates(
    subset=["date", "fund_house"]
)

df = df[df["aum_lakh_crore"] > 0]
df = df[df["aum_crore"] > 0]
df = df[df["num_schemes"] > 0]

save_clean(df, "03_aum_by_fund_house_clean.csv", original_rows)


# 04 MONTHLY SIP INFLOWS


df = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv")
original_rows = len(df)

df["month"] = pd.to_datetime(
    df["month"],
    format="%Y-%m",
    errors="coerce"
)

numeric_cols = [
    "sip_inflow_crore",
    "active_sip_accounts_crore",
    "new_sip_accounts_lakh",
    "sip_aum_lakh_crore"
]

for col in numeric_cols:
    df = df[df[col] >= 0]

df["yoy_anomaly"] = (
    df["yoy_growth_pct"].abs() > 200
)

save_clean(df, "04_monthly_sip_inflows_clean.csv", original_rows)


# 05 CATEGORY INFLOWS


df = pd.read_csv(RAW_DIR / "05_category_inflows.csv")
original_rows = len(df)

df["month"] = pd.to_datetime(
    df["month"],
    format="%Y-%m",
    errors="coerce"
)

df["category"] = (
    df["category"]
    .astype(str)
    .str.strip()
)

df = df.drop_duplicates(
    subset=["month", "category"]
)

save_clean(df, "05_category_inflows_clean.csv", original_rows)


# 06 INDUSTRY FOLIO COUNT


df = pd.read_csv(RAW_DIR / "06_industry_folio_count.csv")
original_rows = len(df)

df["month"] = pd.to_datetime(
    df["month"],
    format="%Y-%m",
    errors="coerce"
)

folio_cols = [
    "total_folios_crore",
    "equity_folios_crore",
    "debt_folios_crore",
    "hybrid_folios_crore",
    "others_folios_crore"
]

for col in folio_cols:
    df = df[df[col] >= 0]

df["folio_difference"] = (
    df["total_folios_crore"]
    -
    (
        df["equity_folios_crore"]
        + df["debt_folios_crore"]
        + df["hybrid_folios_crore"]
        + df["others_folios_crore"]
    )
)

save_clean(df, "06_industry_folio_count_clean.csv", original_rows)

# 07 SCHEME PERFORMANCE


df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
original_rows = len(df)

numeric_cols = [
    "return_1yr_pct",
    "return_3yr_pct",
    "return_5yr_pct",
    "benchmark_3yr_pct",
    "alpha",
    "beta",
    "sharpe_ratio",
    "sortino_ratio",
    "std_dev_ann_pct",
    "max_drawdown_pct",
    "aum_crore",
    "expense_ratio_pct"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df["return_anomaly"] = (
    (df["return_1yr_pct"].abs() > 100)
    |
    (df["return_3yr_pct"].abs() > 100)
    |
    (df["return_5yr_pct"].abs() > 100)
)

df["expense_ratio_flag"] = (
    ~df["expense_ratio_pct"].between(0.1, 2.5)
)

df = df[df["amfi_code"].isin(valid_amfi_codes)]

save_clean(df, "07_scheme_performance_clean.csv", original_rows)


# 08 INVESTOR TRANSACTIONS


df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
original_rows = len(df)

df["transaction_date"] = pd.to_datetime(
    df["transaction_date"],
    errors="coerce"
)

df["transaction_type"] = (
    df["transaction_type"]
    .astype(str)
    .str.strip()
    .str.title()
)

valid_types = [
    "Sip",
    "Lumpsum",
    "Redemption"
]

df = df[
    df["transaction_type"].isin(valid_types)
]

df = df[df["amount_inr"] > 0]

df["kyc_status"] = (
    df["kyc_status"]
    .astype(str)
    .str.title()
)

valid_kyc = [
    "Verified",
    "Pending",
    "Rejected"
]

df = df[
    df["kyc_status"].isin(valid_kyc)
]

df = df[df["amfi_code"].isin(valid_amfi_codes)]

save_clean(
    df,
    "08_investor_transactions_clean.csv",
    original_rows
)


# 09 PORTFOLIO HOLDINGS


df = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv")
original_rows = len(df)

df["portfolio_date"] = pd.to_datetime(
    df["portfolio_date"],
    errors="coerce"
)

text_cols = [
    "stock_symbol",
    "stock_name",
    "sector"
]

for col in text_cols:
    df[col] = (
        df[col]
        .astype(str)
        .str.strip()
    )

df = df[
    df["weight_pct"].between(0, 100)
]

df = df[df["market_value_cr"] > 0]
df = df[df["current_price_inr"] > 0]

df = df[df["amfi_code"].isin(valid_amfi_codes)]

save_clean(
    df,
    "09_portfolio_holdings_clean.csv",
    original_rows
)


# 10 BENCHMARK INDICES


df = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv")
original_rows = len(df)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df = df.sort_values(
    ["index_name", "date"]
)

df = df.drop_duplicates(
    subset=["date", "index_name"]
)

df["close_value"] = (
    df.groupby("index_name")["close_value"]
    .ffill()
)

df = df[df["close_value"] > 0]

save_clean(
    df,
    "10_benchmark_indices_clean.csv",
    original_rows
)


# SUMMARY


print("\n")
print("=" * 60)
print("DATA CLEANING SUMMARY")
print("=" * 60)

for row in summary:
    print(
        f"{row['file']:<40}"
        f"{row['before']:>8} -> "
        f"{row['after']:>8}"
    )

print("\nAll cleaned files saved in:")
print(PROCESSED_DIR)

print("\nDATA CLEANING COMPLETED")