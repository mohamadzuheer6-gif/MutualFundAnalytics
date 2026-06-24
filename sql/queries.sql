-- 1. Top 5 funds by AUM
SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f
    ON p.fund_id = f.fund_id
ORDER BY p.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT
    strftime('%Y-%m', d.full_date) AS month,
    ROUND(AVG(n.nav), 4) AS avg_nav
FROM fact_nav n
JOIN dim_date d
    ON n.date_id = d.date_id
GROUP BY strftime('%Y-%m', d.full_date)
ORDER BY month;

-- 3. SIP YoY growth
WITH yearly_sip AS (
    SELECT
        CAST(strftime('%Y', month) AS INTEGER) AS year,
        SUM(sip_inflow_crore) AS sip_inflow_crore
    FROM stg_monthly_sip_inflows
    GROUP BY CAST(strftime('%Y', month) AS INTEGER)
)
SELECT
    year,
    ROUND(sip_inflow_crore, 2) AS sip_inflow_crore,
    ROUND(
        100.0 * (
            sip_inflow_crore - LAG(sip_inflow_crore) OVER (ORDER BY year)
        ) / NULLIF(LAG(sip_inflow_crore) OVER (ORDER BY year), 0),
        2
    ) AS yoy_growth_pct
FROM yearly_sip
ORDER BY year;

-- 4. Transactions by state
SELECT
    state,
    COUNT(*) AS txn_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY txn_count DESC, total_amount_inr DESC;

-- 5. Funds with expense ratio below 1%
SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    p.expense_ratio_pct
FROM fact_performance p
JOIN dim_fund f
    ON p.fund_id = f.fund_id
WHERE p.expense_ratio_pct < 1.0
ORDER BY p.expense_ratio_pct ASC, f.scheme_name;

-- 6. Top 5 funds by 5Y return
SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    p.return_5yr_pct,
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f
    ON p.fund_id = f.fund_id
ORDER BY p.return_5yr_pct DESC
LIMIT 5;

-- 7. AUM by fund house
SELECT
    fund_house,
    ROUND(SUM(aum_crore), 2) AS total_aum_crore,
    ROUND(AVG(num_schemes), 1) AS avg_schemes
FROM fact_aum
GROUP BY fund_house
ORDER BY total_aum_crore DESC;

-- 8. Monthly redemption trends
SELECT
    strftime('%Y-%m', d.full_date) AS month,
    COUNT(*) AS redemption_txn_count,
    ROUND(SUM(t.amount_inr), 2) AS redemption_amount_inr
FROM fact_transactions t
JOIN dim_date d
    ON t.date_id = d.date_id
WHERE t.transaction_type = 'Redemption'
GROUP BY strftime('%Y-%m', d.full_date)
ORDER BY month;

-- 9. Risk grade distribution
SELECT
    risk_category,
    COUNT(*) AS fund_count
FROM dim_fund
GROUP BY risk_category
ORDER BY fund_count DESC, risk_category;

-- 10. Top investing states
SELECT
    state,
    ROUND(AVG(amount_inr), 2) AS avg_ticket_size_inr,
    COUNT(*) AS txn_count
FROM fact_transactions
GROUP BY state
ORDER BY avg_ticket_size_inr DESC, txn_count DESC
LIMIT 10;
