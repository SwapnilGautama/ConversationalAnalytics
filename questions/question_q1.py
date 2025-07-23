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

    # Identify latest quarter range
    latest_month = df_margin["Month"].max()
    quarter_start = latest_month - relativedelta(months=2)

    # Filter latest quarter
    latest_qtr = df_margin[(df_margin["Month"] >= quarter_start) & (df_margin["Month"] <= latest_month)]

    # Aggregate Margin %, Revenue, Cost
    agg = latest_qtr.groupby("Client").agg({
        "Margin %": "mean",
        "Revenue": "sum",
        "Cost": "sum"
    }).reset_index()

    agg.rename(columns={
        "Margin %": "Latest Margin %",
        "Revenue": "Revenue (₹ Cr)",
        "Cost": "Cost (₹ Cr)"
    }, inplace=True)

    # Convert ₹ values to Cr and round
    agg["Revenue (₹ Cr)"] = (agg["Revenue (₹ Cr)"] / 1e7).round(2)
    agg["Cost (₹ Cr)"] = (agg["Cost (₹ Cr)"] / 1e7).round(2)
    agg["Latest Margin %"] = agg["Latest Margin %"].round(2)

    # Filter where margin is below 30%
    low_margin_df = agg[agg["Latest Margin %"] < 30].copy()

    # Sort in ascending order and keep only top 10
    low_margin_df = low_margin_df.sort_values("Latest Margin %").head(10)

    # 🔹 Summary text
    total_clients = agg["Client"].nunique()
    low_margin_count = agg[agg["Latest Margin %"] < 30]["Client"].nunique()
    proportion = (low_margin_count / total_clients * 100) if total_clients else 0

    summary = (
        f"🔍 **In the last quarter**, **{low_margin_count} accounts** had an average margin below **30%**, "
        f"which is **{proportion:.1f}%** of all **{total_clients} accounts**."
    )
    st.markdown(summary)

    # 🔹 Layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📋 Accounts with Margin < 30%")
        st.dataframe(
            low_margin_df[["Client", "Latest Margin %", "Revenue (₹ Cr)", "Cost (₹ Cr)"]].reset_index(drop=True),
            use_container_width=True
        )

    with col2:
        st.markdown("#### 📊 Margin % by Client (Bar Chart)")
        fig, ax = plt.subplots()
        ax.barh(low_margin_df["Client"], low_margin_df["Latest Margin %"], color='tomato')
        ax.set_xlabel("Margin % (Latest Quarter)")
        ax.set_ylabel("Client")
        ax.set_title("Top 10 Clients with Margin < 30%")
        plt.tight_layout()
        st.pyplot(fig)

    return None
