# Mutual Fund Analytics Platform - Data Dictionary

This document describes all cleaned datasets used in the Mutual Fund Analytics Platform project. It includes column definitions, data types, business meaning, and source references for each dataset stored in `data/processed/`.

## 01_fund_master_clean.csv

| Column | Type | Business definition | Source |
|---|---|---|---|
| amfi_code | INTEGER | Unique AMFI scheme identifier | `data/raw/01_fund_master.csv` |
| fund_house | TEXT | AMC or fund house name | `data/raw/01_fund_master.csv` |
| scheme_name | TEXT | Full mutual fund scheme name | `data/raw/01_fund_master.csv` |
| category | TEXT | Broad scheme category | `data/raw/01_fund_master.csv` |
| sub_category | TEXT | More specific scheme bucket | `data/raw/01_fund_master.csv` |
| plan | TEXT | Regular or Direct plan label | `data/raw/01_fund_master.csv` |
| launch_date | DATE | Scheme launch date | `data/raw/01_fund_master.csv` |
| benchmark | TEXT | Benchmark index used for comparison | `data/raw/01_fund_master.csv` |
| expense_ratio_pct | REAL | Annual expense ratio in percent | `data/raw/01_fund_master.csv` |
| exit_load_pct | REAL | Exit load in percent | `data/raw/01_fund_master.csv` |
| min_sip_amount | REAL | Minimum SIP investment amount | `data/raw/01_fund_master.csv` |
| min_lumpsum_amount | REAL | Minimum lump sum investment amount | `data/raw/01_fund_master.csv` |
| fund_manager | TEXT | Fund manager name | `data/raw/01_fund_master.csv` |
| risk_category | TEXT | Risk label assigned to scheme | `data/raw/01_fund_master.csv` |
| sebi_category_code | TEXT | SEBI scheme category code | `data/raw/01_fund_master.csv` |

## 02_nav_history_clean.csv

| Column | Type | Business definition | Source |
|---|---|---|---|
| amfi_code | INTEGER | Scheme identifier for the NAV series | `data/raw/02_nav_history.csv` |
| date | DATE | NAV observation date | `data/raw/02_nav_history.csv` |
| nav | REAL | Daily net asset value | `data/raw/02_nav_history.csv` |

## 03_aum_by_fund_house_clean.csv

| Column | Type | Business definition | Source |
|---|---|---|---|
| date | DATE | Reporting date for the AUM snapshot | `data/raw/03_aum_by_fund_house.csv` |
| fund_house | TEXT | Fund house name | `data/raw/03_aum_by_fund_house.csv` |
| aum_lakh_crore | REAL | AUM in lakh crore | `data/raw/03_aum_by_fund_house.csv` |
| aum_crore | REAL | Total fund house AUM in crore across schemes | `data/raw/03_aum_by_fund_house.csv` |
| num_schemes | INTEGER | Number of schemes managed by the fund house | `data/raw/03_aum_by_fund_house.csv` |

## 04_monthly_sip_inflows_clean.csv

| Column | Type | Business definition | Source |
|---|---|---|---|
| month | DATE | Month bucket for SIP metrics | `data/raw/04_monthly_sip_inflows.csv` |
| sip_inflow_crore | REAL | Monthly SIP inflow amount in crore | `data/raw/04_monthly_sip_inflows.csv` |
| active_sip_accounts_crore | REAL | Active SIP accounts in crore | `data/raw/04_monthly_sip_inflows.csv` |
| new_sip_accounts_lakh | REAL | New SIP accounts opened in lakh | `data/raw/04_monthly_sip_inflows.csv` |
| sip_aum_lakh_crore | REAL | SIP AUM in lakh crore | `data/raw/04_monthly_sip_inflows.csv` |
| yoy_growth_pct | REAL | Year-over-year SIP inflow growth percent; first-year months are blank because no prior-year comparison exists | `data/raw/04_monthly_sip_inflows.csv` |
| yoy_anomaly | BOOLEAN | Flag for unusually high or low YoY growth | `data/raw/04_monthly_sip_inflows.csv` |

## 05_category_inflows_clean.csv

| Column | Type | Business definition | Source |
|---|---|---|---|
| month | DATE | Month bucket for category inflows | `data/raw/05_category_inflows.csv` |
| category | TEXT | Mutual fund category | `data/raw/05_category_inflows.csv` |
| net_inflow_crore | REAL | Net inflow for the category in crore | `data/raw/05_category_inflows.csv` |

## 06_industry_folio_count_clean.csv

| Column | Type | Business definition | Source |
|---|---|---|---|
| month | DATE | Month bucket for folio counts | `data/raw/06_industry_folio_count.csv` |
| total_folios_crore | REAL | Total industry folios in crore | `data/raw/06_industry_folio_count.csv` |
| equity_folios_crore | REAL | Equity folios in crore | `data/raw/06_industry_folio_count.csv` |
| debt_folios_crore | REAL | Debt folios in crore | `data/raw/06_industry_folio_count.csv` |
| hybrid_folios_crore | REAL | Hybrid folios in crore | `data/raw/06_industry_folio_count.csv` |
| others_folios_crore | REAL | Other folios in crore | `data/raw/06_industry_folio_count.csv` |
| folio_difference | REAL | Difference between total folios and component sum | `data/raw/06_industry_folio_count.csv` |

## 07_scheme_performance_clean.csv

