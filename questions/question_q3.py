# question_q3.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import numpy as np
import re

def run(df, user_question=None):
    import streamlit as st

    # --- Standardize column names ---
    df.columns = df.columns.str.strip()

    # --- Identify amount column ---
    amount_col = next((col for col in df.columns if col.lower() in ['amount in usd', 'amountinusd', 'amount', 'amount in inr']), None)
    if not amount_col:
        st.error("❌ Column not found: Amount")
        return

    # --- Extract segment from prompt ---
    selected_segment = None
    if user_question:
        match = re.search(r'\b(transportation|manufacturing|retail|energy|healthcare|defense|telecom)\b', user_question, re.IGNORECASE)
        if match:
            selected_segment = match.group(1).capitalize()
            st.markdown(f"🔍 Filtering data for segment: **{selected_segment}**")

    # --- Filter by segment if provided ---
    if selected_segment:
        df = df[df['Segment'].str.lower() == selected_segment.lower()]
        if df.empty:
            st.warning(f"No data found for segment: {selected_segment}")
            return

    # --- Clean and convert Month ---
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])
    df['Quarter'] = df['Month'].dt.to_period('Q')

    # --- Get quarters ---
    latest_month = df['Month'].max()
    latest_q = latest_month.to_period('Q')
    prev_q = (latest_month - pd.DateOffset(months=3)).to_period('Q')

    # --- Split groups ---
    df_cb = df[df['Group3'].str.contains('C&B', na=False)]
    df_cost = df[df['Type'].str.lower() == 'cost']
    df_rev = df[df['Type'].str.lower() == 'revenue']

    # --- Aggregation ---
    cb_summary = df_cb.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)
    cost_summary = df_cost.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)
    rev_summary = df_rev.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)

    # --- Ensure both quarters exist ---
    for q in [prev_q, latest_q]:
        for summary in [cb_summary, cost_summary, rev_summary]:
            if q not in summary.columns:
                summary[q] = 0

    cb_summary = cb_summary[[prev_q, latest_q]] / 1e6
    cost_summary = cost_summary[[prev_q, latest_q]] / 1e6
    rev_summary = rev_summary[[prev_q, latest_q]] / 1e6

    # --- Header insights ---
    total_q1_cb = cb_summary[prev_q].sum()
    total_q2_cb = cb_summary[latest_q].sum()
    cb_change = ((total_q2_cb - total_q1_cb) / total_q1_cb) * 100 if total_q1_cb else 0

    total_q1_rev = rev_summary[prev_q].sum()
    total_q2_rev = rev_summary[latest_q].sum()
    rev_change = ((total_q2_rev - total_q1_rev) / total_q1_rev) * 100 if total_q1_rev else 0

    increased_segments = cb_summary[cb_summary[latest_q] > cb_summary[prev_q]].index.tolist()

    st.markdown("### 📊 C&B Cost Insights")
    st.markdown(f"- 💰 **Overall C&B change** from {prev_q} to {latest_q}: **{cb_change:+.1f}%**")
    st.markdown(f"- ✅ **Overall Revenue change** from {prev_q} to {latest_q}: **{rev_change:+.1f}%**")
    if increased_segments:
        st.markdown(f"- 📈 **Segments with increased C&B**: {', '.join(increased_segments)}")

    # --- Table ---
    merged = pd.DataFrame(index=cb_summary.index)
    merged['C&B Q1'] = cb_summary[prev_q]
    merged['C&B Q2'] = cb_summary[latest_q]
    merged['Total Cost Q1'] = cost_summary[prev_q]
    merged['Total Cost Q2'] = cost_summary[latest_q]
    merged['Revenue Q1'] = rev_summary[prev_q]
    merged['Revenue Q2'] = rev_summary[latest_q]
    merged['% C&B Change'] = ((merged['C&B Q2'] - merged['C&B Q1']) / merged['C&B Q1'].replace(0, 1)) * 100
    merged['% Rev Change'] = ((merged['Revenue Q2'] - merged['Revenue Q1']) / merged['Revenue Q1'].replace(0, 1)) * 100
    merged['C&B vs Revenue Growth (pp)'] = merged['% C&B Change'] - merged['% Rev Change']

    # --- Total Row ---
    total_row = merged.sum(numeric_only=True)
    total_row.name = 'Total'
    merged = pd.concat([merged, total_row.to_frame().T])

    # --- Format ---
    def fmt(x): return f"{x:,.1f}"
    def fmt_pct(x): return f"{x:.2f}%" if pd.notnull(x) else "—"
    styled = merged.copy()
    styled[['C&B Q1', 'C&B Q2', 'Total Cost Q1', 'Total Cost Q2', 'Revenue Q1', 'Revenue Q2']] = \
        styled[['C&B Q1', 'C&B Q2', 'Total Cost Q1', 'Total Cost Q2', 'Revenue Q1', 'Revenue Q2']].applymap(fmt)
    styled[['% C&B Change', '% Rev Change', 'C&B vs Revenue Growth (pp)']] = \
        styled[['% C&B Change', '% Rev Change', 'C&B vs Revenue Growth (pp)']].applymap(fmt_pct)

    def highlight_mismatch(val):
        try:
            return 'background-color: #ffe6e6' if float(val.strip('%')) > 0 else ''
        except:
            return ''

    st.markdown("#### 🧾 C&B vs Revenue Comparison by Segment")
    st.dataframe(
        styled.style
            .applymap(highlight_mismatch, subset=['C&B vs Revenue Growth (pp)'])
            .set_properties(**{'white-space': 'normal', 'text-align': 'left'})
            .set_table_styles([{'selector': 'th', 'props': [('text-align', 'left')]}])
    )

    # --- Charts ---
    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        bar_data = ((cb_summary[latest_q] - cb_summary[prev_q]) / cb_summary[prev_q].replace(0, 1)) * 100
        bar_data = bar_data.sort_values()
        norm = mcolors.TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100)
        colors = [cm.Reds(norm(val)) if val < 0 else cm.Greens(norm(val)) for val in bar_data]
        bar_data.plot(kind='barh', ax=ax1, color=colors)
        for spine in ax1.spines.values():
            spine.set_linewidth(0.5)
            spine.set_edgecolor('#cccccc')
        ax1.set_xlabel('% Change in C&B Cost')
        ax1.set_title(f'C&B Change by Segment: {prev_q} vs {latest_q}')
        ax1.set_xlim(-100, 100)
        st.pyplot(fig1)

    with col2:
        cb_ratio_q1 = (cb_summary[prev_q] / rev_summary[prev_q].replace(0, np.nan)) * 100
        cb_ratio_q2 = (cb_summary[latest_q] / rev_summary[latest_q].replace(0, np.nan)) * 100
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        index = cb_ratio_q1.index
        bar_width = 0.35
        x = np.arange(len(index))
        ax2.bar(x - bar_width / 2, cb_ratio_q1, width=bar_width, label=str(prev_q), color='#a8dadc', edgecolor='#ccc')
        ax2.bar(x + bar_width / 2, cb_ratio_q2, width=bar_width, label=str(latest_q), color='#fff9b0', edgecolor='#ccc')
        ax2.set_xticks(x)
        ax2.set_xticklabels(index, rotation=45, ha='right')
        ax2.set_ylabel('C&B / Revenue (%)')
        ax2.set_title('Quarterly C&B as % of Revenue')
        ax2.legend()
        for spine in ax2.spines.values():
            spine.set_linewidth(0.5)
            spine.set_edgecolor('#cccccc')
        st.pyplot(fig2)
