-- ============================================================================
-- schema.sql
-- Creates the tables used by this project.
-- Works on PostgreSQL. For SQLite/SQL Server, drop SERIAL/adjust types as
-- needed -- only minor syntax differences are required.
-- ============================================================================

DROP TABLE IF EXISTS daily_prices;
DROP TABLE IF EXISTS sector_index_prices;
DROP TABLE IF EXISTS stock_master;

-- Sector / classification lookup for each stock
CREATE TABLE stock_master (
    symbol      VARCHAR(20) PRIMARY KEY,
    sector      VARCHAR(50) NOT NULL
);

-- Daily OHLC + return data for individual stocks
CREATE TABLE daily_prices (
    id                SERIAL PRIMARY KEY,
    symbol            VARCHAR(20) NOT NULL REFERENCES stock_master(symbol),
    trade_date        DATE NOT NULL,
    open              NUMERIC(12, 2),
    high              NUMERIC(12, 2),
    low               NUMERIC(12, 2),
    close             NUMERIC(12, 2),
    volume            BIGINT,
    daily_return_pct  NUMERIC(8, 4),
    UNIQUE (symbol, trade_date)
);

CREATE INDEX idx_daily_prices_symbol_date ON daily_prices (symbol, trade_date);

-- Daily OHLC + return data for sector/benchmark indices
CREATE TABLE sector_index_prices (
    id                SERIAL PRIMARY KEY,
    index_name        VARCHAR(50) NOT NULL,
    trade_date        DATE NOT NULL,
    open              NUMERIC(12, 2),
    high              NUMERIC(12, 2),
    low               NUMERIC(12, 2),
    close             NUMERIC(12, 2),
    daily_return_pct  NUMERIC(8, 4),
    UNIQUE (index_name, trade_date)
);

CREATE INDEX idx_sector_index_name_date ON sector_index_prices (index_name, trade_date);
