# questions/question_q1.py

import pandas as pd
from kpi_engine.margin import compute_margin
from dateutil.relativedelta import relativedelta
import streamlit as st

def run(df):
    df_margin = compute_margin(df)

    if "Month" not in df_margin or "Client" not in df_margin or "Margin %" not in df_margin:
        st.error("Required fields missing. Ensure Margin % calculation is correctly applied.")
        return

    # Get the latest quarter
    latest_month = df_margin["Month"].max()
    quarter_start = latest_month - relativedelta(months=2)
    quarter_data = df_margin[df_margin["Month"] >= quarter_start]

    # Group by Client and calculate average margin
    grouped = (
        quarter_data.groupby("Client")["Margin %"]
        .mean()
        .reset_index()
        .rename(columns={"Margin %": "Avg Margin %"})
    )

    # Clean and filter
    grouped = grouped.dropna(subset=["Avg Margin %"])
    grouped["Avg Margin %"] = grouped["Avg Margin %"].round(2)
    low_margin_clients = grouped[grouped["Avg Margin %"] < 30].copy()
    low_margin_clients = low_margin_clients.sort_values("Avg Margin %")

    # 🔹 Text summary (Markdown)
    total_clients = grouped["Client"].nunique()
    low_margin_count = low_margin_clients["Client"].nunique()
    proportion = (low_margin_count / total_clients * 100) if total_clients else 0

    summary = (
        f"🔍 **In the last quarter**, **{low_margin_count} accounts** had an average margin below **30%**, "
        f"which is **{proportion:.1f}%** of all **{total_clients} accounts**."
    )
    st.markdown(summary)

    # 🔹 Show table
    st.dataframe(low_margin_clients.reset_index(drop=True))

    # Also return dict for logging if needed
    return {
        "summary": summary,
        "table": low_margin_clients
    }
