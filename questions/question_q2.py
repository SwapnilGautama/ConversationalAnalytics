import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

def analyze_margin_drop(segment_input):
    file_path = "sample_data/LnTPnL.xlsx"
    df = pd.read_excel(file_path)

    # Clean and filter
    df["Month"] = pd.to_datetime(df["Month"])
    df["MonthStr"] = df["Month"].dt.strftime("%b-%Y")
    df = df[df["Segment"] == segment_input]

    # Identify latest 2 months
    latest_months = sorted(df["Month"].dt.to_period("M").unique())[-2:]
    if len(latest_months) < 2:
        return f"❗Not enough data for MoM comparison in segment: {segment_input}", pd.DataFrame()

    prev_month, curr_month = latest_months
    df_filtered = df[df["Month"].dt.to_period("M").isin([prev_month, curr_month])]

    # Revenue & Cost tables
    df_filtered["Revenue"] = df_filtered[df_filtered["Type"] == "Revenue"]["Amount in INR"]
    df_filtered["Cost"] = df_filtered[df_filtered["Type"] == "Cost"]["Amount in INR"]

    # Pivot tables
    rev_df = df_filtered[df_filtered["Type"] == "Revenue"].pivot_table(
        index="Company_code", columns="MonthStr", values="Amount in INR", aggfunc="sum").fillna(0)
    cost_df = df_filtered[df_filtered["Type"] == "Cost"].pivot_table(
        index="Company_code", columns="MonthStr", values="Amount in INR", aggfunc="sum").fillna(0)

    # Align both DataFrames to common index
    common_index = rev_df.index.intersection(cost_df.index)
    rev_df = rev_df.loc[common_index]
    cost_df = cost_df.loc[common_index]

    # Calculate change
    rev_cols = list(rev_df.columns)
    cost_cols = list(cost_df.columns)
    rev_df["Revenue_Change"] = rev_df[rev_cols[1]] - rev_df[rev_cols[0]]
    cost_df["Cost_Change"] = cost_df[cost_cols[1]] - cost_df[cost_cols[0]]

    # Merge for margin analysis
    merged_df = pd.concat([rev_df, cost_df], axis=1)
    merged_df["Margin_Change"] = merged_df["Revenue_Change"] - merged_df["Cost_Change"]
    merged_df["Margin_%_Prev"] = ((rev_df[rev_cols[0]] - cost_df[cost_cols[0]]) / cost_df[cost_cols[0]]) * 100
    merged_df["Margin_%_Curr"] = ((rev_df[rev_cols[1]] - cost_df[cost_cols[1]]) / cost_df[cost_cols[1]]) * 100
    merged_df["Margin_%_Change"] = merged_df["Margin_%_Curr"] - merged_df["Margin_%_Prev"]
    merged_df = merged_df.sort_values("Margin_%_Change")

    # Top contributors to margin drop
    top_drops = merged_df.head(5)

    # Group1-4 cost analysis
    group_cols = ["Group 1", "Group 2", "Group 3", "Group 4"]
    cost_grp = df_filtered[df_filtered["Type"] == "Cost"]
    group_cost_changes = cost_grp.groupby(["MonthStr"])[group_cols].sum().fillna(0)
    group_cost_diff = group_cost_changes.diff().iloc[-1]

    # Summary
    total_rev_prev = df_filtered[(df_filtered["Type"] == "Revenue") & (df_filtered["Month"].dt.to_period("M") == prev_month)]["Amount in INR"].sum()
    total_rev_curr = df_filtered[(df_filtered["Type"] == "Revenue") & (df_filtered["Month"].dt.to_period("M") == curr_month)]["Amount in INR"].sum()
    total_cost_prev = df_filtered[(df_filtered["Type"] == "Cost") & (df_filtered["Month"].dt.to_period("M") == prev_month)]["Amount in INR"].sum()
    total_cost_curr = df_filtered[(df_filtered["Type"] == "Cost") & (df_filtered["Month"].dt.to_period("M") == curr_month)]["Amount in INR"].sum()

    summary = f"""
🔹 **Revenue moved from ₹{total_rev_prev:,.0f} to ₹{total_rev_curr:,.0f}**
🔹 **Cost moved from ₹{total_cost_prev:,.0f} to ₹{total_cost_curr:,.0f}**

Top cost contributors to margin drop (Month-on-Month):
"""
    top_cost_drivers = group_cost_diff.sort_values(ascending=False).head(5)
    for group, change in top_cost_drivers.items():
        summary += f"\n- {group}: +₹{change:,.0f}"

    return summary, top_drops.reset_index()

def run(user_input):
    import streamlit as st
    import re
    segment_match = re.search(r"(?:in|for)\s+([A-Za-z]+)", user_input, re.IGNORECASE)
    segment = segment_match.group(1) if segment_match else "Transportation"

    summary, table = analyze_margin_drop(segment)

    st.markdown(f"### Margin Drop Analysis for **{segment}** Segment")
    st.markdown(summary)
    if not table.empty:
        st.dataframe(table)
    else:
        st.error("No comparison data available for the latest 2 months.")
