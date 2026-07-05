"""
fetch_data.py
-------------
Downloads historical daily OHLC data for a basket of NSE stocks and
sectoral indices using the `jugaad-data` library, and saves raw CSVs
to data/raw/.

Usage:
    python scripts/fetch_data.py

Requirements:
    pip install jugaad-data pandas

Notes:
    - jugaad-data pulls data directly from the NSE archives, so no API
      key is required.
    - NSE occasionally rate-limits / changes response formats. If a
      download fails, wait a bit and re-run -- the script skips files
      that already exist so it's safe to re-run.
"""

import time
from datetime import date
from pathlib import Path

import pandas as pd
from jugaad_data.nse import stock_df
from nselib import capital_market

# ---------------------------------------------------------------------------
# CONFIG -- edit this section to change the stock/sector universe or dates
# ---------------------------------------------------------------------------

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = date(2021, 1, 1)
END_DATE = date(2026, 1, 1)  # adjust to "today" if you want the latest data

# A representative basket across sectors (~25 stocks) rather than all 50,
# to keep download time and fundamentals collection manageable.
STOCK_UNIVERSE = {
    # symbol: sector
    "RELIANCE": "Energy",
    "ONGC": "Energy",
    "HDFCBANK": "Banking",
    "ICICIBANK": "Banking",
    "SBIN": "Banking",
    "KOTAKBANK": "Banking",
    "TCS": "IT",
    "INFY": "IT",
    "WIPRO": "IT",
    "HCLTECH": "IT",
    "SUNPHARMA": "Pharma",
    "DRREDDY": "Pharma",
    "CIPLA": "Pharma",
    "MARUTI": "Auto",
    "TATAMOTORS": "Auto",
    "M&M": "Auto",
    "HINDUNILVR": "FMCG",
    "ITC": "FMCG",
    "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG",
    "LT": "Infrastructure",
    "ULTRACEMCO": "Infrastructure",
    "ADANIPORTS": "Infrastructure",
    "BHARTIARTL": "Telecom",
    "TATASTEEL": "Metals",
}

SECTOR_INDICES = [
    "NIFTY 50",
    "NIFTY BANK",
    "NIFTY IT",
    "NIFTY PHARMA",
    "NIFTY AUTO",
    "NIFTY FMCG",
    "NIFTY METAL",
]


def fetch_stock(symbol: str) -> None:
    out_path = RAW_DIR / f"stock_{symbol}.csv"
    if out_path.exists():
        print(f"[skip] {symbol} already downloaded")
        return
    try:
        df = stock_df(symbol=symbol, from_date=START_DATE, to_date=END_DATE, series="EQ")
        df.to_csv(out_path, index=False)
        print(f"[ok]   {symbol}: {len(df)} rows -> {out_path.name}")
    except Exception as e:
        print(f"[fail] {symbol}: {e}")
    time.sleep(1)  # be polite to NSE's servers


def fetch_index(index_name: str) -> None:
    safe_name = index_name.replace(" ", "_")
    out_path = RAW_DIR / f"index_{safe_name}.csv"

    if out_path.exists():
        print(f"[skip] {index_name}")
        return

    try:
        df = capital_market.index_data(
            index=index_name,
            from_date=START_DATE.strftime("%d-%m-%Y"),
            to_date=END_DATE.strftime("%d-%m-%Y"),
        )

        if df.empty:
            print(f"[fail] {index_name}: no data returned")
            return

        df.to_csv(out_path, index=False)

        print(f"[ok] {index_name}: {len(df)} rows")

    except Exception as e:
        print(f"[fail] {index_name}: {e}")


def write_stock_master() -> None:
    """Writes a simple symbol -> sector mapping CSV used later in SQL load."""
    out_path = RAW_DIR / "stock_master.csv"
    pd.DataFrame(
        [{"symbol": s, "sector": sec} for s, sec in STOCK_UNIVERSE.items()]
    ).to_csv(out_path, index=False)
    print(f"[ok]   stock_master.csv written ({len(STOCK_UNIVERSE)} stocks)")


def main():
    print(f"Fetching data from {START_DATE} to {END_DATE}\n")

    print("== Stocks ==")
    for symbol in STOCK_UNIVERSE:
        fetch_stock(symbol)

    print("\n== Sector Indices ==")
    for index_name in SECTOR_INDICES:
        fetch_index(index_name)

    print("\n== Stock master (sector mapping) ==")
    write_stock_master()

    print("\nDone. Raw files are in:", RAW_DIR)


if __name__ == "__main__":
    main()
