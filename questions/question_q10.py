import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from kpi_engine.utilization import load_ut_data

def run(prompt=None):
    st.subheader("Fresher UT% Monthly Trends by Bucket")

    # Step 1: User Year Input
    selected_year = st.text_input("Enter Year (2024-25 or 2025-26):", value="2024-25")

    if selected_year not in ["2024-25", "2025-26"]:
        st.warning("Please enter year as '2024-25' or '2025-26'")
        return

    year_map = {"2024-25": "2024", "2025-26": "2025"}
    year_numeric = year_map[selected_year]

    # Step 2: Load Utilization Data
    df = load_ut_data()
    df["Year"] = df["Year"].astype(str)
    df = df[df["Year"] == year_numeric]
    df = df[df["Status"].isin(["Billable", "Non Billable"])]

    # Step 3: Filter only Fresher Categories
    fresher_buckets = [
        "Freshers ET(0-3 Months)",
        "Freshers ET(4-6 Months)",
        "Freshers PGET(0-3 Months)",
        "Freshers ETPremium(0-3 Months)"
    ]
    df = df[df["FresherAgeingCategory"].isin(fresher_buckets)]

    # Step 4: Aggregate Month-on-Month UT%
    trend_df = (
        df.groupby(["Month", "FresherAgeingCategory"])
        .agg({"UT%": "mean"})
        .reset_index()
        .sort_values(by=["FresherAgeingCategory", "Month"])
    )

    # Step 5: Insights
    st.markdown("### 🔍 Key Insights")
    latest_month = trend_df["Month"].max()
    for bucket in fresher_buckets:
        current = trend_df[(trend_df["FresherAgeingCategory"] == bucket) & (trend_df["Month"] == latest_month)]["UT%"].values
        prev = trend_df[(trend_df["FresherAgeingCategory"] == bucket) & (trend_df["Month"] == latest_month - 1)]["UT%"].values
        if len(current) > 0 and len(prev) > 0:
            delta = current[0] - prev[0]
            direction = "increased" if delta > 0 else "decreased"
            st.markdown(f"- UT% for **{bucket}** has {direction} by **{abs(delta):.1f}%** from month {latest_month - 1} to {latest_month}.")

    # Step 6: Table
    st.markdown("### 📊 Monthly UT% Table")
    table_df = trend_df.pivot(index="Month", columns="FresherAgeingCategory", values="UT%")
    st.dataframe(table_df.style.format("{:.1f}").set_properties(**{
        'border-color': 'lightgrey',
        'border-width': '1px',
        'border-style': 'solid'
    }), use_container_width=True)

    # Step 7: Line Chart
    st.markdown("### 📈 UT% Trend by Fresher Category")
    fig, ax = plt.subplots(figsize=(10, 5))
    pastel_colors = ["#A1CDE1", "#F4B6C2", "#BFD8B8", "#FFDEB4"]
    for i, bucket in enumerate(fresher_buckets):
        data = trend_df[trend_df["FresherAgeingCategory"] == bucket]
        if not data.empty:
            ax.plot(
                data["Month"],
                data["UT%"],
                label=bucket,
                linewidth=2.5,
                color=pastel_colors[i],
            )

    ax.set_title("Fresher UT% Trends (Monthly)", fontsize=14)
    ax.set_ylabel("Utilization %")
    ax.set_xlabel("Month")
    ax.grid(True, linestyle="--", linewidth=0.5, color="lightgrey")
    ax.legend(title="Fresher Category")
    ax.set_facecolor("white")
    sns.despine()
    st.pyplot(fig)
