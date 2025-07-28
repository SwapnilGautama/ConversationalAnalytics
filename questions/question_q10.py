import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from io import BytesIO

@st.cache_data
def load_data():
    df = pd.read_excel("sample_data/LNTData.xlsx")
    df.columns = df.columns.str.strip()
    df = df[df["Status"] == "Billable"]
    df = df[df["FresherAgeingCategory"].notna()]
    df["UT%"] = (df["TotalBillableHours"] / df["NetAvailableHours"]) * 100
    df["Month"] = pd.to_numeric(df["Month"], errors='coerce')
    df = df[df["Month"].between(1, 12)]
    df["MonthName"] = df["Month"].map({
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    })
    df["MonthOrder"] = df["Month"]
    df["Year"] = df["Year"].astype(str).str[:4]
    return df

def run(prompt=None):
    df = load_data()

    # Extract year and segment from chatbot prompt
    year = None
    segment_filter = None
    if prompt:
        for yr in ["2024", "2025"]:
            if yr in prompt:
                year = yr
        segments = df["Segment"].dropna().unique()
        for seg in segments:
            if str(seg).lower() in prompt.lower():
                segment_filter = seg

    if year:
        df = df[df["Year"] == year]
    if segment_filter:
        df = df[df["Segment"] == segment_filter]

    # Aggregate UT%
    agg_df = df.groupby(["MonthOrder", "MonthName", "Segment", "FresherAgeingCategory"])["UT%"].mean().reset_index()

    # Pivot Table
    table_df = agg_df.pivot_table(
        index=["MonthOrder", "MonthName", "Segment"],
        columns="FresherAgeingCategory",
        values="UT%"
    )
    table_df = table_df.reset_index().sort_values("MonthOrder").drop(columns="MonthOrder")
    table_df = table_df.round(1)

    # 💡 Top Key Insight Block — At top
    st.markdown("### 🔍 Key Insights")
    last_month = table_df["MonthName"].iloc[-1] if not table_df.empty else "N/A"
    trend_summary = ""
    if not table_df.empty:
        recent = table_df.iloc[-1].drop(["MonthName", "Segment"])
        top_cat = recent.idxmax()
        top_val = recent.max()
        trend_summary += f"**In {last_month}**, highest UT% was in **{top_cat}** at **{top_val:.1f}%**. "
        lowest_cat = recent.idxmin()
        lowest_val = recent.min()
        trend_summary += f"Lowest UT% was in **{lowest_cat}** at **{lowest_val:.1f}%**."
    else:
        trend_summary = "No data available for the selected year or segment."
    st.markdown(trend_summary)

    # 📋 Layout: Table and Chart side by side
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📋 Monthly UT% Table")
        st.dataframe(table_df.style.format("{:.1f}"))

    with col2:
        st.markdown("### 📈 UT% Trend by Fresher Category")
        chart_df = agg_df.groupby(["MonthOrder", "MonthName", "FresherAgeingCategory"])["UT%"].mean().reset_index()
        pivot_chart = chart_df.pivot(index="MonthOrder", columns="FresherAgeingCategory", values="UT%")
        pivot_chart.index = chart_df.drop_duplicates("MonthOrder").sort_values("MonthOrder")["MonthName"].values

        fig, ax = plt.subplots(figsize=(6, 4))
        pastel_colors = sns.color_palette("pastel")

        for idx, col in enumerate(pivot_chart.columns):
            ax.plot(pivot_chart.index, pivot_chart[col], label=col, linewidth=2, marker='o', color=pastel_colors[idx % len(pastel_colors)])

        ax.set_xlabel("Month")
        ax.set_ylabel("UT%")
        ax.set_title("Fresher UT% Trends (Monthly)")
        ax.grid(visible=True, linestyle='--', linewidth=0.3, color='lightgrey')
        ax.set_facecolor("white")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('lightgrey')
        ax.spines['bottom'].set_color('lightgrey')
        ax.legend(title="Fresher Category", fontsize=8, title_fontsize=9)
        st.pyplot(fig)
