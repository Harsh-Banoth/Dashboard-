# Indian Equity Sector Performance Analysis

A SQL + Python (Streamlit) analysis of how different sectors of the Indian stock
market (NSE) have performed over time — built as a portfolio project for
Finance Analyst / Business Analyst roles.

Rather than just plotting stock prices, this project asks specific
business questions of the data: which sectors led, which lagged, how did
each sector behave during market corrections, and how correlated are
sectors with the broader market. The analytical work happens in SQL; the
results are visualized in an interactive Streamlit dashboard.

**New to this project / setting it up for the first time?** Use
[`SETUP_CHECKLIST.md`](./SETUP_CHECKLIST.md) for a linear, copy-paste
checklist (Mac-focused) that also covers the most common setup errors.

---

## Why this project

Most "stock dashboard" projects show a chart and stop there. This one is
built to demonstrate the actual skill set a Finance/Business Analyst role
needs:
- Translating a business question into a query
- Working confidently in SQL (window functions, aggregations, correlation)
- Building a clear, decision-oriented dashboard rather than a generic chart
- Writing up findings as an analyst would, not just generating numbers

---

## Business questions answered

1. Which sectors delivered the best risk-adjusted returns over the period?
2. Which individual stocks led and lagged within each sector?
3. How far did each sector fall (drawdown) during a market correction, and
   which sectors were most defensive?
4. Which sectors move closely with the broader market (Nifty 50), and
   which are more independent — useful for diversification thinking?
5. Does sector leadership rotate over time, and is there a visible pattern?

---

## Project structure

```
.
├── data/
│   ├── raw/              # Raw CSVs downloaded from NSE (gitignored, regenerate locally)
│   └── processed/        # Cleaned CSVs ready for SQL load (gitignored, regenerate locally)
├── scripts/
│   ├── fetch_data.py     # Downloads historical stock + sector index data from NSE
│   └── clean_data.py     # Cleans raw data, computes daily returns, writes processed CSVs
├── sql/
│   ├── schema.sql            # Table definitions
│   ├── load_data.sql         # Loads processed CSVs into the database
│   └── analysis_queries.sql  # The analytical core -- one query per business question
├── dashboard/
│   ├── app.py             # Streamlit dashboard (3 pages: Overview, Sector Deep Dive, Rotation & Correlation)
│   └── db.py              # Database connection helper (reads credentials from .env)
├── docs/
│   └── INSIGHTS_TEMPLATE.md  # Template for writing up your findings once you have results
├── requirements.txt
├── .env.example           # Template for database connection variables
├── SETUP_CHECKLIST.md      # Linear copy-paste setup guide + common error fixes
└── README.md
```

---

## Tech stack

| Layer            | Tool                                              |
|-------------------|----------------------------------------------------|
| Data source       | NSE historical data via the `jugaad-data` Python library |
| Data cleaning      | Python (pandas)                                   |
| Storage / analysis | SQL (PostgreSQL syntax; minor edits work for SQL Server/MySQL/SQLite) |
| Visualization      | Streamlit + Plotly (interactive Python dashboard) |

No paid API keys are required — `jugaad-data` reads NSE's own public
historical data archives.

---

## How it works, end to end

### 1. Fetch raw data
```bash
pip install -r requirements.txt
python scripts/fetch_data.py
```
This downloads daily OHLC data for a basket of ~25 NSE stocks spanning 8
sectors (Banking, IT, Pharma, Auto, FMCG, Energy, Infrastructure, Metals,
Telecom), plus the corresponding sector indices (Nifty Bank, Nifty IT,
etc.) and the Nifty 50 benchmark. Edit `STOCK_UNIVERSE` and
`SECTOR_INDICES` in `scripts/fetch_data.py` to change the universe or date
range. Files land in `data/raw/`.

### 2. Clean and prepare the data
```bash
python scripts/clean_data.py
```
This standardizes column names/types, sorts by date, and computes daily
percentage returns for every stock and index. Output lands in
`data/processed/` as three files: `daily_prices.csv`,
`sector_index_prices.csv`, and `stock_master.csv` (the sector mapping).

### 3. Load into a SQL database
```bash
# create the tables
psql -d your_database -f sql/schema.sql

# load the cleaned CSVs
psql -d your_database -f sql/load_data.sql
```
(If you're using a GUI tool like pgAdmin or DBeaver instead of `psql`,
run `schema.sql` there and use the tool's CSV import wizard pointed at the
files in `data/processed/` — same result, different interface.)

### 4. Run the analysis
Open `sql/analysis_queries.sql` and run each query against your database.
Each one is commented with the business question it answers. These are
also the queries the Streamlit dashboard's caching layer mirrors.

### 5. Run the Streamlit dashboard
```bash
# create a .env file with your DB credentials (copy from .env.example)
cp .env.example .env

streamlit run dashboard/app.py
```
This opens an interactive dashboard in your browser with three pages:
- **Market Overview** — Nifty 50 trend, sector returns heatmap, risk-vs-return scatter
- **Sector Deep Dive** — pick a sector, see its stocks' price trends and a ranked performance table
- **Sector Rotation & Correlation** — each sector's correlation with Nifty 50, and which sector led each month

All charts respect a date-range filter in the sidebar.

### 6. Write up your findings
Use `docs/INSIGHTS_TEMPLATE.md` to document what you found. This write-up
is arguably the most important deliverable for a resume project — it's
the narrative you'll actually talk through in interviews.

---

## Data scope and assumptions

- **Stock universe:** ~25 stocks across 8 sectors, chosen to be
  representative rather than exhaustive (full Nifty 50 coverage adds
  fetch time without changing the analytical approach).
- **Returns:** Price returns only — dividends are not factored in, so
  total return figures are a slight underestimate of true investor
  returns. This is noted explicitly in the insights template.
- **Frequency:** Daily closing-price based. Intraday volatility isn't
  captured.
- **Corporate actions:** `jugaad-data` pulls NSE's series data, which
  generally reflects adjusted prices for standard corporate actions, but
  it's worth spot-checking any stock that had a major split/bonus during
  your date range if a return number looks unusually large.

---

## Possible extensions
- Pull fundamentals (P/E, market cap) per stock and add valuation-based
  analysis alongside the return/volatility analysis
- Extend to the full Nifty 50 / Nifty 500
- Add dividend-adjusted total return calculations
- Automate periodic refresh with a scheduled script instead of one-time
  historical pull
- Add a macro overlay (repo rate changes, FII/DII flow data) to explain
  *why* certain sectors moved, not just *that* they moved

---

## Disclaimer
This project is for educational and portfolio purposes only. Nothing here
constitutes investment advice. Historical performance shown is not
indicative of future results.
# Dashboard-
