# question_q3.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm

def run(df, user_question=None):
    import streamlit as st

    # Standardize column names
    df.columns = df.columns.str.strip()

    # Choose correct amount column
    amount_col = None
    for col in df.columns:
        if col.strip().lower() in ['amount in usd', 'amountinusd', 'amount']:
            amount_col = col
            break

    if not amount_col:
        st.error("❌ Column not found: Amount in USD")
        return

    # Convert Month column
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])

    # Add Quarter
    df['Quarter'] = df['Month'].dt.to_period('Q')

    # Get quarters
    latest_month = df['Month'].max()
    prev_q_month = (latest_month - pd.DateOffset(months=3)).replace(day=1)

    latest_q = latest_month.to_period('Q')
    prev_q = (latest_month - pd.DateOffset(months=3)).to_period('Q')

    # C&B data
    df_cb = df[df['Group3'].str.contains('C&B', na=False)]
    cb_summary = df_cb.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)

    # Revenue data
    df_rev = df[df['Type'].str.lower() == 'revenue']
    rev_summary = df_rev.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)

    # Ensure quarters
    for q in [prev_q, latest_q]:
        if q not in cb_summary.columns:
            cb_summary[q] = 0
        if q not in rev_summary.columns:
            rev_summary[q] = 0

    cb_summary = cb_summary[[prev_q, latest_q]] / 1e6
    rev_summary = rev_summary[[prev_q, latest_q]] / 1e6

    # Insights
    total_q1_cb = cb_summary[prev_q].sum()
    total_q2_cb = cb_summary[latest_q].sum()
    cb_change = ((total_q2_cb - total_q1_cb) / total_q1_cb) * 100 if total_q1_cb else 0

    total_q1_rev = rev_summary[prev_q].sum()
    total_q2_rev = rev_summary[latest_q].sum()
    rev_change = ((total_q2_rev - total_q1_rev) / total_q1_rev) * 100 if total_q1_rev else 0

    increased_segments = cb_summary[cb_summary[latest_q] > cb_summary[prev_q]].index.tolist()

    st.markdown("### 📊 C&B Cost Insights")
    st.markdown(f"- 💰 **Overall C&B change** from {prev_q} to {latest_q}: **{cb_change:+.1f}%**")
    st.markdown(f"- 💹 **Overall Revenue change** from {prev_q} to {latest_q}: **{rev_change:+.1f}%**")
    if increased_segments:
        st.markdown(f"- 📈 **Segments with increased C&B**: {', '.join(increased_segments)}")
    else:
        st.markdown("- ✅ No segments recorded an increase in C&B.")

    # Table
    cb_summary_disp = cb_summary.copy()
    rev_summary_disp = rev_summary.copy()

    cb_summary_disp['% Change'] = ((cb_summary[latest_q] - cb_summary[prev_q]) / cb_summary[prev_q].replace(0, 1)) * 100
    rev_summary_disp['% Rev Change'] = ((rev_summary[latest_q] - rev_summary[prev_q]) / rev_summary[prev_q].replace(0, 1)) * 100

    merged = cb_summary_disp[[prev_q, latest_q, '% Change']].merge(
        rev_summary_disp[['% Rev Change']], left_index=True, right_index=True
    )

    # Format
    merged.columns = [str(col) for col in merged.columns]
    merged['% Change'] = merged['% Change'].map(lambda x: f"{x:.2f}%")
    merged['% Rev Change'] = merged['% Rev Change'].map(lambda x: f"{x:.2f}%")

    # Layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🧾 C&B Cost (Million USD) and % Change")
        st.dataframe(merged)

    with col2:
        fig, ax = plt.subplots(figsize=(6, 6))
        bar_data = ((cb_summary[latest_q] - cb_summary[prev_q]) / cb_summary[prev_q].replace(0, 1)) * 100
        bar_data = bar_data.sort_values()

        norm = mcolors.TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100)
        cmap_red = cm.get_cmap('Reds')
        cmap_green = cm.get_cmap('Greens')
        colors = [cmap_red(norm(val)) if val < 0 else cmap_green(norm(val)) for val in bar_data]

        bar_data.plot(kind='barh', ax=ax, color=colors)

        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
            spine.set_edgecolor('#cccccc')

        ax.set_xlabel('% Change in C&B Cost')
        ax.set_title(f'C&B Change by Segment: {prev_q} vs {latest_q}')
        ax.set_xlim(-100, 100)
        st.pyplot(fig)
