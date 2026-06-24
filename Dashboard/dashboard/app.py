"""
app.py
------
Streamlit dashboard for the Indian Equity Sector Performance Analysis project.

Run with:
    streamlit run dashboard/app.py

Three pages (selectable from the sidebar):
    1. Market Overview      -- Nifty 50 trend + sector return heatmap
    2. Sector Deep Dive      -- drill into one sector's stocks
    3. Sector Rotation & Correlation -- which sector led each month, and
       how correlated each sector is with the broader market
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent))
from db import run_query  # noqa: E402

st.set_page_config(
    page_title="Indian Equity Sector Performance",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Cached data loaders -- cached so switching pages doesn't re-hit the DB
# ---------------------------------------------------------------------------


@st.cache_data(ttl=3600)
def load_sector_index_prices() -> pd.DataFrame:
    return run_query(
        "SELECT index_name, trade_date, close, daily_return_pct "
        "FROM sector_index_prices ORDER BY trade_date"
    )


@st.cache_data(ttl=3600)
def load_daily_prices() -> pd.DataFrame:
    return run_query(
        "SELECT dp.symbol, sm.sector, dp.trade_date, dp.close, dp.daily_return_pct "
        "FROM daily_prices dp JOIN stock_master sm ON sm.symbol = dp.symbol "
        "ORDER BY dp.trade_date"
    )


@st.cache_data(ttl=3600)
def load_sector_summary() -> pd.DataFrame:
    return run_query(
        """
        SELECT
            sm.sector,
            ROUND(AVG(dp.daily_return_pct)::numeric * 252, 2) AS annualized_return_pct,
            ROUND((STDDEV(dp.daily_return_pct) * SQRT(252))::numeric, 2) AS annualized_volatility_pct
        FROM daily_prices dp
        JOIN stock_master sm ON sm.symbol = dp.symbol
        WHERE dp.daily_return_pct IS NOT NULL
        GROUP BY sm.sector
        ORDER BY annualized_return_pct DESC
        """
    )


try:
    sector_index_df = load_sector_index_prices()
    stock_df = load_daily_prices()
    sector_summary_df = load_sector_summary()
except Exception as e:
    st.error(
        "Could not connect to the database. Make sure Postgres is running, "
        "the tables are loaded (see README), and your .env file has the "
        f"right connection details.\n\nError detail: {e}"
    )
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.title("📈 Sector Analysis")
page = st.sidebar.radio(
    "Page",
    ["Market Overview", "Sector Deep Dive", "Sector Rotation & Correlation"],
)

min_date = sector_index_df["trade_date"].min()
max_date = sector_index_df["trade_date"].max()
# st.date_input requires plain datetime.date objects, not pandas Timestamps
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date, end_date = min_date, max_date

sector_index_filtered = sector_index_df[
    (sector_index_df["trade_date"] >= start_date)
    & (sector_index_df["trade_date"] <= end_date)
]
stock_filtered = stock_df[
    (stock_df["trade_date"] >= start_date) & (stock_df["trade_date"] <= end_date)
]

# ---------------------------------------------------------------------------
# Page 1: Market Overview
# ---------------------------------------------------------------------------

if page == "Market Overview":
    st.title("Market Overview")
    st.caption(
        "Nifty 50 trend and sector-level performance for the selected date range."
    )

    nifty = sector_index_filtered[sector_index_filtered["index_name"] == "NIFTY 50"]

    col1, col2, col3 = st.columns(3)
    if not nifty.empty:
        period_return = (nifty["close"].iloc[-1] / nifty["close"].iloc[0] - 1) * 100
        col1.metric("Nifty 50 period return", f"{period_return:.2f}%")
    if not sector_summary_df.empty:
        best_row = sector_summary_df.iloc[0]
        worst_row = sector_summary_df.iloc[-1]
        col2.metric(
            "Best sector (annualized)",
            best_row["sector"],
            f"{best_row['annualized_return_pct']:.1f}%",
        )
        col3.metric(
            "Worst sector (annualized)",
            worst_row["sector"],
            f"{worst_row['annualized_return_pct']:.1f}%",
        )

    st.subheader("Nifty 50 Closing Price")
    if not nifty.empty:
        fig = px.line(nifty, x="trade_date", y="close")
        fig.update_layout(yaxis_title="Close (₹)", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No NIFTY 50 data found for this date range.")

    st.subheader("Sector Returns Heatmap (Month x Sector)")
    sectors_only = sector_index_filtered[
        sector_index_filtered["index_name"] != "NIFTY 50"
    ].copy()
    if not sectors_only.empty:
        sectors_only["month"] = sectors_only["trade_date"].dt.to_period("M").astype(str)
        monthly = (
            sectors_only.groupby(["index_name", "month"])["daily_return_pct"]
            .sum()
            .reset_index()
        )
        pivot = monthly.pivot(index="index_name", columns="month", values="daily_return_pct")
        fig = px.imshow(
            pivot,
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            aspect="auto",
            labels=dict(color="Monthly Return %"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sector index data found for this date range.")

    st.subheader("Sector Risk vs. Return")
    if not sector_summary_df.empty:
        fig = px.scatter(
            sector_summary_df,
            x="annualized_volatility_pct",
            y="annualized_return_pct",
            text="sector",
            labels={
                "annualized_volatility_pct": "Annualized Volatility %",
                "annualized_return_pct": "Annualized Return %",
            },
        )
        fig.update_traces(textposition="top center", marker=dict(size=12))
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Page 2: Sector Deep Dive
# ---------------------------------------------------------------------------

elif page == "Sector Deep Dive":
    st.title("Sector Deep Dive")

    sectors = sorted(stock_filtered["sector"].dropna().unique().tolist())
    selected_sector = st.selectbox("Choose a sector", sectors)

    sector_stocks = stock_filtered[stock_filtered["sector"] == selected_sector]

    st.subheader(f"{selected_sector} — Stock Price Trends")
    if not sector_stocks.empty:
        fig = px.line(sector_stocks, x="trade_date", y="close", color="symbol")
        fig.update_layout(yaxis_title="Close (₹)", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"{selected_sector} — Stock Performance Summary")
    summary_rows = []
    for symbol, grp in sector_stocks.groupby("symbol"):
        grp = grp.sort_values("trade_date")
        if len(grp) < 2:
            continue
        total_return = (grp["close"].iloc[-1] / grp["close"].iloc[0] - 1) * 100
        vol = grp["daily_return_pct"].std() * (252 ** 0.5)
        summary_rows.append(
            {
                "Symbol": symbol,
                "Total Return %": round(total_return, 2),
                "Annualized Volatility %": round(vol, 2) if pd.notna(vol) else None,
            }
        )
    summary_df = pd.DataFrame(summary_rows).sort_values(
        "Total Return %", ascending=False
    )
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    if not summary_df.empty:
        col1, col2 = st.columns(2)
        col1.metric("Best performer", summary_df.iloc[0]["Symbol"], f"{summary_df.iloc[0]['Total Return %']}%")
        col2.metric("Worst performer", summary_df.iloc[-1]["Symbol"], f"{summary_df.iloc[-1]['Total Return %']}%")

# ---------------------------------------------------------------------------
# Page 3: Sector Rotation & Correlation
# ---------------------------------------------------------------------------

elif page == "Sector Rotation & Correlation":
    st.title("Sector Rotation & Correlation")

    st.subheader("Correlation with Nifty 50")
    nifty = sector_index_filtered[sector_index_filtered["index_name"] == "NIFTY 50"][
        ["trade_date", "daily_return_pct"]
    ].rename(columns={"daily_return_pct": "nifty_return"})

    sectors_only = sector_index_filtered[sector_index_filtered["index_name"] != "NIFTY 50"]
    corr_rows = []
    for index_name, grp in sectors_only.groupby("index_name"):
        merged = grp.merge(nifty, on="trade_date", how="inner")
        if len(merged) > 1:
            corr = merged["daily_return_pct"].corr(merged["nifty_return"])
            corr_rows.append({"Sector Index": index_name, "Correlation with Nifty 50": round(corr, 3)})

    corr_df = pd.DataFrame(corr_rows).sort_values(
        "Correlation with Nifty 50", ascending=False
    )
    if not corr_df.empty:
        fig = px.bar(
            corr_df,
            x="Correlation with Nifty 50",
            y="Sector Index",
            orientation="h",
            color="Correlation with Nifty 50",
            color_continuous_scale="RdYlGn",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Monthly Sector Leadership")
    st.caption("Which sector delivered the highest return in each month.")
    if not sectors_only.empty:
        df = sectors_only.copy()
        df["month"] = df["trade_date"].dt.to_period("M").astype(str)
        monthly_returns = df.groupby(["index_name", "month"])["daily_return_pct"].sum().reset_index()
        idx = monthly_returns.groupby("month")["daily_return_pct"].idxmax()
        leaders = monthly_returns.loc[idx].sort_values("month")
        leaders = leaders.rename(
            columns={"index_name": "Leading Sector", "daily_return_pct": "Return %", "month": "Month"}
        )
        leaders["Return %"] = leaders["Return %"].round(2)
        st.dataframe(leaders, use_container_width=True, hide_index=True)

        fig = px.bar(leaders, x="Month", y="Return %", color="Leading Sector")
        st.plotly_chart(fig, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data source: NSE historical data via jugaad-data. "
    "For educational/portfolio purposes only — not investment advice."
)
