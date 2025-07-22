import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime

def analyze_margin_drop(segment_input):
    # Load data
    file_path = "sample_data/LnTPnL.xlsx"
    df = pd.read_excel(file_path)

    # Clean and filter
    df["Month"] = pd.to_datetime(df["Month"])
    df["MonthStr"] = df["Month"].dt.strftime("%b-%Y")
    df = df[df["Segment"] == segment_input]

    # Ensure enough months
    latest_months = sorted(df["Month"].dt.to_period("M").unique())[-2:]
    if len(latest_months) < 2:
        return f"❗Not enough data for MoM comparison in segment: {segment_input}", pd.DataFrame()

    prev_month, curr_month = latest_months
    df_filtered = df[df["Month"].dt.to_period("M").isin([prev_month, curr_month])]

    # Aggregate by Month and Type
    summary_df = df_filtered.groupby(["MonthStr", "Type"])["Amount in INR"].sum().unstack().fillna(0)
    summary_df["Margin"] = summary_df["Revenue"] - summary_df["Cost"]
    summary_df["Margin %"] = (summary_df["Margin"] / summary_df["Cost"]) * 100

    # MoM movement summary
    if summary_df.shape[0] < 2:
        return "❗Insufficient data for margin comparison", pd.DataFrame()

    rev_diff = summary_df["Revenue"].iloc[1] - summary_df["Revenue"].iloc[0]
    cost_diff = summary_df["Cost"].iloc[1] - summary_df["Cost"].iloc[0]

    summary_text = f"""\
1. **Revenue Change (MoM)**: ₹{rev_diff:,.0f}
2. **Cost Change (MoM)**: ₹{cost_diff:,.0f}
"""

    # Detailed cost category comparison
    cost_fields = ["Group 1", "Group 2", "Group 3", "Group 4"]
    cost_df = df_filtered[df_filtered["Type"] == "Cost"]
    monthly_costs = cost_df.groupby(["MonthStr"])[cost_fields].sum()

    if monthly_costs.shape[0] < 2:
        return summary_text + "\n⚠️ Insufficient cost category data.", pd.DataFrame()

    delta = monthly_costs.iloc[1] - monthly_costs.iloc[0]
    delta_sorted = delta.sort_values(ascending=False)

    top_contributors = delta_sorted.head(4)
    insights = "\n3. **Top Increasing Cost Categories:**\n" + "\n".join([
        f"   - {idx}: ₹{val:,.0f}" for idx, val in top_contributors.items() if val > 0
    ])

    final_summary = summary_text + insights

    # Prepare comparison table
    comparison_df = monthly_costs.copy()
    comparison_df.loc["Change"] = delta

    return final_summary, comparison_df

# ✅ Streamlit run wrapper
def run(user_input):
    import streamlit as st
    import re

    user_input = str(user_input)
    segment_match = re.search(r"(?:in|for)\s+([A-Za-z]+)", user_input, re.IGNORECASE)
    segment = segment_match.group(1) if segment_match else "Transportation"

    st.markdown(f"### Margin Drop Analysis for **{segment}** Segment")

    summary, table = analyze_margin_drop(segment)

    if isinstance(summary, str):
        st.markdown(summary)
    else:
        st.warning("⚠️ Could not generate summary.")

    if isinstance(table, pd.DataFrame) and not table.empty:
        st.dataframe(table)
    else:
        st.info("ℹ️ No data available for table view.")
