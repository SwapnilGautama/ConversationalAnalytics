# question_q3.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm

def run(df, user_question=None):
    import streamlit as st

    # Standardize column names
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

    # Convert Month and get Quarters
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])
    df['Quarter'] = df['Month'].dt.to_period('Q')

    latest_month = df['Month'].max()
    latest_q = latest_month.to_period('Q')
    prev_q = (latest_month - pd.DateOffset(months=3)).to_period('Q')

    # C&B Data
    df_cb = df[df['Group3'].str.contains('C&B', na=False)]
    cb_summary = df_cb.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)

    # Revenue Data
    df_rev = df[df['Type'].str.lower() == 'revenue']
    rev_summary = df_rev.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)

    # Ensure both quarters exist
    for q in [prev_q, latest_q]:
        if q not in cb_summary.columns:
            cb_summary[q] = 0
        if q not in rev_summary.columns:
            rev_summary[q] = 0

    cb_summary = cb_summary[[prev_q, latest_q]] / 1e6
    rev_summary = rev_summary[[prev_q, latest_q]] / 1e6

    # Compute summary metrics
    total_q1_cb = cb_summary[prev_q].sum()
    total_q2_cb = cb_summary[latest_q].sum()
    cb_change = ((total_q2_cb - total_q1_cb) / total_q1_cb) * 100 if total_q1_cb else 0

    total_q1_rev = rev_summary[prev_q].sum()
    total_q2_rev = rev_summary[latest_q].sum()
    rev_change = ((total_q2_rev - total_q1_rev) / total_q1_rev) * 100 if total_q1_rev else 0

    increased_segments = cb_summary[cb_summary[latest_q] > cb_summary[prev_q]].index.tolist()

    # Display Insights
    st.markdown("### 📊 C&B Cost Insights")
    st.markdown(f"- 💰 **Overall C&B change** from {prev_q} to {latest_q}: **{cb_change:+.1f}%**")
    st.markdown(f"- ✅ **Overall Revenue change** from {prev_q} to {latest_q}: **{rev_change:+.1f}%**")
    if increased_segments:
        st.markdown(f"- 📈 **Segments with increased C&B**: {', '.join(increased_segments)}")
    else:
        st.markdown("- ✅ No segments recorded an increase in C&B.")

    # Prepare Table
    cb_df = cb_summary.copy()
    rev_df = rev_summary.copy()

    merged = cb_df.merge(rev_df, left_index=True, right_index=True, suffixes=(' C&B', ' Revenue'))

    merged['% C&B Change'] = ((cb_df[latest_q] - cb_df[prev_q]) / cb_df[prev_q].replace(0, 1)) * 100
    merged['% Rev Change'] = ((rev_df[latest_q] - rev_df[prev_q]) / rev_df[prev_q].replace(0, 1)) * 100
    merged['C&B vs Rev Growth (pp)'] = merged['% C&B Change'] - merged['% Rev Change']

    # Reorder and rename
    display_df = merged[[f'{prev_q} C&B', f'{latest_q} C&B', f'{prev_q} Revenue', f'{latest_q} Revenue',
                         '% C&B Change', '% Rev Change', 'C&B vs Rev Growth (pp)']].copy()

    display_df.columns = ['C&B Q1', 'C&B Q2', 'Revenue Q1', 'Revenue Q2',
                          '% C&B Change', '% Revenue Change', 'C&B Growth vs Revenue Growth (pp)']

    # Add Totals Row
    total_row = display_df.sum(numeric_only=True)
    total_row.name = 'Total'
    display_df = pd.concat([display_df, pd.DataFrame([total_row])])

    # Format %
    for col in ['% C&B Change', '% Revenue Change', 'C&B Growth vs Revenue Growth (pp)']:
        display_df[col] = display_df[col].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "—")

    # Show table and chart
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🧾 C&B vs Revenue Comparison by Segment")
        st.dataframe(display_df)

    with col2:
        bar_data = ((cb_df[latest_q] - cb_df[prev_q]) / cb_df[prev_q].replace(0, 1)) * 100
        bar_data = bar_data.sort_values()
        fig, ax = plt.subplots(figsize=(6, 6))

        norm = mcolors.TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100)
        cmap_red = cm.get_cmap('Reds')
        cmap_green = cm.get_cmap('Greens')
        colors = [cmap_red(norm(val)) if val < 0 else cmap_green(norm(val)) for val in bar_data]

        bar_data.plot(kind='barh', ax=ax, color=colors)
        ax.set_xlabel('% Change in C&B Cost')
        ax.set_title(f'C&B Change by Segment: {prev_q} vs {latest_q}')
        ax.set_xlim(-100, 100)

        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
            spine.set_edgecolor('#cccccc')

        st.pyplot(fig)
