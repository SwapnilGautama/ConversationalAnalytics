import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from kpi_engine import utilization
import seaborn as sns

def run(user_query: str = ""):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    # Load data
    df = utilization.load_ut_data()

    # Filter nulls
    df = df[df['Status'].notna()]
    df = df[df['FresherAgeingCategory'].notna()]
    df = df[df['ut%'].notna()]

    if df.empty:
        st.info("No fresher UT% data available.")
        return

    # Extract year and segment from query
    year = "2025-26" if "2025" in user_query else "2024-25"
    segment = None
    possible_segments = df["Segment"].dropna().unique().tolist()
    for s in possible_segments:
        if str(s).lower() in user_query.lower():
            segment = s
            break

    df = df[df["Year"] == year]
    if segment:
        df = df[df["Segment"] == segment]

    # Month number to short name
    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    df["MonthName"] = df["Month"].map(month_map)

    # Aggregate UT% by MonthName, FresherAgeingCategory, Segment
    df_grouped = (
        df.groupby(["MonthName", "FresherAgeingCategory", "Segment"])["ut%"]
        .mean()
        .reset_index()
    )

    if df_grouped.empty:
        st.warning("No data after filtering for year and segment.")
        return

    # Pivot for table display
    df_pivot = df_grouped.pivot_table(
        index=["MonthName", "Segment"],
        columns="FresherAgeingCategory",
        values="ut%"
    ).reset_index()

    # Format as percent with 1 decimal
    df_display = df_pivot.copy()
    for col in df_display.columns[2:]:
        df_display[col] = df_display[col].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "")

    # Key Insights
    latest_month = df_grouped["MonthName"].dropna().unique().tolist()[-1]
    first_month = df_grouped["MonthName"].dropna().unique().tolist()[0]

    trend_summary = df_grouped[df_grouped["MonthName"].isin([first_month, latest_month])]
    pivot_trend = trend_summary.pivot(index="FresherAgeingCategory", columns="MonthName", values="ut%")
    pivot_trend["Change"] = pivot_trend[latest_month] - pivot_trend[first_month]

    top_increase = pivot_trend["Change"].idxmax()
    top_decrease = pivot_trend["Change"].idxmin()

    top_inc_val = pivot_trend.loc[top_increase, "Change"]
    top_dec_val = pivot_trend.loc[top_decrease, "Change"]

    st.subheader("🔍 Key Insights")
    st.markdown(f"""
    - 📈 **Highest UT% increase**: **{top_increase}**, up by **{top_inc_val:.1f}pt** from {first_month} to {latest_month}.
    - 📉 **Sharpest UT% drop**: **{top_decrease}**, down by **{top_dec_val:.1f}pt** from {first_month} to {latest_month}.
    """)

    # Layout: table and chart side by side
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🧮 Monthly UT% Table")
        st.dataframe(df_display.style.set_properties(**{
            'border-color': '#ccc',
            'border-width': '1px',
            'border-style': 'solid'
        }), use_container_width=True)

    with col2:
        st.subheader("📈 UT% Trend by Fresher Category")

        # Prepare data for line chart
        df_chart = df_grouped.copy()
        df_chart["MonthOrder"] = df_chart["MonthName"].map({
            v: k for k, v in month_map.items()
        })
        df_chart = df_chart.sort_values("MonthOrder")

        pastel_colors = sns.color_palette("pastel", n_colors=df_chart["FresherAgeingCategory"].nunique())

        plt.figure(figsize=(10, 5))
        for i, category in enumerate(df_chart["FresherAgeingCategory"].unique()):
            temp = df_chart[df_chart["FresherAgeingCategory"] == category]
            plt.plot(
                temp["MonthName"],
                temp["ut%"],
                label=category,
                color=pastel_colors[i],
                linewidth=2,
                linestyle='-',
                marker='o'
            )

        plt.title("Fresher UT% Trends (Monthly)")
        plt.ylabel("UT%")
        plt.xlabel("Month")
        plt.grid(True, linestyle='--', linewidth=0.5, color='grey', alpha=0.3)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['left'].set_color('#ccc')
        plt.gca().spines['bottom'].set_color('#ccc')
        plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
        st.pyplot(plt)

    st.success("✅ Analysis complete.")
