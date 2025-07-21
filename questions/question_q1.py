# questions/question_q1.py

import pandas as pd
from kpi_engine.margin import compute_margin
from dateutil.relativedelta import relativedelta
import streamlit as st
import matplotlib.pyplot as plt

def run(df, user_query):
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

    # 🔹 Layout: Table + Chart side by side
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📋 Accounts with Margin < 30%")
        st.dataframe(low_margin_clients.reset_index(drop=True), use_container_width=True)

    with col2:
        st.markdown("#### 📊 Margin % by Client (Bar Chart)")
        fig, ax = plt.subplots()
        ax.barh(low_margin_clients["Client"], low_margin_clients["Avg Margin %"], color='tomato')
        ax.set_xlabel("Avg Margin %")
        ax.set_ylabel("Client")
        ax.set_title("Clients with Avg Margin < 30%")
        plt.tight_layout()
        st.pyplot(fig)

    return None
