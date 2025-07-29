import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re

def run(prompt):
    st.markdown("""
        <h2 style='color:#4F8BF9'>📊 MoM Revenue vs C&B % of Revenue</h2>
    """, unsafe_allow_html=True)

    # Extract segment from prompt
    segment_match = re.search(r"\b(?:in|for)?\s*(Transportation|Media & Technology|Plant Engineering|Industrial Products|Med Tech)\b", prompt, re.IGNORECASE)
    segment_filter = segment_match.group(1) if segment_match else None

    # ✅ Corrected file path
    df = pd.read_excel("sample_data/LnTPnL.xlsx", sheet_name="LnTPnL")  # Adjust sheet if needed

    # Clean columns
    df.columns = df.columns.str.strip()

    # Filter by segment if present
    if segment_filter and 'Segment' in df.columns:
        df['Segment'] = df['Segment'].fillna('').str.strip()
        df = df[df['Segment'].str.lower() == segment_filter.lower()]

    # Filter to C&B rows
    cb_df = df[df['Group4'] == 'C&B'].copy()

    # Parse date
    cb_df['Year'] = cb_df['Year'].astype(str)
    cb_df['Month'] = cb_df['Month'].astype(str).str.zfill(2)
    cb_df['Period'] = cb_df['Year'] + '-' + cb_df['Month']

    # Group by Period
    grouped_cb = cb_df.groupby('Period')['Amount in INR'].sum() / 1e6

    # Revenue (from full DF, grouped by period)
    revenue_df = df[df['Type'] == 'Revenue'].copy()
    revenue_df['Year'] = revenue_df['Year'].astype(str)
    revenue_df['Month'] = revenue_df['Month'].astype(str).str.zfill(2)
    revenue_df['Period'] = revenue_df['Year'] + '-' + revenue_df['Month']
    grouped_rev = revenue_df.groupby('Period')['Amount in INR'].sum() / 1e6

    # Align periods
    all_periods = sorted(set(grouped_cb.index).union(set(grouped_rev.index)))
    cb_cost = grouped_cb.reindex(all_periods, fill_value=0)
    revenue = grouped_rev.reindex(all_periods, fill_value=0)

    cb_pct = (cb_cost / revenue.replace(0, np.nan)) * 100
    cb_mom = cb_cost.pct_change() * 100
    rev_mom = revenue.pct_change() * 100

    # Prepare DataFrame
    result_df = pd.DataFrame({
        'Period': all_periods,
        'C&B (Million USD)': cb_cost.values,
        'Revenue (Million USD)': revenue.values,
        'C&B % of Revenue (%)': cb_pct.values,
        'MoM C&B Change (%)': cb_mom.values,
        'MoM Revenue Change (%)': rev_mom.values
    })

    # Drop rows with NaN revenue
    result_df.dropna(subset=['Revenue (Million USD)'], inplace=True)

    # Show insights
    if not result_df.empty:
        latest = result_df.iloc[-1]
        prev = result_df.iloc[-2] if len(result_df) > 1 else None

        if prev is not None:
            cb_change = latest['MoM C&B Change (%)']
            rev_change = latest['MoM Revenue Change (%)']
            period = latest['Period']
            prev_period = prev['Period']

            direction = "🔺" if cb_change > 0 else "🔻"
            st.markdown(f"<span style='color:#E63946'>{direction}</span> In <b>{period}</b>, C&B cost changed by <b>{cb_change:.1f}%</b> while revenue changed by <b>{rev_change:.1f}%</b> vs <b>{prev_period}</b>.", unsafe_allow_html=True)

    # Show table
    st.dataframe(result_df.round(2), use_container_width=True)

    # Plot
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
