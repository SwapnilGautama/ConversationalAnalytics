# question_q4.py

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run(df, user_question=None):
    # Filter for only C&B cost rows
    df_cb = df[df['Group3'] == 'C&B']
    df_cb = df_cb[df_cb['Type'] == 'Cost']

    # Calculate C&B cost and Revenue by Segment and Month
    cb_by_month = df_cb.groupby(['Month'])['Amount in INR'].sum().reset_index()
    cb_by_month.rename(columns={'Amount in INR': 'C&B Cost'}, inplace=True)

    df_rev = df[df['Type'] == 'Revenue']
    rev_by_month = df_rev.groupby(['Month'])['Amount in INR'].sum().reset_index()
    rev_by_month.rename(columns={'Amount in INR': 'Revenue'}, inplace=True)

    # Merge and calculate % C&B of Revenue
    merged = pd.merge(cb_by_month, rev_by_month, on='Month')
    merged['C&B as % of Revenue'] = (merged['C&B Cost'] / merged['Revenue']) * 100

    # Sort months chronologically
    merged['Month'] = pd.to_datetime(merged['Month'], format='%b %Y')
    merged.sort_values('Month', inplace=True)
    merged['Month'] = merged['Month'].dt.strftime('%b %Y')

    # Calculate MoM % change for C&B cost and Revenue
    merged['C&B MoM % Change'] = merged['C&B Cost'].pct_change() * 100
    merged['Revenue MoM % Change'] = merged['Revenue'].pct_change() * 100

    # Prepare summary
    latest_row = merged.iloc[-1]
    prev_row = merged.iloc[-2]

    insight_1 = f"1️⃣ **C&B cost** increased by {latest_row['C&B MoM % Change']:.1f}% from {prev_row['Month']} to {latest_row['Month']}."
    insight_2 = f"2️⃣ **Revenue** changed by {latest_row['Revenue MoM % Change']:.1f}% in the same period."
    insight_3 = f"3️⃣ **C&B as % of Revenue** is {latest_row['C&B as % of Revenue']:.2f}% in {latest_row['Month']}."

    st.markdown("### 🧾 Key Insights")
    st.markdown(insight_1)
    st.markdown(insight_2)
    st.markdown(insight_3)

    # Plot C&B and Revenue trends
    st.markdown("### 📉 MoM Trend of C&B vs Revenue")

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()

    ax1.bar(merged['Month'], merged['C&B Cost'] / 1e7, label='C&B Cost (Cr)', color='orange')
    ax2.plot(merged['Month'], merged['Revenue'] / 1e7, label='Revenue (Cr)', color='blue', marker='o')

    ax1.set_ylabel('C&B Cost (Cr)', color='orange')
    ax2.set_ylabel('Revenue (Cr)', color='blue')
    ax1.set_xlabel('Month')
    ax1.tick_params(axis='x', rotation=45)

    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.85))
    st.pyplot(fig)

    return merged[['Month', 'C&B Cost', 'Revenue', 'C&B as % of Revenue']].round(2)
