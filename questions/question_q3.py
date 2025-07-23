# questions/question_q3.py

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run(df, user_query=None):
    df = df.copy()

    # --- Filter C&B Costs ---
    cb_filter = df["Group4"].str.contains("C&B", case=False, na=False)
    df_cb = df[cb_filter & (df["Type"] == "Cost")].copy()
    df_cb["Month"] = pd.to_datetime(df_cb["Month"], format="%b %Y")
    df_cb["Quarter"] = df_cb["Month"].dt.to_period("Q")
    
    # --- Get last two quarters ---
    last_two_quarters = sorted(df_cb["Quarter"].unique())[-2:]
    q1, q2 = last_two_quarters[0], last_two_quarters[1]
    df_cb = df_cb[df_cb["Quarter"].isin(last_two_quarters)]

    # --- Group by Segment & Quarter ---
    segment_quarter = df_cb.groupby(["Segment", "Quarter"])["Amount in INR"].sum().unstack().fillna(0)
    segment_quarter.columns = [str(c) for c in segment_quarter.columns]
    segment_quarter["% Change"] = ((segment_quarter[str(q2)] - segment_quarter[str(q1)]) / segment_quarter[str(q1)] * 100).round(2)

    # --- Round values in Crores ---
    segment_quarter[[str(q1), str(q2)]] = segment_quarter[[str(q1), str(q2)]] / 1e7
    segment_quarter[[str(q1), str(q2)]] = segment_quarter[[str(q1), str(q2)]].round(2)

    # --- Prepare Bar Chart ---
    fig, ax = plt.subplots(figsize=(8, 6))
    segment_quarter["% Change"].sort_values(ascending=False).plot(kind="barh", ax=ax, color="skyblue")
    ax.set_title("QoQ % Change in C&B Cost by Segment")
    ax.set_xlabel("% Change")
    ax.invert_yaxis()
    st.pyplot(fig)

    # --- Summary Insights ---
    total_cb_q2 = df_cb[df_cb["Quarter"] == q2]["Amount in INR"].sum() / 1e7
    top3_segments = segment_quarter[str(q2)].sort_values(ascending=False).head(3).index.tolist()

    change_df = segment_quarter.copy()
    increase_segment = change_df["% Change"].idxmax()
    decrease_segment = change_df["% Change"].idxmin()

    # Revenue comparison
    df_rev = df[(df["Type"] == "Revenue") & (df["Quarter"].isin(last_two_quarters))]
    revenue_q1 = df_rev[df_rev["Quarter"] == q1]["Amount in INR"].sum()
    revenue_q2 = df_rev[df_rev["Quarter"] == q2]["Amount in INR"].sum()
    revenue_change = ((revenue_q2 - revenue_q1) / revenue_q1 * 100)

    st.markdown(f"""
    ### 🔍 C&B Cost Analysis by Segment ({q1} vs {q2})
    - **Total C&B cost in {q2}**: ₹{total_cb_q2:.2f} Cr. Top segments: {', '.join(top3_segments)}.
    - **QoQ C&B Change**: Highest increase in **{increase_segment}**, highest drop in **{decrease_segment}**.
    - **Overall Revenue** changed by **{revenue_change:.2f}%** compared to C&B cost.
    """)

    # --- Show table and chart side-by-side ---
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown("#### 📊 C&B Cost Change by Segment (in ₹ Cr)")
        st.dataframe(segment_quarter)

    return
