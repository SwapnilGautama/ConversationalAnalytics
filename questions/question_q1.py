# questions/question_q1.py

import pandas as pd
from kpi_engine.margin import compute_margin
from dateutil.relativedelta import relativedelta
import streamlit as st
import matplotlib.pyplot as plt

def run(df):
    df_margin = compute_margin(df)

    if "Month" not in df_margin or "Client" not in df_margin or "Margin %" not in df_margin:
        st.error("Required fields missing. Ensure Margin % calculation is correctly applied.")
        return

    # Identify latest and previous quarters
    latest_month = df_margin["Month"].max()
    quarter_start = latest_month - relativedelta(months=2)
    previous_quarter_start = quarter_start - relativedelta(months=3)
    previous_quarter_end = quarter_start - relativedelta(days=1)

    # Compute average margin for both quarters
    latest_qtr = df_margin[(df_margin["Month"] >= quarter_start) & (df_margin["Month"] <= latest_month)]
    prev_qtr = df_margin[(df_margin["Month"] >= previous_quarter_start) & (df_margin["Month"] <= previous_quarter_end)]

    latest_margin = latest_qtr.groupby("Client")["Margin %"].mean().reset_index(name="Latest Margin %")
    prev_margin = prev_qtr.groupby("Client")["Margin %"].mean().reset_index(name="Previous Margin %")

    # Merge the two
    combined = pd.merge(latest_margin, prev_margin, on="Client", how="left")
    combined = combined.dropna(subset=["Latest Margin %"])
    combined["Latest Margin %"] = combined["Latest Margin %"].round(2)
    combined["Previous Margin %"] = combined["Previous Margin %"].round(2)

    # Filter where latest margin < 30%
    low_margin_clients = combined[combined["Latest Margin %"] < 30].copy()
    low_margin_clients = low_margin_clients.sort_values("Latest Margin %")

    # 🔹 Text summary
    total_clients = combined["Client"].nunique()
    low_margin_count = low_margin_clients["Client"].nunique()
    proportion = (low_margin_count / total_clients * 100) if total_clients else 0

    summary = (
        f"🔍 **In the last quarter**, **{low_margin_count} accounts** had an average margin below **30%**, "
        f"which is **{proportion:.1f}%** of all **{total_clients} accounts**."
    )
    st.markdown(summary)

    # 🔹 Layout: Table + Bar Chart
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📋 Accounts with Margin < 30%")
        st.dataframe(
            low_margin_clients[["Client", "Latest Margin %", "Previous Margin %"]]
            .reset_index(drop=True),
            use_container_width=True
        )

    with col2:
        st.markdown("#### 📊 Margin % by Client (Bar Chart)")
        fig, ax = plt.subplots()
        ax.barh(low_margin_clients["Client"], low_margin_clients["Latest Margin %"], color='tomato')
        ax.set_xlabel("Margin % (Latest Quarter)")
        ax.set_ylabel("Client")
        ax.set_title("Clients with Avg Margin < 30%")
        plt.tight_layout()
        st.pyplot(fig)

    return None
