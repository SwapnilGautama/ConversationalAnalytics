import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re

def run(prompt):
    st.markdown("""
        <h2 style='color:#4F8BF9'>📊 MoM Revenue vs C&B % of Revenue</h2>
    """, unsafe_allow_html=True)

    # Extract segment from prompt if mentioned
    segment_match = re.search(r"\b(?:in|for)?\s*(Transportation|Media & Technology|Plant Engineering|Industrial Products|Med Tech)\b", prompt, re.IGNORECASE)
    segment_filter = segment_match.group(1) if segment_match else None

    # Load data
    df = pd.read_excel("LNTDataSample.xlsx", sheet_name="LNTDataSample")

    # Filter segment if provided
    if segment_filter:
        df = df[df['Segment'].fillna('').str.lower() == segment_filter.lower()]

    # Filter to C&B only
    cb_df = df[df['Group4'] == 'C&B']
    cb_df = cb_df.copy()

    # Preprocess
    cb_df['Year'] = cb_df['Year'].astype(str)
    cb_df['Month'] = cb_df['Month'].astype(str).str.zfill(2)
    cb_df['Period'] = cb_df['Year'] + '-' + cb_df['Month']

    # Aggregate
    grouped = cb_df.groupby('Period')
    cb_cost = grouped['Amount in INR'].sum() / 1e6
    revenue = grouped[df['Type'] == 'Revenue']['Amount in INR'].sum() / 1e6

    cb_pct = (cb_cost / revenue) * 100
    cb_mom = cb_cost.pct_change() * 100
    rev_mom = revenue.pct_change() * 100

    result_df = pd.DataFrame({
        'C&B (Million USD)': cb_cost,
        'Revenue (Million USD)': revenue,
        'C&B % of Revenue (%)': cb_pct,
        'MoM C&B Change (%)': cb_mom,
        'MoM Revenue Change (%)': rev_mom
    })

    result_df.index.name = 'Period'
    result_df.reset_index(inplace=True)

    # Highlight MoM insights
    latest = result_df.dropna().iloc[-1]
    cb_change = latest['MoM C&B Change (%)']
    rev_change = latest['MoM Revenue Change (%)']
    period = latest['Period']
    direction = "🔺" if cb_change > 0 else "🔻"
    st.markdown(f"<span style='color:#E63946'>{direction}</span> In <b>{period}</b>, C&B cost changed by <b>{cb_change:.1f}%</b> while revenue changed by <b>{rev_change:.1f}%</b> vs <b>{result_df.iloc[-2]['Period']}</b>.", unsafe_allow_html=True)

    # Show table
    st.dataframe(result_df.round(2), use_container_width=True)

    # Chart
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()
    ax1.bar(result_df['Period'], result_df['C&B % of Revenue (%)'], color='lightyellow', label='C&B % of Revenue')
    ax2.plot(result_df['Period'], result_df['Revenue (Million USD)'], color='skyblue', marker='o', label='Revenue')

    ax1.set_ylabel('C&B % of Revenue')
    ax2.set_ylabel('Revenue (Million USD)')
    ax1.set_xticklabels(result_df['Period'], rotation=45)
    ax1.grid(False)
    ax2.grid(False)
    st.pyplot(fig)
