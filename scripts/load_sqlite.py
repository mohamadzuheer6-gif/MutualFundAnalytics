import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def parse_date(series, *, fmt=None, dayfirst=False):
    parsed = pd.to_datetime(
        series,
        errors="coerce",
        format=fmt,
        dayfirst=dayfirst
    )
    return parsed.dt.normalize()


def table_count(conn, table_name):
    return conn.execute(
        text(f"SELECT COUNT(*) FROM {table_name}")
    ).scalar_one()


try:
    if DB_PATH.exists():
        os.remove(DB_PATH)
except PermissionError:
    print("Database file locked by another process. Dropping tables dynamically to re-initialize.")
    temp_engine = create_engine(f"sqlite:///{DB_PATH}")
    with temp_engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        for tbl in ["fact_nav", "fact_transactions", "fact_performance", "fact_aum", "dim_fund", "dim_date", "stg_monthly_sip_inflows", "stg_category_inflows", "stg_industry_folio_count", "stg_portfolio_holdings", "stg_benchmark_indices", "etl_metadata"]:
            conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))

engine = create_engine(f"sqlite:///{DB_PATH}")

fund_df = pd.read_csv(PROCESSED_DIR / "01_fund_master_clean.csv")
nav_df = pd.read_csv(PROCESSED_DIR / "02_nav_history_clean.csv")
aum_df = pd.read_csv(PROCESSED_DIR / "03_aum_by_fund_house_clean.csv")
sip_df = pd.read_csv(PROCESSED_DIR / "04_monthly_sip_inflows_clean.csv")
category_df = pd.read_csv(PROCESSED_DIR / "05_category_inflows_clean.csv")
folio_df = pd.read_csv(PROCESSED_DIR / "06_industry_folio_count_clean.csv")
perf_df = pd.read_csv(PROCESSED_DIR / "07_scheme_performance_clean.csv")
txn_df = pd.read_csv(PROCESSED_DIR / "08_investor_transactions_clean.csv")
hold_df = pd.read_csv(PROCESSED_DIR / "09_portfolio_holdings_clean.csv")
bench_df = pd.read_csv(PROCESSED_DIR / "10_benchmark_indices_clean.csv")

fund_df = fund_df.drop_duplicates(subset=["amfi_code"]).copy()
fund_df = fund_df.sort_values("amfi_code").reset_index(drop=True)
fund_df.insert(0, "fund_id", range(1, len(fund_df) + 1))

date_parts = [
    parse_date(nav_df["date"], dayfirst=True),
    parse_date(aum_df["date"], fmt="%Y-%m-%d"),
    parse_date(sip_df["month"], fmt="%Y-%m-%d"),
    parse_date(category_df["month"], fmt="%Y-%m-%d"),
    parse_date(folio_df["month"], fmt="%Y-%m-%d"),
    parse_date(txn_df["transaction_date"], fmt="%Y-%m-%d"),
    parse_date(hold_df["portfolio_date"], fmt="%Y-%m-%d"),
    parse_date(bench_df["date"], fmt="%Y-%m-%d"),
]

all_dates = pd.concat(date_parts, ignore_index=True).dropna()
min_date = all_dates.min()
max_date = all_dates.max()

dim_date = pd.DataFrame(
    {
        "full_date": pd.date_range(min_date, max_date, freq="D")
    }
)
dim_date.insert(0, "date_id", range(1, len(dim_date) + 1))
dim_date["year"] = dim_date["full_date"].dt.year
dim_date["quarter"] = dim_date["full_date"].dt.quarter
dim_date["month"] = dim_date["full_date"].dt.month
dim_date["month_name"] = dim_date["full_date"].dt.month_name()
dim_date["day"] = dim_date["full_date"].dt.day
dim_date["weekday"] = dim_date["full_date"].dt.day_name()

source_counts = {
    "dim_fund": len(fund_df),
    "dim_date": len(dim_date),
    "fact_nav": len(nav_df),
    "fact_transactions": len(txn_df),
    "fact_performance": len(perf_df),
    "fact_aum": len(aum_df),
    "stg_monthly_sip_inflows": len(sip_df),
    "stg_category_inflows": len(category_df),
    "stg_industry_folio_count": len(folio_df),
    "stg_portfolio_holdings": len(hold_df),
    "stg_benchmark_indices": len(bench_df),
}

