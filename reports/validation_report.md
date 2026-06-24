# Validation Report

## Summary

The cleaned CSV files loaded into SQLite without row loss. The fact-table join issue was fixed by normalizing dates consistently and using a complete calendar dimension.

## AMFI Code Validation

| Dataset | AMFI mismatches vs fund master |
|---|---:|
| 02_nav_history_clean.csv | 0 |
| 07_scheme_performance_clean.csv | 0 |
| 08_investor_transactions_clean.csv | 0 |
| 09_portfolio_holdings_clean.csv | 0 |

All fund-linked datasets match the AMFI codes in `01_fund_master_clean.csv`.

## Duplicate Checks

| Dataset | Duplicate rows on natural key |
|---|---:|
| 01_fund_master_clean.csv | 0 |
| 02_nav_history_clean.csv | 0 |
| 03_aum_by_fund_house_clean.csv | 0 |
| 04_monthly_sip_inflows_clean.csv | 0 |
| 05_category_inflows_clean.csv | 0 |
| 06_industry_folio_count_clean.csv | 0 |
| 07_scheme_performance_clean.csv | 0 |
| 08_investor_transactions_clean.csv | 0 |
| 09_portfolio_holdings_clean.csv | 0 |
| 10_benchmark_indices_clean.csv | 0 |

The cleaned outputs are deduplicated on the keys used in the cleaning step.

## Missing Value Checks

| Dataset | Notable missing values |
|---|---:|
| 04_monthly_sip_inflows_clean.csv | 12 nulls in `yoy_growth_pct` |
| All other cleaned datasets | 0 nulls in key fields |

The `yoy_growth_pct` gaps are expected because the first comparison periods do not have a prior-year base.

## Date Validation

| Check | Result |
|---|---|
| NAV date parsing | Passed with `dayfirst=True` |
| Transaction date parsing | Passed with ISO parsing |
| AUM / benchmark / monthly date parsing | Passed |
| Null dates in cleaned key date columns | 0 |
| SQLite `dim_date` span | `2022-01-01` to `2026-05-29` |

## Referential Integrity Checks

| Check | Result |
|---|---|
| SQLite foreign key violations | 0 |
| `fact_nav` rows loaded | 46,000 |
| `fact_transactions` rows loaded | 32,778 |
| `fact_performance` rows loaded | 40 |
| `fact_aum` rows loaded | 90 |
| Staging tables loaded | 48, 144, 21, 322, 8,050 rows |

Row counts in SQLite match the cleaned source CSVs.

