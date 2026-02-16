import os
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

from src.data_preprocessing import preprocess_sales
from src.visualization import (
    plot_monthly_revenue,
    plot_top_products,
    plot_revenue_by_country,
    plot_profit_box,
    plot_category_heatmap,
    plot_treemap_top_products,
    plot_country_choropleth,
)

st.set_page_config(layout="wide", page_title="Bike Sales Dashboard")


def local_css(path: Path):
    try:
        with open(path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        # silently continue if CSS not available
        return


local_css(Path(__file__).resolve().parent / "static" / "styles.css")

st.markdown(
    """
<div class='header-hero'>
  <h1>Bike Sales Dashboard</h1>
  <p>Interactive sales analytics — filter by country, category, and time.</p>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    """
    Locate and load Sales.csv from common locations.

    This cached function only attempts to read CSV files from disk (no
    Streamlit widgets) so it's safe to cache. If no file is found an
    empty DataFrame is returned and the caller should prompt for upload.
    """
    import logging
    import os
    import re

    logger = logging.getLogger(__name__)

    cwd = os.getcwd()
    candidates = [
        os.path.join(cwd, "data", "Sales.csv"),
        os.path.join(cwd, "data", "sales.csv"),
        "/Users/krishnarawat/Desktop/Data Science/sales.csv",
        os.path.join(cwd, "Sales.csv"),
        os.path.join(cwd, "sales.csv"),
        os.path.join(os.path.dirname(__file__), "..", "Sales.csv"),
    ]

    df = None
    for p in candidates:
        try:
            if os.path.exists(p):
                # Try fast, strict read first (C engine). Do NOT pass parse_dates
                # until we've normalized column names.
                try:
                    df = pd.read_csv(p, low_memory=False)
                except Exception:
                    # Fallback: use python engine and skip malformed lines
                    try:
                        df = pd.read_csv(p, engine="python", on_bad_lines="skip", skipinitialspace=True)
                    except TypeError:
                        # Older pandas: use error_bad_lines / warn_bad_lines
                        df = pd.read_csv(p, engine="python", error_bad_lines=False, warn_bad_lines=True, skipinitialspace=True)
                df_path = p
                break
        except Exception:
            logger.exception("Failed reading candidate CSV: %s", p)

    # If no file found on disk return empty DataFrame to let caller handle upload
    if df is None:
        return pd.DataFrame()

    # Strip whitespace from column names
    try:
        df.columns = df.columns.astype(str).str.strip()
    except Exception:
        logger.exception("Failed to normalize column names")

    # Heuristic to find a date-like column
    chosen = None
    if "Date" in df.columns:
        chosen = "Date"
    else:
        pattern = re.compile(r"date|time", re.I)
        matches = [c for c in df.columns if pattern.search(c)]
        if matches:
            chosen = matches[0]

    # If not found by name, try to infer by parsing a sample of each column
    if chosen is None:
        best_col = None
        best_parsed = 0
        for col in df.columns:
            try:
                sample = df[col].dropna().astype(str).head(500)
                if sample.empty:
                    continue
                parsed = pd.to_datetime(sample, errors="coerce", infer_datetime_format=True)
                n_parsed = int(parsed.notna().sum())
                if n_parsed > best_parsed:
                    best_parsed = n_parsed
                    best_col = col
            except Exception:
                continue
        # require at least some reasonable fraction to accept the column
        if best_col is not None and best_parsed >= max(1, int(0.5 * min(500, len(df)))):
            chosen = best_col

    # If still not found, return raw df (caller may upload or handle)
    if chosen is None:
        return df

    # Convert chosen column to datetime safely
    try:
        df[chosen] = pd.to_datetime(df[chosen], dayfirst=False, errors="coerce", infer_datetime_format=True)
    except Exception:
        logger.exception("Failed to convert column %s to datetime", chosen)

    # Rename to `Date` for downstream consistency
    if chosen != "Date":
        try:
            df.rename(columns={chosen: "Date"}, inplace=True)
        except Exception:
            logger.exception("Failed to rename date column %s to 'Date'", chosen)

    return df

# Load and preprocess
raw = load_data()

# If loader didn't find a file on disk, prompt user to upload (avoid caching widgets)
if raw.empty:
    uploaded = st.file_uploader("Upload Sales CSV (if not found automatically)", type=["csv"])
    if uploaded is None:
        st.error("Sales.csv not found. Place `Sales.csv` into the project `data/` folder or upload it.")
        st.stop()
    # Read uploaded file without going through the cached function
    import csv as _csv

    def _safe_read_csv(fileobj):
        # Try several pandas read_csv options to handle malformed rows.
        # Note: `low_memory` is not supported with engine='python', so only
        # include it for C-engine attempts.
        read_attempts = [
            {"kwargs": {"low_memory": False}},
            {"kwargs": {"engine": "python", "on_bad_lines": "warn"}},
            {"kwargs": {"engine": "python", "sep": None, "encoding": "utf-8", "quoting": _csv.QUOTE_MINIMAL, "on_bad_lines": "warn"}},
        ]

        last_exc = None
        for attempt in read_attempts:
            try:
                fileobj.seek(0)
                return pd.read_csv(fileobj, **attempt["kwargs"])
            except TypeError:
                # Older pandas may not accept `on_bad_lines`; try the older
                # `error_bad_lines` / `warn_bad_lines` arguments instead.
                try:
                    fileobj.seek(0)
                    fb_kwargs = attempt["kwargs"].copy()
                    fb_kwargs.pop("on_bad_lines", None)
                    # ensure we don't pass low_memory with python engine
                    if fb_kwargs.get("engine") == "python":
                        fb_kwargs.pop("low_memory", None)
                    fb_kwargs.update({"engine": "python", "error_bad_lines": False, "warn_bad_lines": True})
                    return pd.read_csv(fileobj, **fb_kwargs)
                except Exception as e:
                    last_exc = e
                    continue
            except Exception as e:
                last_exc = e
                continue

        # if all attempts failed, raise the last exception
        raise last_exc if last_exc is not None else ValueError("Failed to parse CSV")

    try:
        raw = _safe_read_csv(uploaded)
        raw.columns = raw.columns.astype(str).str.strip()
    except Exception as exc:
        st.error(f"Failed to read uploaded CSV: {exc}")
        st.stop()

    # try to detect and convert a date column from the uploaded file
    date_col = None
    if "Date" in raw.columns:
        date_col = "Date"
    else:
        import re
        pattern = re.compile(r"date|time", re.I)
        candidates = [c for c in raw.columns if pattern.search(c)]
        if candidates:
            date_col = candidates[0]
        else:
            # infer by sampling
            best_col = None
            best_parsed = 0
            for col in raw.columns:
                try:
                    sample = raw[col].dropna().astype(str).head(200)
                    if sample.empty:
                        continue
                    parsed = pd.to_datetime(sample, errors="coerce", infer_datetime_format=True)
                    n_parsed = int(parsed.notna().sum())
                    if n_parsed > best_parsed:
                        best_parsed = n_parsed
                        best_col = col
                except Exception:
                    continue
            if best_col is not None and best_parsed >= max(1, int(0.5 * min(200, len(raw)))):
                date_col = best_col

    if date_col is not None:
        try:
            raw[date_col] = pd.to_datetime(raw[date_col], dayfirst=False, errors="coerce", infer_datetime_format=True)
            if date_col != "Date":
                raw.rename(columns={date_col: "Date"}, inplace=True)
        except Exception:
            # non-fatal; preprocessing may handle missing dates
            pass

@st.cache_data(hash_funcs={
    pd.DataFrame: lambda df: df.to_csv(index=False).encode("utf-8")
})
def preprocess_cached(df):
    return preprocess_sales(df)

# Preprocess and validate
df = preprocess_cached(raw)

# Ensure Date column exists and is usable
if 'Date' not in df.columns or df['Date'].isna().all():
    st.error('No valid `Date` column found after parsing. Please check `data/Sales.csv` or upload a correct CSV.')
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    years = sorted(df['Year'].dropna().unique().tolist())
    selected_years = st.multiselect("Year", years, default=years)
    countries = sorted(df['Country'].dropna().unique().tolist())
    selected_countries = st.multiselect("Country", countries, default=countries)
    categories = sorted(df['Product_Category'].dropna().unique().tolist())
    selected_categories = st.multiselect("Product Category", categories, default=categories)
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    date_range = st.date_input("Date range", value=(min_date, max_date))

# Apply filters
filtered = df[
    (df['Year'].isin(selected_years)) &
    (df['Country'].isin(selected_countries)) &
    (df['Product_Category'].isin(selected_categories)) &
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1]))
]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${filtered['Revenue'].sum():,.0f}")
col2.metric("Total Profit", f"${filtered['Profit'].sum():,.0f}")
col3.metric("Total Orders", f"{filtered['Order_Quantity'].sum():,}")
col4.metric("Avg Order Value", f"${(filtered['Revenue'].sum() / max(1, filtered.shape[0])):,.2f}")

# Main visualizations
st.header("Time Series")
st.plotly_chart(plot_monthly_revenue(filtered), use_container_width=True)

st.header("Top Products")
st.plotly_chart(plot_top_products(filtered, top_n=10), use_container_width=True)

st.header("Geographic & Category Views")
c1, c2 = st.columns([2,1])
with c1:
    st.plotly_chart(plot_revenue_by_country(filtered), use_container_width=True)
with c2:
    st.plotly_chart(plot_profit_box(filtered), use_container_width=True)

# Additional charts: heatmap, treemap, country map
st.header("Additional Charts")
hc1, hc2 = st.columns([2,1])
with hc1:
    st.subheader("Category x Month Heatmap")
    st.plotly_chart(plot_category_heatmap(filtered, agg_col='Revenue'), use_container_width=True)
with hc2:
    st.subheader("Top Products Treemap")
    st.plotly_chart(plot_treemap_top_products(filtered, top_n=40), use_container_width=True)

st.subheader("Country Map")
st.plotly_chart(plot_country_choropleth(filtered, agg_col='Revenue'), use_container_width=True)

st.header("Data Preview")
st.dataframe(filtered.head(200))

st.markdown("---")
st.caption("Dashboard generated from Sales.csv — refine filters to explore.")