| Column | Type | Business definition | Source |
|---|---|---|---|
| amfi_code | INTEGER | Scheme identifier | `data/raw/07_scheme_performance.csv` |
| scheme_name | TEXT | Scheme name | `data/raw/07_scheme_performance.csv` |
| fund_house | TEXT | AMC name | `data/raw/07_scheme_performance.csv` |
| category | TEXT | Scheme category | `data/raw/07_scheme_performance.csv` |
| plan | TEXT | Regular or Direct plan | `data/raw/07_scheme_performance.csv` |
| return_1yr_pct | REAL | One-year return in percent | `data/raw/07_scheme_performance.csv` |
| return_3yr_pct | REAL | Three-year return in percent | `data/raw/07_scheme_performance.csv` |
| return_5yr_pct | REAL | Five-year return in percent | `data/raw/07_scheme_performance.csv` |
| benchmark_3yr_pct | REAL | Benchmark three-year return in percent | `data/raw/07_scheme_performance.csv` |
| alpha | REAL | Alpha versus benchmark | `data/raw/07_scheme_performance.csv` |
| beta | REAL | Beta versus benchmark | `data/raw/07_scheme_performance.csv` |
| sharpe_ratio | REAL | Sharpe ratio | `data/raw/07_scheme_performance.csv` |
| sortino_ratio | REAL | Sortino ratio | `data/raw/07_scheme_performance.csv` |
| std_dev_ann_pct | REAL | Annualized standard deviation in percent | `data/raw/07_scheme_performance.csv` |
| max_drawdown_pct | REAL | Maximum drawdown in percent | `data/raw/07_scheme_performance.csv` |
| aum_crore | REAL | Individual scheme AUM in crore | `data/raw/07_scheme_performance.csv` |
| expense_ratio_pct | REAL | Expense ratio in percent | `data/raw/07_scheme_performance.csv` |
| morningstar_rating | INTEGER | Morningstar star rating | `data/raw/07_scheme_performance.csv` |
| risk_grade | TEXT | Risk grade band | `data/raw/07_scheme_performance.csv` |
| return_anomaly | BOOLEAN | Flag for extreme return values | `data/raw/07_scheme_performance.csv` |
| expense_ratio_flag | BOOLEAN | Flag for expense ratio outside the expected range | `data/raw/07_scheme_performance.csv` |

## 08_investor_transactions_clean.csv

| Column | Type | Business definition | Source |
|---|---|---|---|
| investor_id | TEXT | Anonymous investor identifier | `data/raw/08_investor_transactions.csv` |
| transaction_date | DATE | Transaction date | `data/raw/08_investor_transactions.csv` |
| amfi_code | INTEGER | Scheme identifier for the transaction | `data/raw/08_investor_transactions.csv` |
| transaction_type | TEXT | SIP, Lumpsum, or Redemption | `data/raw/08_investor_transactions.csv` |
| amount_inr | REAL | Transaction amount in rupees | `data/raw/08_investor_transactions.csv` |
| state | TEXT | Investor state | `data/raw/08_investor_transactions.csv` |
| city | TEXT | Investor city | `data/raw/08_investor_transactions.csv` |
| city_tier | TEXT | City tier bucket | `data/raw/08_investor_transactions.csv` |
| age_group | TEXT | Investor age band | `data/raw/08_investor_transactions.csv` |
| gender | TEXT | Investor gender | `data/raw/08_investor_transactions.csv` |
| annual_income_lakh | REAL | Annual income in lakh | `data/raw/08_investor_transactions.csv` |
| payment_mode | TEXT | Payment channel used for the transaction | `data/raw/08_investor_transactions.csv` |
| kyc_status | TEXT | KYC status value | `data/raw/08_investor_transactions.csv` |

## 09_portfolio_holdings_clean.csv

| Column | Type | Business definition | Source |
|---|---|---|---|
| amfi_code | INTEGER | Scheme identifier for the portfolio snapshot | `data/raw/09_portfolio_holdings.csv` |
| stock_symbol | TEXT | Listed stock ticker | `data/raw/09_portfolio_holdings.csv` |
| stock_name | TEXT | Stock name | `data/raw/09_portfolio_holdings.csv` |
| sector | TEXT | Stock sector | `data/raw/09_portfolio_holdings.csv` |
| weight_pct | REAL | Portfolio weight in percent | `data/raw/09_portfolio_holdings.csv` |
| market_value_cr | REAL | Holding market value in crore | `data/raw/09_portfolio_holdings.csv` |
| current_price_inr | REAL | Current stock price in rupees | `data/raw/09_portfolio_holdings.csv` |
| portfolio_date | DATE | Portfolio snapshot date | `data/raw/09_portfolio_holdings.csv` |

## 10_benchmark_indices_clean.csv

| Column | Type | Business definition | Source |
|---|---|---|---|
| date | DATE | Trading date for the benchmark index | `data/raw/10_benchmark_indices.csv` |
| index_name | TEXT | Benchmark index name | `data/raw/10_benchmark_indices.csv` |
| close_value | REAL | Closing index value | `data/raw/10_benchmark_indices.csv` |


## Dataset Summary

| Dataset | Rows | Columns |
|----------|------:|------:|
| 01_fund_master_clean.csv | 40 | 15 |
| 02_nav_history_clean.csv | 46000 | 3 |
| 03_aum_by_fund_house_clean.csv | 90 | 5 |
| 04_monthly_sip_inflows_clean.csv | 48 | 7 |
| 05_category_inflows_clean.csv | 144 | 3 |
| 06_industry_folio_count_clean.csv | 21 | 7 |
| 07_scheme_performance_clean.csv | 40 | 21 |
| 08_investor_transactions_clean.csv | 32778 | 13 |
| 09_portfolio_holdings_clean.csv | 322 | 8 |
| 10_benchmark_indices_clean.csv | 8050 | 3 |
