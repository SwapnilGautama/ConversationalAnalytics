# question_q4.py (Updated for 'Amount in USD' and values in Million USD)

import pandas as pd
import matplotlib.pyplot as plt

def run(df, user_question=None):
    import streamlit as st

    df.columns = df.columns.str.strip()

    # ✅ Fix for 'Amount in USD'
    amount_col = None
    for col in df.columns:
        if col.strip().lower() in ['amount in usd', 'amountinusd', 'amount']:
            amount_col = col
            break
    if not amount_col:
        st.error("❌ Column not found: Amount in USD")
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
        'C&B (Million USD)': cb_monthly / 1e6,
        'Revenue (Million USD)': rev_monthly / 1e6
    }).dropna()

    df_summary['C&B % of Revenue'] = (df_summary['C&B (Million USD)'] / df_summary['Revenue (Million USD)']) * 100
    df_summary['MoM C&B Change (%)'] = df_summary['C&B (Million USD)'].pct_change() * 100
    df_summary['MoM Revenue Change (%)'] = df_summary['Revenue (Million USD)'].pct_change() * 100
    df_summary = df_summary.round(2)

    # ✅ Segment-level margin drop + C&B increase logic
    latest_month = df['Month'].max()
    prev_month = (latest_month - pd.DateOffset(months=1)).replace(day=1)

    df_latest = df[df['Month'].dt.to_period('M') == latest_month.to_period('M')]
    df_prev = df[df['Month'].dt.to_period('M') == prev_month.to_period('M')]

    def margin_calc(sub_df):
        rev = sub_df[sub_df['Type'].str.lower() == 'revenue'][amount_col].sum()
        cost = sub_df[sub_df['Type'].str.lower() == 'cost'][amount_col].sum()
        return ((rev - cost) / cost * 100) if cost else 0

    segment_insights = []
    segments = df['Segment'].dropna().unique()

    for seg in segments:
        margin_now = margin_calc(df_latest[df_latest['Segment'] == seg])
        margin_prev = margin_calc(df_prev[df_prev['Segment'] == seg])
        cb_now = df_cb[(df_cb['Segment'] == seg) & (df_cb['Month'].dt.to_period('M') == latest_month.to_period('M'))][amount_col].sum()
        cb_prev = df_cb[(df_cb['Segment'] == seg) & (df_cb['Month'].dt.to_period('M') == prev_month.to_period('M'))][amount_col].sum()

        if cb_now > cb_prev and margin_now < margin_prev:
            segment_insights.append(
                f"**{seg}**: Margin% dropped from {margin_prev:.1f}% to {margin_now:.1f}% and C&B rose from ${cb_prev/1e6:.1f}M to ${cb_now/1e6:.1f}M"
            )

    # ✅ Display insights
    st.markdown("### 📊 MoM Trend of C&B % of Revenue")

    if df_summary.shape[0] >= 2:
        last = df_summary.index[-1]
        prev = df_summary.index[-2]
        cb_chg = df_summary.loc[last, 'MoM C&B Change (%)']
        rev_chg = df_summary.loc[last, 'MoM Revenue Change (%)']
        st.markdown(
            f"📌 In **{last.strftime('%b %Y')}**, C&B cost changed by **{cb_chg:+.1f}%** while revenue changed by **{rev_chg:+.1f}%** vs **{prev.strftime('%b %Y')}**."
        )
        if segment_insights:
            st.markdown("🔍 Segments with margin drop and C&B increase:")
            for insight in segment_insights:
                st.markdown(f"- {insight}")

    # ✅ Table and chart side by side
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df_summary.reset_index(drop=False).rename(columns={'Month': 'Period'}), hide_index=True)

    with col2:
        fig, ax1 = plt.subplots(figsize=(6.5, 4))
        df_summary_plot = df_summary.copy()
        df_summary_plot.index = df_summary_plot.index.to_timestamp()

        bar_color = '#E7F3FF'
        line_color = '#FFB3BA'

        ax1.bar(df_summary_plot.index, df_summary_plot['Revenue (Million USD)'], width=20,
                color=bar_color, label='Revenue')
        ax1.set_ylabel("Revenue (Million USD)", color=bar_color)

        for spine in ax1.spines.values():
            spine.set_linewidth(0.5)
            spine.set_edgecolor('#cccccc')

        ax2 = ax1.twinx()
        ax2.plot(df_summary_plot.index, df_summary_plot['C&B % of Revenue'],
                 color=line_color, marker='o', label='C&B %')
        ax2.set_ylabel("C&B % of Revenue", color=line_color)

        for spine in ax2.spines.values():
            spine.set_linewidth(0.5)
            spine.set_edgecolor('#cccccc')

        ax1.set_title("MoM Revenue vs C&B % of Revenue")
        fig.tight_layout()
        st.pyplot(fig)
