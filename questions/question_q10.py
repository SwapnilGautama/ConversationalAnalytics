import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from kpi_engine.utilization import load_ut_data

def run(user_query: str = ""):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    # Load UT data
    df = load_ut_data()

    if "UT%" not in df.columns or "FresherAgeingCategory" not in df.columns:
        st.error("Required columns (UT%, FresherAgeingCategory) not found.")
        return

    df = df[df["FresherAgeingCategory"].notna()]
    df = df[df["UT%"].notna()]
    df = df[df["Status"].notna()]
    df = df[df["Status"].isin(["Billable", "Non Billable"])]

    # Infer year from user_query
    selected_year = None
    if "2024-25" in user_query:
        selected_year = "2024"
    elif "2025-26" in user_query:
        selected_year = "2025"
    if selected_year:
        df = df[df["Year"] == selected_year]

    # Month mapping
    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    df["MonthName"] = df["Month"].astype(int).map(month_map)

    if df.empty:
        st.info("No fresher UT% data available after applying filters.")
        return

    # Pivot data
    pivot_df = df.groupby(["MonthName", "FresherAgeingCategory"])["UT%"].mean().reset_index()
    table_df = pivot_df.pivot(index="MonthName", columns="FresherAgeingCategory", values="UT%").fillna(0)
    table_df = table_df.reset_index()

    ordered_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    table_df["MonthName"] = pd.Categorical(table_df["MonthName"], categories=ordered_months, ordered=True)
    table_df = table_df.sort_values("MonthName")

    # 🔍 Enhanced Key Insights
    st.subheader("🔍 Key Insights")
    insights = []
    for cat in table_df.columns[1:]:
        trend = table_df[cat]
        valid_values = trend[(~trend.isna()) & (trend != 0)]
        if len(valid_values) >= 2:
            first = valid_values.iloc[0]
            last = valid_values.iloc[-1]
            avg = valid_values.mean()
            direction = "↑ Increasing" if last > first else "↓ Decreasing" if last < first else "→ Stable"
            insights.append(f"• {cat}: Avg UT% = {avg:.1f}%, Trend = {direction} ({first:.1f}% → {last:.1f}%)")
    if not insights:
        insights.append("• No meaningful UT% trends detected for fresher categories.")
    st.markdown("\n".join(insights))

    # 📊 Table + Chart
    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        st.subheader("🏋️ Monthly UT% Table")
        display_df = table_df.copy()
        for col in display_df.columns[1:]:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
        st.dataframe(display_df.style.set_table_styles([
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("border", "1px solid #ddd"), ("padding", "5px")]}
        ]), use_container_width=True)

    with col2:
        st.subheader("🌐 UT% Trend by Fresher Category")
        fig, ax = plt.subplots(figsize=(8, 4))
        for cat in table_df.columns[1:]:
            sns.lineplot(data=table_df, x="MonthName", y=cat, label=cat, linewidth=2, ax=ax)
        plt.xlabel("Month")
        plt.ylabel("UT%")
        plt.title("Fresher UT% Trends (Monthly)")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#ccc")
        ax.spines["bottom"].set_color("#ccc")
        plt.grid(False)
        plt.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), borderaxespad=0., fontsize="small")
        st.pyplot(fig)
