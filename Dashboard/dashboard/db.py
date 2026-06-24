"""
db.py
-----
Shared database connection helper for the Streamlit dashboard.
Reads connection details from environment variables so credentials are
never hardcoded into the repo.

Set these in a .env file (see .env.example) or your shell environment:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import os

import pandas as pd
from sqlalchemy import create_engine

# Load .env file if python-dotenv is available (optional convenience)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_engine():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "stockdata")
    user = os.getenv("DB_USER", os.getenv("USER", "postgres"))
    password = os.getenv("DB_PASSWORD", "")

    if password:
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    else:
        # Local Postgres on Mac via Homebrew typically needs no password
        url = f"postgresql+psycopg2://{user}@{host}:{port}/{name}"

    return create_engine(url)


def run_query(sql: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)
