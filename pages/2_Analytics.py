from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("analytics.db")

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

st.title("📈 Analytics Dashboard")

@st.cache_data(show_spinner=False)
def load_data(db_path: Path) -> pd.DataFrame:
    if not db_path.exists():
        return pd.DataFrame(columns=["platform","post_id","permalink","likes","comments","views","shares","created_time"])
    with sqlite3.connect(db_path.as_posix()) as conn:
        try:
            df = pd.read_sql_query("SELECT * FROM analytics", conn)
        except Exception:
            return pd.DataFrame(columns=["platform","post_id","permalink","likes","comments","views","shares","created_time"])
    # Normalize dtypes
    if not df.empty and "created_time" in df.columns:
        # Try parse ISO or RFC datetimes
        df["created_time"] = pd.to_datetime(df["created_time"], errors="coerce")
    return df


def kpi_card(label: str, value: float|int|None, fmt: str = ","):
    c1, c2 = st.columns([2, 3])
    with c1:
        st.caption(label)
    with c2:
        st.metric(label="", value=(f"{value:{fmt}}" if pd.notna(value) else "-"))


def sidebar_filters(df: pd.DataFrame):
    st.sidebar.header("Filters")
    platforms = sorted(df["platform"].dropna().unique().tolist()) if not df.empty else []

    default_start = (datetime.utcnow() - timedelta(days=30)).date()
    default_end = datetime.utcnow().date()

    selected_platforms = st.sidebar.multiselect("Platform", options=platforms, default=platforms)
    date_range = st.sidebar.date_input(
        "Date range",
        value=(default_start, default_end),
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, default_end

    return selected_platforms, pd.to_datetime(start_date), pd.to_datetime(end_date) + pd.Timedelta(days=1)


def apply_filters(df: pd.DataFrame, platforms: list[str], start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if df.empty:
        return df
    f = df.copy()
    if platforms:
        f = f[f["platform"].isin(platforms)]
    if "created_time" in f.columns:
        f = f[(f["created_time"] >= start) & (f["created_time"] < end)]
    return f


def draw_trends(df: pd.DataFrame):
    if df.empty:
        st.info("No data to display.")
        return

    # Aggregate by date
    if "created_time" in df.columns:
        df = df.copy()
        df["date"] = df["created_time"].dt.date

    # KPIs
    total_views = df["views"].fillna(0).sum()
    total_likes = df["likes"].fillna(0).sum()
    total_comments = df["comments"].fillna(0).sum()
    total_shares = df["shares"].fillna(0).sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Views", f"{int(total_views):,}")
    with c2:
        st.metric("Total Likes", f"{int(total_likes):,}")
    with c3:
        st.metric("Total Comments", f"{int(total_comments):,}")
    with c4:
        st.metric("Total Shares", f"{int(total_shares):,}")

    st.markdown("---")

    # Time series by metric
    ts_cols = ["views", "likes", "comments", "shares"]
    for metric in ts_cols:
        ts = df.groupby("date")[metric].sum().reset_index()
        ts["date"] = pd.to_datetime(ts["date"])  # ensure datetime for charts
        st.subheader(f"Trend: {metric.title()}")
        st.line_chart(ts.set_index("date")[metric])

    st.markdown("---")

    # Platform breakdown
    st.subheader("Platform Breakdown (Totals)")
    breakdown = df.groupby("platform")[ts_cols].sum().reset_index()
    c1, c2 = st.columns(2)
    with c1:
        st.bar_chart(breakdown.set_index("platform")["views"])
    with c2:
        st.bar_chart(breakdown.set_index("platform")["likes"])

    st.markdown("---")

    # Top posts table
    st.subheader("Top Posts by Views")
    top = df.sort_values(by=["views","likes","comments"], ascending=False).head(30)
    # Create a clickable link column if permalink exists
    if "permalink" in top.columns:
        top = top.copy()
        top["link"] = top["permalink"].fillna("")
    st.dataframe(top[["platform", "created_time", "views", "likes", "comments", "shares", "permalink"]], use_container_width=True)

    # Download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv, file_name="analytics_filtered.csv", mime="text/csv")


def main():
    df = load_data(DB_PATH)
    plats, start, end = sidebar_filters(df)
    filtered = apply_filters(df, plats, start, end)
    draw_trends(filtered)


if __name__ == "__main__":
    main()
