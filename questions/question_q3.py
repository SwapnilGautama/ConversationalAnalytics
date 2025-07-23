# question_q3.py

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def run_question():
    st.subheader("🧾 C&B Cost Comparison by Segment – Quarter over Quarter")

    # Load the data
    df = pd.read_excel("sample_data/LnTPnLSample.xlsx")

    # Filter for C&B cost
    cb_df = df[
        (df["Group4"].str.contains("C&B", case=False, na=False)) &
        (df["Type"] == "Cost")
    ].copy()

    # Convert Amount in INR to crores
    cb_df["Amount_Cr"] = cb_df["Amount in INR"] / 1e7

    # Convert Month to datetime and assign quarter labels
    cb_df["Month"] = pd.to_datetime(cb_df["Month"], format="%b %Y")
    cb_df["Quarter"] = cb_df["Month"].dt.to_period("Q")

    # Pivot table: sum of C&B cost by Segment and Quarter
    cb_summary = cb_df.pivot_table(
        index="Segment", 
        columns="Quarter", 
        values="Amount_Cr", 
        aggfunc="sum", 
        fill_value=0
    ).reset_index()

    quarters = sorted(cb_df["Quarter"].unique())
    if len(quarters) < 2:
        st.warning("❗Not enough quarters to compare.")
        return

    q1, q2 = quarters[-2], quarters[-1]
    cb_summary["% Change"] = ((cb_summary[q2] - cb_summary[q1]) / cb_summary[q1].replace(0, pd.NA)) * 100
    cb_summary.replace([pd.NA, pd.NaT], 0, inplace=True)

    # Total and top segments
    total_cb = cb_df.groupby("Segment")["Amount_Cr"].sum().sort_values(ascending=False)
    top_segments = total_cb.head(3)

    # Revenue data for comparison
    rev_df = df[df["Type"] == "Revenue"].copy()
    rev_df["Month"] = pd.to_datetime(rev_df["Month"], format="%b %Y")
    rev_df["Quarter"] = rev_df["Month"].dt.to_period("Q")
    rev_df["Amount_Cr"] = rev_df["Amount in INR"] / 1e7
    rev_q = rev_df.groupby("Quarter")["Amount_Cr"].sum()
    rev_change = ((rev_q[q2] - rev_q[q1]) / rev_q[q1]) * 100 if rev_q[q1] != 0 else 0

    # 🔹 Text Insights
    st.markdown("### 🧠 Summary Insights")
    st.markdown(f"1. **Total C&B Cost:** ₹{cb_df['Amount_Cr'].sum():,.2f} Cr. Top 3 segments: {', '.join(top_segments.index)}")
    st.markdown(f"2. **Quarter-over-Quarter C&B Change:**")
    for seg, val in cb_summary.sort_values(by="% Change", ascending=False).head(3)[["Segment", "% Change"]].values:
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;- {seg}: {val:.1f}% increase")
    for seg, val in cb_summary.sort_values(by="% Change").head(3)[["Segment", "% Change"]].values:
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;- {seg}: {val:.1f}% decrease")
    st.markdown(f"3. **Overall C&B vs Revenue Change:** C&B changed by {cb_summary['% Change'].mean():.1f}%, Revenue changed by {rev_change:.1f}%")

    # 📊 Table and Chart
    st.markdown("### 📋 C&B Cost by Segment – Quarter Comparison")

    col1, col2 = st.columns(2)

    with col1:
        formatted_df = cb_summary.copy()
        formatted_df[q1] = formatted_df[q1].apply(lambda x: f"{x:,.2f}")
        formatted_df[q2] = formatted_df[q2].apply(lambda x: f"{x:,.2f}")
        formatted_df["% Change"] = formatted_df["% Change"].apply(lambda x: f"{x:,.1f}%")
        st.dataframe(formatted_df.rename(columns={q1: f"{q1}", q2: f"{q2}"}), use_container_width=True)

    with col2:
        chart_df = cb_summary.sort_values(by="% Change", ascending=False)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.barh(chart_df["Segment"], chart_df["% Change"], color="coral")
        ax.set_xlabel("% Change in C&B Cost")
        ax.set_title("C&B % Change by Segment")
        st.pyplot(fig)
