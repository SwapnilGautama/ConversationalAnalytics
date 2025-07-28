import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from kpi_engine import utilization
import seaborn as sns

def run(user_query: str = ""):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    # Load data
    df = utilization.load_ut_data()

    # Clean and filter data
    df = df[df["Status"].notna()]
    df = df[df["FresherAgeingCategory"].notna()]
    df = df[df["Utilization %"].notna()]

    if df.empty:
        st.info("No fresher UT% data available.")
        return

    # Map numeric month to name
    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    df["MonthName"] = df["Month"].map(month_map)

    # Sort month order
    df["MonthName"] = pd.Categorical(df["MonthName"], categories=list(month_map.values()), ordered=True)

    # Create pivot table for UT% by Month × FresherAgeingCategory
    ut_table = df.pivot_table(index="MonthName", columns="FresherAgeingCategory", values="Utilization %", aggfunc="mean")
    ut_table = ut_table.reset_index()

    # Generate insights
    st.subheader("🔍 Key Insights")
    if ut_table.empty:
        st.info("Not enough data to generate insights.")
    else:
        latest_month = ut_table["MonthName"].dropna().iloc[-1]
        trends = []
        for cat in ut_table.columns[1:]:
            series = ut_table[cat].dropna()
            if len(series) >= 2:
                trend = "↑" if series.iloc[-1] > series.iloc[-2] else "↓"
                change = series.iloc[-1] - series.iloc[-2]
                trends.append(f"{cat}: {trend} {change:.1f}% from previous month")
        if trends:
            for t in trends:
                st.markdown(f"- {t}")
        else:
            st.write("No clear trend data available.")

    # Layout: Side-by-side table and chart
    st.subheader("🏋️ Monthly UT% Table")
    col1, col2 = st.columns(2)

    with col1:
        if not ut_table.empty:
            st.dataframe(ut_table.style.set_properties(**{
                'border-color': 'lightgrey',
                'border-style': 'solid',
                'border-width': '1px'
            }))
        else:
            st.write("No data to display.")

    with col2:
        if not ut_table.empty:
            plt.figure(figsize=(8, 4))
            pastel_colors = sns.color_palette("pastel")
            for i, col in enumerate(ut_table.columns[1:]):
                plt.plot(ut_table["MonthName"], ut_table[col], marker='o',
                         linestyle='-', label=col,
                         linewidth=2, color=pastel_colors[i % len(pastel_colors)])
            plt.title("Fresher UT% Trends (Monthly)")
            plt.xlabel("Month")
            plt.ylabel("UT%")
            plt.grid(visible=True, linestyle='--', linewidth=0.5, alpha=0.7)
            plt.legend(title="Fresher Category", loc='best')
            sns.despine()
            st.pyplot(plt.gcf())
        else:
            st.write("No data to plot.")
