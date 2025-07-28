import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from kpi_engine import utilization

def run(user_query: str = ""):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    # Load data
    df = utilization.load_ut_data()

    # Clean and filter required data
    df = df[df['Status'].notna() & df['FresherAgeingCategory'].notna()]
    df = df[df['Utilization %'].notna()]
    
    if df.empty:
        st.info("No fresher UT% data available.")
        return

    # Mapping month number to name
    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    df['MonthName'] = df['Month'].map(month_map)

    # Grouping
    df_grouped = df.groupby(['MonthName', 'FresherAgeingCategory'])['Utilization %'].mean().reset_index()

    # Pivot for table display
    pivot_df = df_grouped.pivot(index='MonthName', columns='FresherAgeingCategory', values='Utilization %')
    pivot_df = pivot_df.reindex(month_map.values())  # Ensure month order

    # Format as percent
    styled_table = pivot_df.style.format("{:.1f}%").set_table_styles(
        [{'selector': 'td, th', 'props': [('border', '1px solid #ccc')]}]
    )

    # Insights
    st.subheader("🔍 Key Insights")
    insights = []
    for cat in pivot_df.columns:
        series = pivot_df[cat].dropna()
        if len(series) > 1:
            change = series.iloc[-1] - series.iloc[0]
            direction = "increased" if change > 0 else "decreased"
            insights.append(f"{cat} has {direction} by {abs(change):.1f} percentage points from {series.index[0]} to {series.index[-1]}.")
    if insights:
        for i in insights:
            st.markdown(f"- {i}")
    else:
        st.info("Not enough data to generate insights.")

    # Display table and chart side by side
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏋️ Monthly UT% Table")
        st.dataframe(styled_table, use_container_width=True)

    with col2:
        st.subheader("🌐 UT% Trend by Fresher Category")
        plt.figure(figsize=(8, 5))
        sns.set(style="whitegrid")
        pastel = sns.color_palette("pastel")

        for i, cat in enumerate(pivot_df.columns):
            plt.plot(pivot_df.index, pivot_df[cat], marker='o', label=cat, color=pastel[i % len(pastel)], linewidth=2)

        plt.xlabel("Month")
        plt.ylabel("UT%")
        plt.title("Fresher UT% Trends (Monthly)")
        plt.xticks(rotation=45)
        plt.legend()
        plt.gca().spines['top'].set_color('#ccc')
        plt.gca().spines['right'].set_color('#ccc')
        plt.gca().spines['bottom'].set_color('#ccc')
        plt.gca().spines['left'].set_color('#ccc')
        st.pyplot(plt.gcf())