with engine.begin() as conn:
    conn.execute(text("PRAGMA foreign_keys = ON"))

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.connection.executescript(f.read())

    print("\nTables created successfully")

    dim_fund = fund_df[
        [
            "fund_id",
            "amfi_code",
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
    ].copy()
    dim_fund.to_sql("dim_fund", conn, if_exists="append", index=False)
    print(f"\ndim_fund loaded : {len(dim_fund)} rows")

    dim_date.to_sql("dim_date", conn, if_exists="append", index=False)
    print(f"dim_date loaded : {len(dim_date)} rows")

    fund_lookup = dim_fund[["fund_id", "amfi_code"]].copy()
    date_lookup = dim_date[["date_id", "full_date"]].copy()

    nav_df["date"] = parse_date(nav_df["date"], dayfirst=True)
    nav_df = nav_df.merge(fund_lookup, on="amfi_code", how="left", validate="many_to_one")
    nav_df = nav_df.merge(
        date_lookup,
        left_on="date",
        right_on="full_date",
        how="left",
        validate="many_to_one"
    )
    if nav_df["fund_id"].isna().any() or nav_df["date_id"].isna().any():
        raise ValueError("fact_nav has unmatched fund or date values")

    fact_nav = nav_df[["fund_id", "date_id", "nav"]].copy()
    fact_nav.to_sql("fact_nav", conn, if_exists="append", index=False)
    print(f"fact_nav loaded : {len(fact_nav)} rows")

    txn_df["transaction_date"] = parse_date(
        txn_df["transaction_date"],
        fmt="%Y-%m-%d"
    )
    txn_df = txn_df.merge(fund_lookup, on="amfi_code", how="left", validate="many_to_one")
    txn_df = txn_df.merge(
        date_lookup,
        left_on="transaction_date",
        right_on="full_date",
        how="left",
        validate="many_to_one"
    )
    if txn_df["fund_id"].isna().any() or txn_df["date_id"].isna().any():
        raise ValueError("fact_transactions has unmatched fund or date values")

    fact_transactions = txn_df[
        [
            "fund_id",
            "date_id",
            "investor_id",
            "transaction_type",
            "amount_inr",
            "state",
            "city",
            "city_tier",
            "age_group",
            "gender",
            "annual_income_lakh",
            "payment_mode",
            "kyc_status"
        ]
    ].copy()
    fact_transactions.to_sql(
        "fact_transactions",
        conn,
        if_exists="append",
        index=False
    )
    print(f"fact_transactions loaded : {len(fact_transactions)} rows")

    perf_df = perf_df.merge(
        fund_lookup,
        on="amfi_code",
        how="left",
        validate="many_to_one"
    )
    if perf_df["fund_id"].isna().any():
        raise ValueError("fact_performance has unmatched fund values")

    fact_performance = perf_df[
        [
            "fund_id",
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
            "expense_ratio_pct",
            "morningstar_rating"
        ]
    ].copy()
    fact_performance.to_sql(
        "fact_performance",
        conn,
        if_exists="append",
        index=False
    )
    print(f"fact_performance loaded : {len(fact_performance)} rows")

    aum_df["date"] = parse_date(aum_df["date"], fmt="%Y-%m-%d")
    aum_df = aum_df.merge(
        date_lookup,
        left_on="date",
        right_on="full_date",
        how="left",
        validate="many_to_one"
    )
    if aum_df["date_id"].isna().any():
        raise ValueError("fact_aum has unmatched date values")

    fact_aum = aum_df[
        [
            "date_id",
            "fund_house",
            "aum_lakh_crore",
            "aum_crore",
            "num_schemes"
        ]
    ].copy()
    fact_aum.to_sql("fact_aum", conn, if_exists="append", index=False)
    print(f"fact_aum loaded : {len(fact_aum)} rows")

    sip_df["month"] = parse_date(sip_df["month"], fmt="%Y-%m-%d")
    sip_df.to_sql("stg_monthly_sip_inflows", conn, if_exists="append", index=False)
    print(f"stg_monthly_sip_inflows loaded : {len(sip_df)} rows")

    category_df["month"] = parse_date(category_df["month"], fmt="%Y-%m-%d")
    category_df.to_sql("stg_category_inflows", conn, if_exists="append", index=False)
    print(f"stg_category_inflows loaded : {len(category_df)} rows")

    folio_df["month"] = parse_date(folio_df["month"], fmt="%Y-%m-%d")
    folio_df.to_sql("stg_industry_folio_count", conn, if_exists="append", index=False)
    print(f"stg_industry_folio_count loaded : {len(folio_df)} rows")

    hold_df["portfolio_date"] = parse_date(
        hold_df["portfolio_date"],
        fmt="%Y-%m-%d"
    )
    hold_df.to_sql("stg_portfolio_holdings", conn, if_exists="append", index=False)
    print(f"stg_portfolio_holdings loaded : {len(hold_df)} rows")

    bench_df["date"] = parse_date(bench_df["date"], fmt="%Y-%m-%d")
    bench_df.to_sql("stg_benchmark_indices", conn, if_exists="append", index=False)
    print(f"stg_benchmark_indices loaded : {len(bench_df)} rows")

    print("\nCurrent table counts:\n")
    for table_name, expected in source_counts.items():
        count = table_count(conn, table_name)
        print(f"{table_name:<20} {count}")
        if count != expected:
            raise ValueError(
                f"{table_name} row count mismatch: "
                f"expected {expected}, got {count}"
            )

print("\nDatabase loading completed.")
