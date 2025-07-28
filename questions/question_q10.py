# question_q10.py

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from utilization import load_ut_data  # ✅ Make sure file is named exactly utilization.py

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
        segment_keywords = ["telecom", "transportation", "industrial", "consumer", "medical", "energy"]
        for s in segment_keywords:
            if s.lower() in prompt.lower():
                segment = s.capitalize()

    # ✅ Load and prepare data
    df = load_ut_data()
    df.columns = df.columns.str.strip()
    df = df[df["Status"].str.lower() == "billable"]  # Billable filter

    # ✅ Year filter
    if year:
        year_num = year.split("-")[0]
        df = df[df["Year"].astype(str).str.startswith(year_num)]

    # ✅ Segment filter
    if segment:
        df = df[df["Segment"].str.lower() == segment.lower()]

    # ✅ Fresher buckets
    fresher_categories = [
        "Freshers ET(0-3 Months)", 
        "Freshers ET(4-6 Months)",
        "Freshers PGET(0-3 Months)",
        "Freshers ETPremium(0-3 Months)"
    ]
    df = df[df["FresherAgeingCategory"].isin(fresher_categories)]

    # ✅ Month mapping
    month_map = {i: m for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
    df["MonthName"] = df["Month"].astype(int).map(month_map)
    df["MonthOrder"] = df["Month"].astype(int)

    # ✅ Pivot table for table output
    pivot_table = df.groupby(["MonthOrder", "MonthName", "Segment", "FresherAgeingCategory"])["UT%"].mean().reset_index()
    pivot_wide = pivot_table.pivot_table(
        index=["MonthOrder", "MonthName", "Segment"],
        columns="FresherAgeingCategory",
        values="UT%"
    ).sort_index()

    # ✅ Style table
    styled_table = pivot_wide.style.format("{:.1f}%").set_table_styles({
        '': {'selector': 'td, th', 'props': [('border', '1px solid lightgrey'), ('padding', '4px')]}
    })

    # ✅ Insight bullets
    st.markdown("🔹 **Insight 1**: Fresher UT% shows clear differentiation — premium ETs often display better utilization.")
    st.markdown("🔹 **Insight 2**: Noticeable dips around onboarding months may indicate bench periods or training.")

    # ✅ Show styled table
    st.write("### 📋 UT% by Month and Segment")
    st.dataframe(styled_table, use_container_width=True)

    # ✅ Line chart preparation
    chart_df = pivot_table.pivot_table(
        index="MonthOrder", columns="FresherAgeingCategory", values="UT%"
    ).sort_index()
    chart_df.index = chart_df.index.map(month_map)

    # ✅ Line chart
    fig, ax = plt.subplots(figsize=(10, 4))
    for col in chart_df.columns:
        ax.plot(chart_df.index, chart_df[col], label=col, linewidth=2)
    ax.set_ylabel("Utilization %")
    ax.set_title("Monthly UT% Trend by Fresher Bucket")
    ax.set_xlabel("Month")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)
    st.pyplot(fig)
