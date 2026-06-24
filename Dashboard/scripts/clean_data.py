"""
clean_data.py
-------------
Reads raw CSVs from data/raw/, standardizes column names and types,
computes daily returns, and writes clean CSVs to data/processed/
ready to be loaded into the SQL database.

Usage:
    python scripts/clean_data.py
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_stock_file(path: Path) -> pd.DataFrame:
    symbol = path.stem.replace("stock_", "")
    df = pd.read_csv(path)

    # jugaad-data's stock_df columns include: DATE, SYMBOL, SERIES, OPEN,
    # HIGH, LOW, PREV. CLOSE, LTP, CLOSE, VOLUME, VALUE, ... -- normalize names.
    df.columns = [c.strip().upper().replace(" ", "_") for c in df.columns]
    rename_map = {
        "DATE": "trade_date",
        "OPEN": "open",
        "HIGH": "high",
        "LOW": "low",
        "CLOSE": "close",
        "VOLUME": "volume",
    }
    df = df.rename(columns=rename_map)
    keep_cols = ["trade_date", "open", "high", "low", "close", "volume"]
    df = df[[c for c in keep_cols if c in df.columns]].copy()

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values("trade_date").reset_index(drop=True)

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["symbol"] = symbol
    df["daily_return_pct"] = df["close"].pct_change() * 100

    return df


def clean_index_file(path: Path) -> pd.DataFrame:
    index_name = path.stem.replace("index_", "").replace("_", " ")
    df = pd.read_csv(path)

    # jugaad-data's index_df() uses different column names than stock_df():
    # the date column is "HistoricalDate" (not "DATE"), and there's no
    # VOLUME column for indices.
    df.columns = [c.strip().upper().replace(" ", "_") for c in df.columns]
    rename_map = {
        "HISTORICALDATE": "trade_date",
        "DATE": "trade_date",  # fallback in case the source format ever changes
        "OPEN": "open",
        "HIGH": "high",
        "LOW": "low",
        "CLOSE": "close",
    }
    df = df.rename(columns=rename_map)
    keep_cols = ["trade_date", "open", "high", "low", "close"]
    missing = [c for c in keep_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"{path.name}: expected columns {missing} not found. "
            f"Actual columns were: {list(df.columns)}"
        )
    df = df[keep_cols].copy()

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values("trade_date").reset_index(drop=True)

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["index_name"] = index_name
    df["daily_return_pct"] = df["close"].pct_change() * 100

    return df


def main():
    stock_frames = []
    for path in sorted(RAW_DIR.glob("stock_*.csv")):
        if path.name == "stock_master.csv":
            continue  # this is the sector-mapping file, not a price file
        print(f"Cleaning {path.name} ...")
        stock_frames.append(clean_stock_file(path))

    if stock_frames:
        all_stocks = pd.concat(stock_frames, ignore_index=True)
        out_path = PROCESSED_DIR / "daily_prices.csv"
        all_stocks.to_csv(out_path, index=False)
        print(f"[ok] Wrote {len(all_stocks)} rows -> {out_path.name}")

    index_frames = []
    for path in sorted(RAW_DIR.glob("index_*.csv")):
        print(f"Cleaning {path.name} ...")
        index_frames.append(clean_index_file(path))

    if index_frames:
        all_indices = pd.concat(index_frames, ignore_index=True)
        out_path = PROCESSED_DIR / "sector_index_prices.csv"
        all_indices.to_csv(out_path, index=False)
        print(f"[ok] Wrote {len(all_indices)} rows -> {out_path.name}")

    master_path = RAW_DIR / "stock_master.csv"
    if master_path.exists():
        master_df = pd.read_csv(master_path)
        master_df.to_csv(PROCESSED_DIR / "stock_master.csv", index=False)
        print(f"[ok] Copied stock_master.csv ({len(master_df)} stocks)")

    print("\nProcessed files are in:", PROCESSED_DIR)


if __name__ == "__main__":
    main()
