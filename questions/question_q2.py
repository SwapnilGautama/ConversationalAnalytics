import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime


def run(pnl_df: pd.DataFrame, segment_filter: str = None):
    # ✅ Fix: Strip column names to remove trailing spaces before ANY column access
    pnl_df.columns = pnl_df.columns.str.strip()

    st.info(f"🔎 Running Q2 analysis for segment: **{segment_filter}**")

    # ✅ Basic validations
    required_cols = {'Month', 'Company_Code', 'Segment', 'Type', 'Amount in INR', 'Group1', 'Group2', 'Group3', 'Group4'}
    if not required_cols.issubset(set(pnl_df.columns)):
        missing = required_cols - set(pnl_df.columns)
        st.error(f"Missing required columns in LnTPnL.xlsx: {missing}")
        return

    # ✅ Convert month to datetime
    pnl_df['Month'] = pd.to_datetime(pnl_df['Month'], errors='coerce')

    # ✅ Filter only current and previous months
    latest_month = pnl_df['Month'].max()
    prev_month = (latest_month - pd.DateOffset(months=1)).replace(day=1)

    df = pnl_df.copy()

    # ✅ Optional segment filtering
    if segment_filter:
        df = df[df['Segment'].str.lower().str.contains(segment_filter.lower())]

    # ✅ Filter revenue and cost separately
    revenue_df = df[df['Type'].str.lower() == 'revenue']
    cost_df = df[df['Type'].str.lower() == 'cost']

    # ✅ Group cost by Company_Code, Month and group levels
    cost_grouped = (
        cost_df.groupby(['Company_Code', 'Month'])[['Amount in INR']]
        .sum()
        .reset_index()
        .rename(columns={'Amount in INR': 'Total_Cost'})
    )

    # ✅ Group revenue by Company_Code, Month
    revenue_grouped = (
        revenue_df.groupby(['Company_Code', 'Month'])[['Amount in INR']]
        .sum()
        .reset_index()
        .rename(columns={'Amount in INR': 'Revenue'})
    )

    # ✅ Merge cost and revenue
    merged = pd.merge(cost_grouped, revenue_grouped, on=['Company_Code', 'Month'], how='outer').fillna(0)

    # ✅ Pivot for current and previous month
    this_month_df = merged[merged['Month'] == latest_month].set_index('Company_Code')
    prev_month_df = merged[merged['Month'] == prev_month].set_index('Company_Code')

    combined = this_month_df.join(prev_month_df, lsuffix='_curr', rsuffix='_prev', how='outer').fillna(0)

    # ✅ Calculate Margin % for both months
    combined['Margin%_curr'] = ((combined['Revenue_curr'] - combined['Total_Cost_curr']) / combined['Total_Cost_curr'].replace(0, 1)) * 100
    combined['Margin%_prev'] = ((combined['Revenue_prev'] - combined['Total_Cost_prev']) / combined['Total_Cost_prev'].replace(0, 1)) * 100
    combined['Margin_Change'] = combined['Margin%_curr'] - combined['Margin%_prev']

    # ✅ Filter accounts where margin dropped and revenue didn't drop much
    margin_drop_df = combined[(combined['Margin_Change'] < -5) & ((combined['Revenue_curr'] - combined['Revenue_prev']) > -0.05 * combined['Revenue_prev'])]

    if margin_drop_df.empty:
        st.warning("No significant margin drop detected with relatively constant revenue.")
        return

    # ✅ Identify top contributors to cost increase
    group_cols = ['Group1', 'Group2', 'Group3', 'Group4']
    cost_trend = cost_df[cost_df['Company_Code'].isin(margin_drop_df.index)]

    summary_costs = (
        cost_trend[cost_trend['Month'].isin([latest_month, prev_month])]
        .groupby(['Company_Code', 'Month'] + group_cols)[['Amount in INR']]
        .sum()
        .reset_index()
    )

    # ✅ Create pivot to show changes
    pivot_costs = summary_costs.pivot_table(
        index=['Company_Code'] + group_cols,
        columns='Month',
        values='Amount in INR',
        fill_value=0
    ).reset_index()

    pivot_costs['Cost_Increase'] = pivot_costs[latest_month] - pivot_costs[prev_month]
    top_cost_increases = pivot_costs.sort_values('Cost_Increase', ascending=False).head(10)

    # ✅ Show summary table
    st.subheader("📊 Accounts with Margin Drop and Cost Increase")
    display_df = margin_drop_df[['Revenue_curr', 'Total_Cost_curr', 'Margin%_curr', 'Revenue_prev', 'Total_Cost_prev', 'Margin%_prev', 'Margin_Change']]
    st.dataframe(display_df.style.format("{:.2f}"))

    st.subheader("📌 Top Cost Groups Driving Margin Drop")
    st.dataframe(top_cost_increases.style.format("{:.2f}"))

    # ✅ Plotting
    fig, ax = plt.subplots(figsize=(10, 5))
    top_cost_increases.set_index('Company_Code')['Cost_Increase'].plot(kind='bar', ax=ax, color='salmon')
    ax.set_ylabel("Cost Increase (INR)")
    ax.set_title("Top Cost Increases by Client")
    st.pyplot(fig)

    st.success("✅ Q2 analysis complete.")
