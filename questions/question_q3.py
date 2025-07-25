# question_q3.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm

def run(df, user_question=None):
    import streamlit as st
    import streamlit.components.v1 as components

    df.columns = df.columns.str.strip()

    # Identify amount column
    amount_col = None
    for col in df.columns:
        if col.strip().lower() in ['amount in usd', 'amountinusd', 'amount']:
            amount_col = col
            break
    if not amount_col:
        st.error("❌ Column not found: Amount in USD")
        return

    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])
    df['Quarter'] = df['Month'].dt.to_period('Q')

    latest_month = df['Month'].max()
    latest_q = latest_month.to_period('Q')
    prev_q = (latest_month - pd.DateOffset(months=3)).to_period('Q')

    # C&B and Revenue summaries
    df_cb = df[df['Group3'].str.contains('C&B', na=False)]
    df_rev = df[df['Type'].str.lower() == 'revenue']

    cb_summary = df_cb.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)
    rev_summary = df_rev.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)

    for q in [prev_q, latest_q]:
        if q not in cb_summary.columns:
            cb_summary[q] = 0
        if q not in rev_summary.columns:
            rev_summary[q] = 0

    cb_summary = cb_summary[[prev_q, latest_q]] / 1e6
    rev_summary = rev_summary[[prev_q, latest_q]] / 1e6

    total_q1_cb, total_q2_cb = cb_summary[prev_q].sum(), cb_summary[latest_q].sum()
    total_q1_rev, total_q2_rev = rev_summary[prev_q].sum(), rev_summary[latest_q].sum()

    cb_change = ((total_q2_cb - total_q1_cb) / total_q1_cb) * 100 if total_q1_cb else 0
    rev_change = ((total_q2_rev - total_q1_rev) / total_q1_rev) * 100 if total_q1_rev else 0

    increased_segments = cb_summary[cb_summary[latest_q] > cb_summary[prev_q]].index.tolist()

    # Header Insights
    st.markdown("### 📊 C&B Cost Insights")
    st.markdown(f"- 💰 **Overall C&B change** from {prev_q} to {latest_q}: **{cb_change:+.1f}%**")
    st.markdown(f"- ✅ **Overall Revenue change** from {prev_q} to {latest_q}: **{rev_change:+.1f}%**")
    if increased_segments:
        st.markdown(f"- 📈 **Segments with increased C&B**: {', '.join(increased_segments)}")

    # Merge and calculate growth
    merged = cb_summary.merge(rev_summary, left_index=True, right_index=True, suffixes=(' C&B', ' Revenue'))
    merged['% C&B Change'] = ((merged[f'{latest_q} C&B'] - merged[f'{prev_q} C&B']) / merged[f'{prev_q} C&B'].replace(0, 1)) * 100
    merged['% Rev Change'] = ((merged[f'{latest_q} Revenue'] - merged[f'{prev_q} Revenue']) / merged[f'{prev_q} Revenue'].replace(0, 1)) * 100
    merged['C&B vs Rev Growth (pp)'] = merged['% C&B Change'] - merged['% Rev Change']

    # Reorder and rename
    display_df = merged[[f'{prev_q} C&B', f'{latest_q} C&B', f'{prev_q} Revenue', f'{latest_q} Revenue',
                         '% C&B Change', '% Rev Change', 'C&B vs Rev Growth (pp)']].copy()
    display_df.columns = ['C&B Q1 (Mn USD)', 'C&B Q2 (Mn USD)', 'Revenue Q1 (Mn USD)', 'Revenue Q2 (Mn USD)',
                          '% C&B Change', '% Revenue Change', 'C&B Growth vs Revenue Growth (pp)']

    # Add total row
    total_row = display_df.drop(columns=['% C&B Change', '% Revenue Change', 'C&B Growth vs Revenue Growth (pp)']).astype(float).sum()
    total_row['% C&B Change'] = ((total_row['C&B Q2 (Mn USD)'] - total_row['C&B Q1 (Mn USD)']) / (total_row['C&B Q1 (Mn USD)'] or 1)) * 100
    total_row['% Revenue Change'] = ((total_row['Revenue Q2 (Mn USD)'] - total_row['Revenue Q1 (Mn USD)']) / (total_row['Revenue Q1 (Mn USD)'] or 1)) * 100
    total_row['C&B Growth vs Revenue Growth (pp)'] = total_row['% C&B Change'] - total_row['% Revenue Change']
    total_row.name = 'Total'
    display_df = pd.concat([display_df, pd.DataFrame([total_row])])

    # Format numeric values
    numeric_cols = ['C&B Q1 (Mn USD)', 'C&B Q2 (Mn USD)', 'Revenue Q1 (Mn USD)', 'Revenue Q2 (Mn USD)']
    for col in numeric_cols:
        display_df[col] = display_df[col].astype(float).map(lambda x: f"{x:,.1f}" if pd.notnull(x) else "—")

    for col in ['% C&B Change', '% Revenue Change']:
        display_df[col] = display_df[col].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "—")

    # Conditional formatting: highlight C&B > Revenue growth
    def highlight_growth(val):
        try:
            v = float(str(val).replace('%', ''))
            if v > 0:
                return 'background-color: #ffc2c2'  # light red
        except:
            pass
        return ''

    styled_table = display_df.style.set_table_styles([
        {'selector': 'th', 'props': [('white-space', 'normal'), ('word-wrap', 'break-word'), ('font-size', '12px')]}
    ]).applymap(highlight_growth, subset=['C&B Growth vs Revenue Growth (pp)'])

    # Layout
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("#### 🧾 C&B vs Revenue Comparison by Segment")
        st.dataframe(styled_table, use_container_width=True, height=500)

    with col2:
        # Horizontal bar for % C&B Change
        bar_data = ((cb_summary[latest_q] - cb_summary[prev_q]) / cb_summary[prev_q].replace(0, 1)) * 100
        bar_data = bar_data.sort_values()
        fig, ax = plt.subplots(figsize=(6, 6))
        norm = mcolors.TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100)
        colors = [cm.Reds(norm(val)) if val < 0 else cm.Greens(norm(val)) for val in bar_data]
        bar_data.plot(kind='barh', ax=ax, color=colors)
        ax.set_xlabel('% Change in C&B Cost')
        ax.set_title(f'C&B Change by Segment: {prev_q} vs {latest_q}')
        st.pyplot(fig)

    # Optional stacked bar: C&B and Revenue absolute values
    st.markdown("#### 📊 Revenue vs C&B Cost by Segment (Mn USD)")
    abs_chart_data = merged[[f'{prev_q} C&B', f'{latest_q} C&B', f'{prev_q} Revenue', f'{latest_q} Revenue']]
    abs_chart_data.columns = ['C&B Q1', 'C&B Q2', 'Revenue Q1', 'Revenue Q2']
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    abs_chart_data[['C&B Q2', 'Revenue Q2']].plot(kind='bar', stacked=True, ax=ax2)
    ax2.set_title(f'C&B vs Revenue (Q2 {latest_q})')
    ax2.set_ylabel('Million USD')
    st.pyplot(fig2)
