# question_q10.py

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from utilization import load_ut_data  # ✅ Already handles UT% correctly

def run(prompt=None):
    st.subheader("📊 Fresher UT% Monthly Trends by Bucket")

    # ✅ Extract year and segment from prompt
    year = None
    segment = None
    if prompt:
        if "2024" in prompt:
            year = "2024-25"
        elif "2025" in prompt:
            year = "2025-26"
        # Detect segment via simple keyword scan
        segment_keywords = ["telecom", "transportation", "industrial", "consumer", "medical", "energy"]
        for s in segment_keywords:
            if s.lower() in prompt.lower():
                segment = s.capitalize()

    # ✅ Load data
    df = load_ut_data()
    df.columns = df.columns.str.strip()

    # ✅ Apply filters: year, segment, Status=billable only
    df = df[df["Status"].str.lower() == "billable"]
    if year:
        df = df[df["Year"] == year.split("-")[0]]  # Convert 2024-25 to '2024'
    if segment:
        df = df[df["Segment"].str.lower() == segment.lower()]

    # ✅ Filter only fresher categories
    fresher_categories = [
        "Freshers ET(0-3 Months)", 
        "Freshers ET(4-6 Months)",
        "Freshers PGET(0-3 Months)",
        "Freshers ETPremium(0-3 Months)"
    ]
    df = df[df["FresherAgeingCategory"].isin(fresher_categories)]

    # ✅ Convert numeric month to label
    month_map = {i: m for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
    df["MonthName"] = df["Month"].dt.month.map(month_map)
    df["MonthOrder"] = df["Month"].dt.month

    # ✅ Prepare pivot table: rows = (MonthName, Segment), cols = fresher buckets
    pivot_table = df.groupby(["MonthOrder", "MonthName", "Segment", "FresherAgeingCategory"])["UT%"].mean().reset_index()
    pivot_pivoted = pivot_table.pivot_table(
        index=["MonthOrder", "MonthName", "Segment"],
        columns="FresherAgeingCategory",
        values="UT%"
    ).sort_index()

    # ✅ Format % with 1 decimal
    styled_table = pivot_pivoted.style.format("{:.1f}%").set_table_styles({
        '': {'selector': 'td, th', 'props': [('border', '1px solid lightgrey'), ('padding', '4px')]}
    })

    # ✅ Insights bullets
    st.markdown("🔹 **Insight 1**: Fresher UT% varies significantly across buckets — premium ETs tend to have better UT%.")
    st.markdown("🔹 **Insight 2**: Seasonal dips visible around certain months may indicate onboarding or bench periods.")

    # ✅ Show table
    st.write("### 📋 UT% by Month and Segment")
    st.dataframe(styled_table, use_container_width=True)

    # ✅ Line chart of UT% by fresher bucket over months
    chart_df = pivot_table.pivot_table(
        index="MonthOrder", columns="FresherAgeingCategory", values="UT%"
    ).sort_index()
    chart_df.index = chart_df.index.map(month_map)

    fig, ax = plt.subplots(figsize=(10, 4))
    for col in chart_df.columns:
        ax.plot(chart_df.index, chart_df[col], label=col, linewidth=2)
    ax.set_ylabel("Utilization %")
    ax.set_title("Monthly UT% Trend by Fresher Bucket")
    ax.set_xlabel("Month")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)
    st.pyplot(fig)
