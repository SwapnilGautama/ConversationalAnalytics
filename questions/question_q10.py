import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import re
from io import BytesIO

def run(prompt=None):
    st.subheader("📊 Fresher UT% Monthly Trends by Bucket")

    @st.cache_data
    def load_data():
        df = pd.read_excel("sample_data/LNTData.xlsx")
        df["Date_a"] = pd.to_datetime(df["Date_a"], errors="coerce")
        df["Month"] = df["Date_a"].dt.month
        df["MonthName"] = df["Date_a"].dt.strftime("%b")
        df["Year"] = df["Date_a"].dt.year
        df["Utilization %"] = (df["TotalBillableHours"] / df["NetAvailableHours"]) * 100
        return df

    df = load_data()

    # ✅ Parse year and segment from prompt
    selected_year = None
    if prompt:
        year_match = re.search(r"(20\d{2})", prompt)
        if year_match:
            selected_year = int(year_match.group(1))

    segments = df["Segment"].dropna().unique().tolist()
    segment_from_prompt = None
    if prompt:
        for s in segments:
            if s.lower() in prompt.lower():
                segment_from_prompt = s
                break

    if selected_year:
        df = df[df["Year"] == selected_year]
    if segment_from_prompt:
        df = df[df["Segment"] == segment_from_prompt]

    fresher_buckets = [
        "Freshers DET(>6 Months)",
        "Freshers ET(0-3 Months)",
        "Freshers ET(4-6 Months)",
        "Freshers ET(>6 Months)",
        "Freshers ET-Premium (4-6 months)",
        "Freshers ET-Premium (>6 months)",
        "Freshers PGET (4-6 months)",
        "Non Freshers",
        "Non-Freshers(1-2 yrs)",
    ]

    # Filter only fresher bucket rows
    df = df[df["FresherAgeingCategory"].isin(fresher_buckets)]

    if df.empty:
        st.warning("No data available for selected filters.")
        return

    # Pivot table for table and chart
    pivot_df = df.groupby(["MonthName", "FresherAgeingCategory"])["Utilization %"].mean().unstack().fillna(0)
    pivot_df = pivot_df.reindex(["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

    # ✅ Insights at the top
    st.markdown("🔍 **Key Insights**")
    insights = []
    for col in pivot_df.columns:
        series = pivot_df[col]
        first_val = series[series != 0].iloc[0] if (series != 0).any() else 0
        last_val = series[series != 0].iloc[-1] if (series != 0).any() else 0
        change = last_val - first_val
        insights.append((col, first_val, last_val, change))

    top_insights = sorted(insights, key=lambda x: abs(x[3]), reverse=True)[:2]
    for name, start, end, change in top_insights:
        st.markdown(f"- **{name}** UT% changed from {start:.1f}% to {end:.1f}% ({change:+.1f}pt change)")

    # ✅ Side-by-side layout
    col1, col2 = st.columns(2)

    with col1:
        table_df = pivot_df.copy()
        table_df["Segment"] = segment_from_prompt if segment_from_prompt else "All Segments"
        st.markdown("📋 **Monthly UT% Table**")
        st.dataframe(table_df.style.format("{:.1f}%"))

    with col2:
        st.markdown("📈 **UT% Trend by Fresher Category**")
        fig, ax = plt.subplots(figsize=(8, 4))
        pastel_palette = sns.color_palette("pastel")
        for idx, col in enumerate(pivot_df.columns):
            ax.plot(pivot_df.index, pivot_df[col], label=col, linewidth=2, marker="o", color=pastel_palette[idx % len(pastel_palette)])
        ax.set_ylabel("UT%")
        ax.set_xlabel("Month")
        ax.set_title("Fresher UT% Trends (Monthly)")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("lightgrey")
        ax.spines["bottom"].set_color("lightgrey")
        ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=8)
        st.pyplot(fig)
