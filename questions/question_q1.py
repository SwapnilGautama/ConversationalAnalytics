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

    # Filter: margin < 30% and revenue > 0
    filtered_df = agg[(agg["Latest Margin %"] < 30) & (agg["Revenue (₹ Cr)"] > 0)]

    # Sort descending and select top 10
    top_10 = filtered_df.sort_values("Latest Margin %", ascending=False).head(10)

    # 🔹 Summary
    total_clients = agg["Client"].nunique()
    low_margin_count = filtered_df["Client"].nunique()
    proportion = (low_margin_count / total_clients * 100) if total_clients else 0

    st.markdown(
        f"🔍 **In the last quarter**, **{low_margin_count} accounts** had an average margin below **30%** "
        f"and non-zero revenue, which is **{proportion:.1f}%** of all **{total_clients} accounts**."
    )

    # 🔹 Layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📋 Accounts with Margin < 30% (non-zero revenue)")
        st.dataframe(
            top_10[["Client", "Latest Margin %", "Revenue (₹ Cr)", "Cost (₹ Cr)"]].reset_index(drop=True),
            use_container_width=True
        )

    with col2:
        st.markdown("#### 📊 Margin % by Client (Bar Chart)")
        fig, ax = plt.subplots()
        ax.barh(top_10["Client"], top_10["Latest Margin %"], color='#E7F3FF', edgecolor='#D3D3D3', linewidth=0.8)
        ax.set_xlabel("Margin % (Latest Quarter)")
        ax.set_ylabel("Client")
        ax.set_title("Top 10 Clients with Margin < 30%")
        ax.set_xlim(-100, 100)
        ax.invert_yaxis()
        ax.grid(axis='x', linestyle='--', alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig)

    return None
