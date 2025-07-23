# questions/question_q3.py

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run(df, user_query=None):
    df = df.copy()

    # --- Filter for C&B Cost ---
    cb_filter = df["Group4"].str.contains("C&B", case=False, na=False)
    df_cb = df[cb_filter & (df["Type"] == "Cost")].copy()
    df_cb["Month"] = pd.to_datetime(df_cb["Month"], format="%b %Y")
    df_cb["Quarter"] = df_cb["Month"].dt.to_period("Q")

    # --- Last 2 quarters ---
    last_two_quarters = sorted(df_cb["Quarter"].unique())[-2:]
    if len(last_two_quarters) < 2:
        st.warning("Not enough data for two quarters.")
        return

    q1, q2 = last_two_quarters[0], last_two_quarters[1]
    df_cb = df_cb[df_cb["Quarter"].isin([q1, q2])]

    # --- Group by Segment & Quarter ---
    cb_grouped = df_cb.groupby(["Segment", "Quarter"])["Amount in INR"].sum().unstack().fillna(0)
    cb_grouped.columns = [str(c) for c in cb_grouped.columns]
    cb_grouped["% Change"] = ((cb_grouped[str(q2)] - cb_grouped[str(q1)]) / cb_grouped[str(q1)].replace(0, 1)).round(4) * 100
    cb_grouped[[str(q1), str(q2)]] = cb_grouped[[str(q1), str(q2)]] / 1e7  # Convert to ₹ Cr
    cb_grouped[[str(q1), str(q2)]] = cb_grouped[[str(q1), str(q2)]].round(2)

    # --- Summary Stats ---
    total_cb_q2 = df_cb[df_cb["Quarter"] == q2]["Amount in INR"].sum() / 1e7
    top3_segments = cb_grouped[str(q2)].sort_values(ascending=False).head(3).index.tolist()
    increase_segment = cb_grouped["% Change"].idxmax()
    decrease_segment = cb_grouped["% Change"].idxmin()

    # --- Revenue Comparison ---
    df_rev = df[(df["Type"] == "Revenue") & (df["Quarter"].isin([q1, q2]))].copy()
    revenue_q1 = df_rev[df_rev["Quarter"] == q1]["Amount in INR"].sum()
    revenue_q2 = df_rev[df_rev["Quarter"] == q2]["Amount in INR"].sum()
    revenue_change = ((revenue_q2 - revenue_q1) / revenue_q1) * 100

    st.markdown(f"""
    ### 🔍 C&B Cost Analysis by Segment ({q1} vs {q2})
    - **Total C&B cost in {q2}**: ₹{total_cb_q2:.2f} Cr. Top segments: {', '.join(top3_segments)}.
    - **QoQ C&B Change**: Highest increase in **{increase_segment}**, highest drop in **{decrease_segment}**.
    - **Overall Revenue** changed by **{revenue_change:.2f}%** compared to C&B cost.
    """)

    # --- Pie chart for top 5 segments in Q2 ---
    pie_df = cb_grouped[str(q2)].sort_values(ascending=False)
    top5 = pie_df.head(5)
    others = pie_df[5:].sum()
    pie_data = top5.copy()
    if others > 0:
        pie_data["Others"] = others

    fig_pie, ax1 = plt.subplots()
    ax1.pie(pie_data, labels=pie_data.index, autopct="%1.1f%%", startangle=90)
    ax1.set_title(f"C&B Cost Distribution - {q2}")

    # --- Bar chart for % change ---
    fig_bar, ax2 = plt.subplots(figsize=(8, 6))
    cb_grouped["% Change"].sort_values(ascending=False).plot(kind="barh", ax=ax2, color="skyblue")
    ax2.set_title("QoQ % Change in C&B Cost by Segment")
    ax2.set_xlabel("% Change")
    ax2.invert_yaxis()

    # --- Layout ---
    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.markdown(f"#### 📊 C&B Cost by Segment (₹ Cr)")
        st.dataframe(cb_grouped[[str(q1), str(q2), "% Change"]].sort_values(by="% Change", ascending=False))
    with col2:
        st.pyplot(fig_pie)

    st.markdown("---")
    st.markdown("#### 📈 QoQ C&B % Change by Segment")
    st.pyplot(fig_bar)
