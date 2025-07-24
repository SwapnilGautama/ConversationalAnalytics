# question_q3.py

import pandas as pd
import matplotlib.pyplot as plt

def run(df, user_question=None):
    import streamlit as st

    # Standardize column names
    df.columns = df.columns.str.strip()

    # Choose correct amount column
    amount_col = None
    for col in df.columns:
        if col.strip().lower() in ['amount in inr', 'amountinr', 'amount']:
            amount_col = col
            break

    if not amount_col:
        st.error("❌ Column not found: Amount in INR")
        return

    # Convert Month column
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])

    # C&B filter
    df_cb = df[df['Group3'].str.contains('C&B', na=False)]
    df_rev = df[df['Type'].str.lower() == 'revenue']

    # Get quarter info
    latest_month = df_cb['Month'].max()
    prev_q_month = (latest_month - pd.DateOffset(months=3)).replace(day=1)

    # Group by Segment and Quarter
    df_cb['Quarter'] = df_cb['Month'].dt.to_period('Q')
    cb_summary = df_cb.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)
    df_rev['Quarter'] = df_rev['Month'].dt.to_period('Q')
    rev_summary = df_rev.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)

    if cb_summary.shape[1] < 2 or rev_summary.shape[1] < 2:
        st.warning("Not enough quarterly data to compare.")
        return

    cb_summary = cb_summary.sort_index(axis=1) / 1e7
    rev_summary = rev_summary.sort_index(axis=1) / 1e7
    q1, q2 = cb_summary.columns[-2], cb_summary.columns[-1]

    # 🔹 Commentary block
    total_cb_q1 = cb_summary[q1].sum()
    total_cb_q2 = cb_summary[q2].sum()
    total_rev_q1 = rev_summary[q1].sum()
    total_rev_q2 = rev_summary[q2].sum()
    cb_change = ((total_cb_q2 - total_cb_q1) / total_cb_q1) * 100 if total_cb_q1 else 0
    rev_change = ((total_rev_q2 - total_rev_q1) / total_rev_q1) * 100 if total_rev_q1 else 0

    flagged_segments = []
    for seg in cb_summary.index:
        cb_q1 = cb_summary.loc[seg, q1]
        cb_q2 = cb_summary.loc[seg, q2]
        rev_q1 = rev_summary.loc[seg, q1] if seg in rev_summary.index else 0
        rev_q2 = rev_summary.loc[seg, q2] if seg in rev_summary.index else 0
        cb_growth = ((cb_q2 - cb_q1) / cb_q1 * 100) if cb_q1 else 0
        rev_growth = ((rev_q2 - rev_q1) / rev_q1 * 100) if rev_q1 else 0
        if cb_q2 > cb_q1 and rev_growth < cb_growth:
            flagged_segments.append(seg)

    st.markdown("### 📊 C&B and Revenue Quarter-over-Quarter")
    st.markdown(f"- 💰 **C&B changed by** {cb_change:+.1f}% from {q1} to {q2}")
    st.markdown(f"- 📈 **Revenue changed by** {rev_change:+.1f}% from {q1} to {q2}")
    if flagged_segments:
        st.markdown(f"- ⚠️ **Segments where C&B increased faster than Revenue**: {', '.join(flagged_segments)}")
    else:
        st.markdown("- ✅ No segments had disproportionate C&B increase")

    # Table output
    cb_summary_display = cb_summary.copy()
    cb_summary_display['% Change'] = ((cb_summary[q2] - cb_summary[q1]) / cb_summary[q1].replace(0, 1)) * 100
    cb_summary_display[q1] = cb_summary_display[q1].round(1)
    cb_summary_display[q2] = cb_summary_display[q2].round(1)
    cb_summary_display['% Change'] = cb_summary_display['% Change'].map(lambda x: f"{x:.2f}%")
    cb_summary_display.columns = [str(col) for col in cb_summary_display.columns]

    # Side-by-side layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🧾 C&B Cost (INR Cr) and % Change")
        st.dataframe(cb_summary_display)

    with col2:
        # Prepare chart
        fig, ax = plt.subplots(figsize=(6, 6))
        bar_data = ((cb_summary[q2] - cb_summary[q1]) / cb_summary[q1].replace(0, 1)) * 100
        colors = ['red' if seg == 'Media & Technology' else 'skyblue' for seg in bar_data.index]
        bar_data.sort_values().plot(kind='barh', ax=ax, color=colors)

        # 👇 Updated border styling
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
            spine.set_edgecolor('#cccccc')

        ax.set_xlabel('% Change in C&B Cost')
        ax.set_title(f'C&B Change by Segment: {q1} vs {q2}')
        ax.set_xlim(-100, 100)
        st.pyplot(fig)
