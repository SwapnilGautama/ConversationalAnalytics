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

    # Get quarter info
    latest_month = df_cb['Month'].max()
    prev_q_month = (latest_month - pd.DateOffset(months=3)).replace(day=1)

    # Group by Segment and Quarter
    df_cb['Quarter'] = df_cb['Month'].dt.to_period('Q')
    cb_summary = df_cb.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)

    if cb_summary.shape[1] < 2:
        st.warning("Not enough quarterly data to compare.")
        return

    # Ensure correct quarter order
    cb_summary = cb_summary.sort_index(axis=1)
    q1, q2 = cb_summary.columns[-2], cb_summary.columns[-1]

    # Convert to INR Crores
    cb_summary = cb_summary / 1e7

    # Insights
    summary = []
    for seg in cb_summary.index:
        old = cb_summary.loc[seg, q1]
        new = cb_summary.loc[seg, q2]
        change_pct = ((new - old) / old * 100) if old != 0 else 0
        summary.append(f"{seg}: {change_pct:+.1f}% change in C&B from {q1} to {q2}")

    st.markdown("### 📊 C&B Cost Variation by Segment")
    for line in summary:
        st.markdown(f"- {line}")

    # Table output
    cb_summary_display = cb_summary.copy()
    cb_summary_display['% Change'] = ((cb_summary[q2] - cb_summary[q1]) / cb_summary[q1].replace(0, 1)) * 100
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

       # Remove plot outline (spines)
       for spine in ax.spines.values():
           spine.set_visible(False)

       ax.set_xlabel('% Change in C&B Cost')
       ax.set_title(f'C&B Change by Segment: {q1} vs {q2}')
       ax.set_xlim(-100, 100)
       st.pyplot(fig)
