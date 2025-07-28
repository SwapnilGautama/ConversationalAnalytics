import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from kpi_engine import utilization

def run(user_query: str = ""):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    df = utilization.load_ut_data()

    # Filter relevant data
    df = df[df["Status"].notna()]
    df = df[df["FresherAgeingCategory"].notna()]
    df = df[df["UT%"].notna()]
    df = df[df["PSNo"].notna()]

    if df.empty:
        st.info("No fresher UT% data available.")
        return

    # Map numeric month to short names
    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    df["MonthName"] = df["Month"].astype(int).map(month_map)

    # Group and calculate average UT% by month and fresher bucket
    grouped = df.groupby(["Month", "MonthName", "FresherAgeingCategory"])["UT%"].mean().reset_index()

    # Pivot table for table display
    table_df = grouped.pivot(index="MonthName", columns="FresherAgeingCategory", values="UT%").fillna(0)
    table_df = table_df.loc[[m for m in month_map.values() if m in table_df.index]]  # order months

    # ➤ Format table values as %
    styled_table = table_df.style.format("{:.1f}%").set_table_styles(
        [{'selector': 'th, td', 'props': [('border', '1px solid lightgrey')]}]
    )
    st.subheader("🏋️ Monthly UT% Table")
    st.dataframe(styled_table, use_container_width=True)

    # ➤ Plot smoothed pastel-colored line chart
    st.subheader("🌐 UT% Trend by Fresher Category")
    fig, ax = plt.subplots(figsize=(10, 5))
    pastel_colors = sns.color_palette("pastel", n_colors=10)

    for i, category in enumerate(table_df.columns):
        ax.plot(table_df.index, table_df[category], label=category,
                marker='o', linewidth=2, linestyle='-',
                color=pastel_colors[i % len(pastel_colors)])

    ax.set_xlabel("Month")
    ax.set_ylabel("UT%")
    ax.set_title("Fresher UT% Trends (Monthly)")
    ax.grid(True, linestyle='--', linewidth=0.5, color='lightgrey')
    ax.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('lightgrey')
    ax.spines['left'].set_color('lightgrey')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize="small")

    st.pyplot(fig)

    # ➤ Key Insights (story-based summary)
    st.subheader("🔍 Key Insights")

    insight_lines = []
    for col in table_df.columns:
        values = table_df[col].dropna()
        if len(values) >= 2:
            start = values.iloc[0]
            end = values.iloc[-1]
            change = end - start
            trend = "increased" if change > 0 else "decreased" if change < 0 else "remained stable"
            insight_lines.append(
                f"• {col} UT% {trend} from {start:.1f}% to {end:.1f}% over the months ({'+' if change > 0 else ''}{change:.1f}pt change)."
            )

    if insight_lines:
        st.markdown("\n".join(insight_lines))
    else:
        st.info("Not enough data to generate insights.")
