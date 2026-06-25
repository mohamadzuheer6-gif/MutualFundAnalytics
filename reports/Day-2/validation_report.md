# Validation Report

## Summary

The cleaned CSV files loaded into SQLite without row loss. The fact-table join issue was fixed by normalizing dates consistently and using a complete calendar dimension.

Final warehouse checks confirmed that all valid source rows were preserved in the fact tables.

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
| 04_monthly_sip_inflows_clean.csv | 12 expected nulls in `yoy_growth_pct` |
| All other cleaned datasets | 0 nulls in key fields |

The `yoy_growth_pct` gaps are expected for January 2022 to December 2022 because those months do not have a prior-year base in the dataset. These values were not filled with zero because zero would incorrectly mean no growth.

## Date Validation

| Check | Result |
|---|---|
| NAV date parsing | Passed with `dayfirst=True` |
| Transaction date parsing | Passed with ISO parsing |
| AUM / benchmark / monthly date parsing | Passed |
| Null dates in cleaned key date columns | 0 |
| SQLite `dim_date` span | `2022-01-01` to `2026-05-29` |


## Database Validation

The following checks were performed after loading data into SQLite:

- Verified all AMFI codes in fact tables exist in `dim_fund`.
- Verified all dates in fact tables exist in `dim_date`.
- Verified no NULL foreign keys in `fact_nav`, `fact_transactions`, `fact_performance`, or `fact_aum`.
- Verified row counts in SQLite match the cleaned CSV source files.


## Database Row Counts

| Table | Rows loaded |
|---|---:|
| `dim_fund` | 40 |
| `dim_date` | 1,610 |
| `fact_nav` | 46,000 |
| `fact_transactions` | 32,778 |
| `fact_performance` | 40 |
| `fact_aum` | 90 |
| `stg_monthly_sip_inflows` | 48 |
| `stg_category_inflows` | 144 |
| `stg_industry_folio_count` | 21 |
| `stg_portfolio_holdings` | 322 |
| `stg_benchmark_indices` | 8,050 |


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
