# question_q4.py

import pandas as pd
import matplotlib.pyplot as plt

def run(df, user_question=None):
    import streamlit as st

    # Standardize columns
    df.columns = df.columns.str.strip()

    # ✅ Fix for 'Amount in INR'
    amount_col = None
    for col in df.columns:
        if col.strip().lower() in ['amount in inr', 'amountinr', 'amount']:
            amount_col = col
            break

    if not amount_col:
        st.error("❌ Column not found: Amount in INR")
        return

    # ✅ Ensure Month is datetime
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])

    # ✅ Filter C&B and Revenue
    df_cb = df[df['Group3'].str.contains('C&B', na=False)]
    df_rev = df[df['Type'].str.lower() == 'revenue']

    # ✅ Monthly aggregation
    cb_monthly = df_cb.groupby(df_cb['Month'].dt.to_period('M'))[amount_col].sum()
    rev_monthly = df_rev.groupby(df_rev['Month'].dt.to_period('M'))[amount_col].sum()

    df_summary = pd.DataFrame({
        'C&B (INR Cr)': cb_monthly / 1e7,
        'Revenue (INR Cr)': rev_monthly / 1e7
    }).dropna()

    df_summary['C&B % of Revenue'] = (df_summary['C&B (INR Cr)'] / df_summary['Revenue (INR Cr)']) * 100

    # ✅ MoM Changes
    df_summary['MoM C&B Change (%)'] = df_summary['C&B (INR Cr)'].pct_change() * 100
    df_summary['MoM Revenue Change (%)'] = df_summary['Revenue (INR Cr)'].pct_change() * 100

    df_summary = df_summary.round(2)

    # ✅ Display table
    st.markdown("### 📊 MoM Trend of C&B % of Revenue")
    st.dataframe(df_summary.reset_index().rename(columns={'Month': 'Period'}))

    # ✅ Text insights
    if df_summary.shape[0] >= 2:
        last_month = df_summary.index[-1]
        prev_month = df_summary.index[-2]
        cb_change = df_summary.loc[last_month, 'MoM C&B Change (%)']
        rev_change = df_summary.loc[last_month, 'MoM Revenue Change (%)']
        st.markdown(f"📌 In {last_month.strftime('%b %Y')}, C&B cost changed by **{cb_change:+.1f}%** while revenue changed by **{rev_change:+.1f}%** compared to {prev_month.strftime('%b %Y')}.")

    # ✅ Dual Axis Chart
    fig, ax1 = plt.subplots(figsize=(10, 5))

    df_summary_plot = df_summary.copy()
    df_summary_plot.index = df_summary_plot.index.to_timestamp()

    ax1.bar(df_summary_plot.index, df_summary_plot['Revenue (INR Cr)'], color='lightgreen', label='Revenue (INR Cr)')
    ax1.set_ylabel("Revenue (INR Cr)", color='green')

    ax2 = ax1.twinx()
    ax2.plot(df_summary_plot.index, df_summary_plot['C&B % of Revenue'], color='blue', marker='o', label='C&B % of Revenue')
    ax2.set_ylabel("C&B % of Revenue", color='blue')

    ax1.set_title("MoM Revenue vs C&B % of Revenue")
    fig.tight_layout()
    st.pyplot(fig)
