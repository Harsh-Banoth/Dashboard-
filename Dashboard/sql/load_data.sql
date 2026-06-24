-- ============================================================================
-- load_data.sql
-- Loads the cleaned CSVs from data/processed/ into the tables created by
-- schema.sql. Run schema.sql first.
--
-- This uses PostgreSQL's \copy (client-side), which works from psql without
-- needing server-side file access permissions. Run from the project root, e.g.:
--
--   psql -d your_database -f sql/load_data.sql
--
-- If you're using a GUI tool (pgAdmin, DBeaver, Azure Data Studio, SSMS for
-- SQL Server) instead, use that tool's "Import CSV" wizard pointed at the
-- same files and skip this script -- it's just an alternative path to the
-- same result.
-- ============================================================================

\copy stock_master (symbol, sector) FROM 'data/processed/stock_master.csv' WITH (FORMAT csv, HEADER true);

\copy daily_prices (symbol, trade_date, open, high, low, close, volume, daily_return_pct) FROM 'data/processed/daily_prices.csv' WITH (FORMAT csv, HEADER true);

\copy sector_index_prices (index_name, trade_date, open, high, low, close, daily_return_pct) FROM 'data/processed/sector_index_prices.csv' WITH (FORMAT csv, HEADER true);
