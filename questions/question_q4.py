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

    # ✅ Monthly aggregation (Total)
    cb_monthly = df_cb.groupby(df_cb['Month'].dt.to_period('M'))[amount_col].sum()
    rev_monthly = df_rev.groupby(df_rev['Month'].dt.to_period('M'))[amount_col].sum()

    df_summary = pd.DataFrame({
        'C&B (INR Cr)': cb_monthly / 1e7,
        'Revenue (INR Cr)': rev_monthly / 1e7
    }).dropna()

    df_summary['C&B % of Revenue'] = (df_summary['C&B (INR Cr)'] / df_summary['Revenue (INR Cr)']) * 100
    df_summary['MoM C&B Change (%)'] = df_summary['C&B (INR Cr)'].pct_change() * 100
    df_summary['MoM Revenue Change (%)'] = df_summary['Revenue (INR Cr)'].pct_change() * 100
    df_summary = df_summary.round(2)

    # ✅ Segment-level analysis for margin drop vs C&B increase
    latest_month = df['Month'].max()
    prev_month = (latest_month - pd.DateOffset(months=1)).replace(day=1)

    df_latest = df[df['Month'].dt.to_period('M') == latest_month.to_period('M')]
    df_prev = df[df['Month'].dt.to_period('M') == prev_month.to_period('M')]

    def margin_calc(sub_df):
        rev = sub_df[sub_df['Type'].str.lower() == 'revenue'][amount_col].sum()
        cost = sub_df[sub_df['Type'].str.lower() == 'cost'][amount_col].sum()
        return ((rev - cost) / cost * 100) if cost else 0

    segment_margin_change = []
    segments = df['Segment'].dropna().unique()
    for seg in segments:
        cb_now = df_cb[(df_cb['Segment'] == seg) & (df_cb['Month'].dt.to_period('M') == latest_month.to_period('M'))][amount_col].sum()
        cb_before = df_cb[(df_cb['Segment'] == seg) & (df_cb['Month'].dt.to_period('M') == prev_month.to_period('M'))][amount_col].sum()
        margin_now = margin_calc(df_latest[df_latest['Segment'] == seg])
        margin_before = margin_calc(df_prev[df_prev['Segment'] == seg])
        if cb_now > cb_before and margin_now < margin_before:
            segment_margin_change.append((seg, round(margin_before,1), round(margin_now,1)))

    # ✅ Display text insights
    st.markdown("### 📊 MoM Trend of C&B % of Revenue")
    if df_summary.shape[0] >= 2:
        last = df_summary.index[-1]
        prev = df_summary.index[-2]
        cb_chg = df_summary.loc[last, 'MoM C&B Change (%)']
        rev_chg = df_summary.loc[last, 'MoM Revenue Change (%)']
        st.markdown(
            f"📌 In **{last.strftime('%b %Y')}**, C&B cost changed by **{cb_chg:+.1f}%** while revenue changed by **{rev_chg:+.1f}%** vs **{prev.strftime('%b %Y')}**."
        )
        if segment_margin_change:
            list_text = ", ".join([f"**{seg}** (↓ from {b}% to {a}%)" for seg, b, a in segment_margin_change])
            st.markdown(f"🔻 Segments where **margin % dropped** despite increase in C&B: {list_text}")

    # ✅ Display table and chart side by side
    col1, col2 = st.columns([1, 1])

    with col1:
        st.dataframe(df_summary.reset_index().rename(columns={'Month': 'Period'}))

    with col2:
        fig, ax1 = plt.subplots(figsize=(6, 4))
        df_summary_plot = df_summary.copy()
        df_summary_plot.index = df_summary_plot.index.to_timestamp()

        ax1.bar(df_summary_plot.index, df_summary_plot['Revenue (INR Cr)'], color='lightgreen', label='Revenue')
        ax1.set_ylabel("Revenue (INR Cr)", color='green')

        ax2 = ax1.twinx()
        ax2.plot(df_summary_plot.index, df_summary_plot['C&B % of Revenue'], color='blue', marker='o', label='C&B %')
        ax2.set_ylabel("C&B % of Revenue", color='blue')

        ax1.set_title("MoM Revenue vs C&B % of Revenue")
        fig.tight_layout()
        st.pyplot(fig)
