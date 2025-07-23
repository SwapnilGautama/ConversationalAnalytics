# question_q2.py

import pandas as pd
import matplotlib.pyplot as plt

def run(df, user_question=None):
    import streamlit as st

    # Ensure consistent column names
    df.columns = df.columns.str.strip()
    
    # Extract latest 2 months
    latest_month = df['Month'].max()
    prev_month = (latest_month - pd.DateOffset(months=1)).replace(day=1)

    # Segment filter from user input or default
    segment = "Transportation"
    if user_question:
        for seg in df['Segment'].dropna().unique():
            if seg.lower() in user_question.lower():
                segment = seg
                break

    df = df[df['Segment'] == segment]

    # Split revenue and cost
    revenue_df = df[df['Type'] == 'Revenue']
    cost_df = df[df['Type'] == 'Cost']

    # Group by Client + Month for Margin calculation
    revenue_m = revenue_df.groupby(['Client', 'Month'])['Amount'].sum().unstack(fill_value=0)
    cost_m = cost_df.groupby(['Client', 'Month'])['Amount'].sum().unstack(fill_value=0)
    margin_m = (revenue_m - cost_m) / cost_m.replace(0, 1) * 100

    # Segment-level margin %
    seg_rev = revenue_df.groupby('Month')['Amount'].sum()
    seg_cost = cost_df.groupby('Month')['Amount'].sum()
    seg_margin_pct = ((seg_rev - seg_cost) / seg_cost.replace(0, 1)) * 100

    # Margin movement summary
    try:
        margin_change = seg_margin_pct[latest_month] - seg_margin_pct[prev_month]
        margin_summary = f"{segment} margin {'increased' if margin_change > 0 else 'reduced'} {abs(margin_change):.1f}% from {prev_month.strftime('%b')} to {latest_month.strftime('%b')}, down from {seg_margin_pct[prev_month]:.1f}% to {seg_margin_pct[latest_month]:.1f}%."
    except:
        margin_summary = "Margin movement data unavailable."

    # Client count movement
    client_margin_prev = ((revenue_m[prev_month] - cost_m[prev_month]) / cost_m[prev_month].replace(0, 1)) * 100
    client_margin_latest = ((revenue_m[latest_month] - cost_m[latest_month]) / cost_m[latest_month].replace(0, 1)) * 100
    client_movement = (client_margin_latest < client_margin_prev).sum()
    total_clients = len(client_margin_prev)
    client_summary = f"{client_movement} out of {total_clients} clients ({(client_movement/total_clients)*100:.1f}%) in {segment} saw a drop in margin."

    # Total cost growth
    cost_prev = seg_cost.get(prev_month, 0)
    cost_latest = seg_cost.get(latest_month, 0)
    cost_growth = ((cost_latest - cost_prev) / cost_prev) * 100 if cost_prev else 0
    cost_summary = f"{segment} cost {'increased' if cost_growth > 0 else 'decreased'} by {abs(cost_growth):.1f}% from {prev_month.strftime('%b')} to {latest_month.strftime('%b')}."

    # Insights summary
    st.markdown("### 🔍 Key Insights")
    st.markdown(f"- 📉 {margin_summary}")
    st.markdown(f"- 👥 {client_summary}")
    st.markdown(f"- 💸 {cost_summary}")

    # Group4 Cost Analysis
    group4_df = cost_df[['Month', 'Client', 'Amount', 'Group4']].copy()
    group4_df = group4_df.dropna(subset=['Group4'])

    g4 = group4_df.groupby(['Group4', 'Month'])['Amount'].sum().unstack(fill_value=0)
    g4 = g4[[prev_month, latest_month]] if prev_month in g4.columns and latest_month in g4.columns else g4
    g4['% Change'] = ((g4[latest_month] - g4[prev_month]) / g4[prev_month].replace(0, 1)) * 100

    # Format to INR Cr
    g4[prev_month] = g4[prev_month] / 1e7
    g4[latest_month] = g4[latest_month] / 1e7
    g4 = g4.rename(columns={prev_month: f"{prev_month.strftime('%b')}", latest_month: f"{latest_month.strftime('%b')}"})

    top8 = g4.sort_values(by='% Change', ascending=False).head(8).reset_index()

    st.markdown("### 📊 Top 8 Group4 Cost Increases")
    st.dataframe(top8)

    return None
