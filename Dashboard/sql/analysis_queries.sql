-- ============================================================================
-- analysis_queries.sql
--
-- The analytical core of the project. Each query answers a specific
-- business question about Indian equity sector performance. These are
-- written for PostgreSQL; minor syntax tweaks may be needed for other
-- engines (e.g. SQL Server uses different date functions).
--
-- Power BI can connect directly to these via "Get Data > Database", or you
-- can paste a query as a custom SQL source / DAX-based measure.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. Rolling 30-day and 90-day returns per stock
--    Business question: "How has each stock performed over the recent past?"
-- ----------------------------------------------------------------------------
SELECT
    symbol,
    trade_date,
    close,
    (close / LAG(close, 30) OVER (PARTITION BY symbol ORDER BY trade_date) - 1) * 100 AS rolling_30d_return_pct,
    (close / LAG(close, 90) OVER (PARTITION BY symbol ORDER BY trade_date) - 1) * 100 AS rolling_90d_return_pct
FROM daily_prices
ORDER BY symbol, trade_date;


-- ----------------------------------------------------------------------------
-- 2. Sector-wise average return and volatility (annualized)
--    Business question: "Which sectors delivered the best risk-adjusted
--    returns over the analysis period?"
-- ----------------------------------------------------------------------------
SELECT
    sm.sector,
    COUNT(*) AS trading_days,
    ROUND(AVG(dp.daily_return_pct)::numeric, 4) AS avg_daily_return_pct,
    ROUND((AVG(dp.daily_return_pct) * 252)::numeric, 2) AS approx_annualized_return_pct,
    ROUND(STDDEV(dp.daily_return_pct)::numeric, 4) AS daily_volatility_pct,
    ROUND((STDDEV(dp.daily_return_pct) * SQRT(252))::numeric, 2) AS annualized_volatility_pct,
    ROUND(
        (AVG(dp.daily_return_pct) * 252) / NULLIF(STDDEV(dp.daily_return_pct) * SQRT(252), 0),
        2
    ) AS return_to_risk_ratio
FROM daily_prices dp
JOIN stock_master sm ON sm.symbol = dp.symbol
WHERE dp.daily_return_pct IS NOT NULL
GROUP BY sm.sector
ORDER BY annualized_return_pct DESC;


-- ----------------------------------------------------------------------------
-- 3. Best and worst performing stock within each sector
--    Business question: "Within each sector, which stock led and which
--    lagged over the full period?"
-- ----------------------------------------------------------------------------
WITH stock_total_return AS (
    SELECT
        sm.sector,
        dp.symbol,
        (
            (SELECT close FROM daily_prices WHERE symbol = dp.symbol ORDER BY trade_date DESC LIMIT 1)
            / NULLIF((SELECT close FROM daily_prices WHERE symbol = dp.symbol ORDER BY trade_date ASC LIMIT 1), 0)
            - 1
        ) * 100 AS total_return_pct
    FROM daily_prices dp
    JOIN stock_master sm ON sm.symbol = dp.symbol
    GROUP BY sm.sector, dp.symbol
),
ranked AS (
    SELECT
        sector,
        symbol,
        total_return_pct,
        RANK() OVER (PARTITION BY sector ORDER BY total_return_pct DESC) AS rank_best,
        RANK() OVER (PARTITION BY sector ORDER BY total_return_pct ASC) AS rank_worst
    FROM stock_total_return
)
SELECT sector, symbol, ROUND(total_return_pct::numeric, 2) AS total_return_pct,
       CASE WHEN rank_best = 1 THEN 'BEST' WHEN rank_worst = 1 THEN 'WORST' END AS flag
FROM ranked
WHERE rank_best = 1 OR rank_worst = 1
ORDER BY sector, flag;


-- ----------------------------------------------------------------------------
-- 4. Sector drawdown analysis during a defined correction window
--    Business question: "How much did each sector fall from peak during a
--    known correction period, and how long did it take to recover?"
--
--    Edit the date range below to match a period you want to study
--    (e.g. the Jan-Mar 2020 COVID crash, or the 2022 rate-hike correction).
-- ----------------------------------------------------------------------------
WITH window_prices AS (
    SELECT
        index_name,
        trade_date,
        close,
        MAX(close) OVER (PARTITION BY index_name ORDER BY trade_date) AS running_peak
    FROM sector_index_prices
    WHERE trade_date BETWEEN '2020-01-01' AND '2020-06-30'
)
SELECT
    index_name,
    MIN(trade_date) AS window_start,
    MAX(trade_date) AS window_end,
    MAX(running_peak) AS peak_close,
    MIN(close) AS trough_close,
    ROUND(((MIN(close) / MAX(running_peak)) - 1) * 100, 2) AS max_drawdown_pct
FROM window_prices
GROUP BY index_name
ORDER BY max_drawdown_pct ASC;


-- ----------------------------------------------------------------------------
-- 5. Sector correlation with Nifty 50 (co-movement analysis)
--    Business question: "Which sectors move closely with the broader market,
--    and which behave more independently (useful for diversification)?"
--
--    Uses Pearson correlation via CORR(), a standard aggregate in Postgres.
-- ----------------------------------------------------------------------------
SELECT
    sec.index_name,
    ROUND(CORR(sec.daily_return_pct, nifty.daily_return_pct)::numeric, 3) AS correlation_with_nifty50
FROM sector_index_prices sec
JOIN sector_index_prices nifty
    ON nifty.trade_date = sec.trade_date
    AND nifty.index_name = 'NIFTY 50'
WHERE sec.index_name <> 'NIFTY 50'
GROUP BY sec.index_name
ORDER BY correlation_with_nifty50 DESC;


-- ----------------------------------------------------------------------------
-- 6. Month-wise sector rotation -- which sector led each month
--    Business question: "Is there a pattern to which sector leads at
--    different points in the market cycle?"
-- ----------------------------------------------------------------------------
WITH monthly_returns AS (
    SELECT
        index_name,
        DATE_TRUNC('month', trade_date) AS month_start,
        (
            (ARRAY_AGG(close ORDER BY trade_date DESC))[1]
            / NULLIF((ARRAY_AGG(close ORDER BY trade_date ASC))[1], 0) - 1
        ) * 100 AS month_return_pct
    FROM sector_index_prices
    WHERE index_name <> 'NIFTY 50'
    GROUP BY index_name, DATE_TRUNC('month', trade_date)
),
ranked_months AS (
    SELECT
        month_start,
        index_name,
        month_return_pct,
        RANK() OVER (PARTITION BY month_start ORDER BY month_return_pct DESC) AS rnk
    FROM monthly_returns
)
SELECT month_start, index_name AS leading_sector, ROUND(month_return_pct::numeric, 2) AS return_pct
FROM ranked_months
WHERE rnk = 1
ORDER BY month_start;
