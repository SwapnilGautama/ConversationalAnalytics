# question_q4.py

import pandas as pd
import matplotlib.pyplot as plt

def run(df, user_question=None):
    import streamlit as st

    st.markdown("## 📉 MoM Trend of C&B Cost % w.r.t Revenue")

    # Standardize column names
    df.columns = df.columns.str.strip()

    # Detect correct amount column
    amount_col = None
    for col in df.columns:
        if col.strip().lower() in ['amount in inr', 'amountinr', 'amount']:
            amount_col = col
            break
    if not amount_col:
        st.error("❌ Column not found: Amount in INR")
        return

    # Parse Month
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])

    # Filter required segments and months
    latest_month = df['Month'].max()
    prev_month = (latest_month - pd.DateOffset(months=1)).replace(day=1)

    # Format month names
    month_fmt = lambda x: x.strftime('%b %Y')
    month_latest = month_fmt(latest_month)
    month_prev = month_fmt(prev_month)

    # Filter C&B cost
    cb_df = df[df['Group3'].str.contains('C&B', na=False)]
    cb_df['MonthPeriod'] = cb_df['Month'].dt.to_period('M')
    cb_by_segment = cb_df.groupby(['Segment', 'MonthPeriod'])[amount_col].sum().unstack(fill_value=0)

    # Filter Revenue
    rev_df = df[df['Type'].str.lower() == 'revenue']
    rev_df['MonthPeriod'] = rev_df['Month'].dt.to_period('M')
    rev_by_segment = rev_df.groupby(['Segment', 'MonthPeriod'])[amount_col].sum().unstack(fill_value=0)

    # Align months
    cb_by_segment = cb_by_segment.loc[:, cb_by_segment.columns.isin([prev_month.to_period('M'), latest_month.to_period('M')])]
    rev_by_segment = rev_by_segment.loc[:, rev_by_segment.columns.isin([prev_month.to_period('M'), latest_month.to_period('M')])]

    # Convert to INR Crores
    cb_by_segment = cb_by_segment / 1e7
    rev_by_segment = rev_by_segment / 1e7

    # Calculate % change
    cb_pct_change = ((cb_by_segment[latest_month.to_period('M')] - cb_by_segment[prev_month.to_period('M')]) / cb_by_segment[prev_month.to_period('M')].replace(0, 1)) * 100
    rev_pct_change = ((rev_by_segment[latest_month.to_period('M')] - rev_by_segment[prev_month.to_period('M')]) / rev_by_segment[prev_month.to_period('M')].replace(0, 1)) * 100

    # Overall changes
    cb_total_prev = cb_df[cb_df['Month'].dt.to_period('M') == prev_month.to_period('M')][amount_col].sum()
    cb_total_curr = cb_df[cb_df['Month'].dt.to_period('M') == latest_month.to_period('M')][amount_col].sum()
    cb_change_pct = ((cb_total_curr - cb_total_prev) / cb_total_prev) * 100 if cb_total_prev else 0

    rev_total_prev = rev_df[rev_df['Month'].dt.to_period('M') == prev_month.to_period('M')][amount_col].sum()
    rev_total_curr = rev_df[rev_df['Month'].dt.to_period('M') == latest_month.to_period('M')][amount_col].sum()
    rev_change_pct = ((rev_total_curr - rev_total_prev) / rev_total_prev) * 100 if rev_total_prev else 0

    # 🧠 Insights
    top_cb = cb_by_segment[latest_month.to_period('M')].sort_values(ascending=False).head(3).index.tolist()
    st.markdown("### 🧠 Key Insights")
    st.markdown(f"- Overall C&B cost changed by **{cb_change_pct:.2f}%** from **{month_prev}** to **{month_latest}**.")
    st.markdown(f"- Overall Revenue changed by **{rev_change_pct:.2f}%** in the same period.")
    st.markdown(f"- Top C&B segments in {month_latest}: **{', '.join(top_cb)}**")

    # 📊 Table
    combined = pd.DataFrame({
        f'C&B {month_prev}': cb_by_segment[prev_month.to_period('M')],
        f'C&B {month_latest}': cb_by_segment[latest_month.to_period('M')],
        '% Change': cb_pct_change
    }).round(2).sort_values(by='% Change', ascending=False)

    # 📈 Charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🧾 MoM C&B Cost (INR Cr)")
        st.dataframe(combined)

    with col2:
        fig, ax = plt.subplots(figsize=(6, 6))
        cb_pct_change.sort_values().plot(kind='barh', ax=ax, color='purple')
        ax.set_title('C&B % Change by Segment')
        ax.set_xlabel('% Change')
        ax.set_xlim(-100, 100)
        st.pyplot(fig)

    # 📉 Line chart: Revenue
    st.markdown("### 📈 Revenue by Segment")
    rev_line_data = rev_by_segment.loc[:, [prev_month.to_period('M'), latest_month.to_period('M')]].T
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    for segment in rev_line_data.columns:
        ax2.plot(rev_line_data.index.astype(str), rev_line_data[segment], marker='o', label=segment)
    ax2.set_ylabel("Revenue (INR Cr)")
    ax2.set_title("Monthly Revenue Trend")
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(fig2)
