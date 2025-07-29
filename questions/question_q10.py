import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run(user_query: str = ""):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    # Load raw LNTData
    df = pd.read_excel("LNTData.xlsx")

    # Map year field to numeric
    df["Year"] = df["Year"].map({"2024-25": "2024", "2025-26": "2025"})

    # Infer year & segment from user query
    selected_year = None
    if "2024" in user_query:
        selected_year = "2024"
    elif "2025" in user_query:
        selected_year = "2025"

    selected_segment = None
    for segment in df["Segment"].dropna().unique():
        if str(segment).lower() in user_query.lower():
            selected_segment = segment
            break

    if selected_year:
        df = df[df["Year"] == selected_year]
    if selected_segment:
        df = df[df["Segment"] == selected_segment]

    # Filter to valid fresher data
    df = df[df["FresherAgeingCategory"].notna()]
    df = df[df["Status"].isin(["Billable", "Non Billable"])]

    # Compute UT% inline (as in utilization.py): UT% = Billable / (Billable + Non-Billable)
    df["Headcount"] = 1
    agg_df = df.groupby(["Year", "Month", "FresherAgeingCategory", "Status", "Segment"]).agg({"Headcount": "sum"}).reset_index()
    pivot_df = agg_df.pivot_table(index=["Year", "Month", "FresherAgeingCategory", "Segment"],
                                  columns="Status", values="Headcount", fill_value=0).reset_index()
    pivot_df["UT%"] = (pivot_df["Billable"] / (pivot_df["Billable"] + pivot_df["Non Billable"])) * 100

    # Month name mapping
    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    pivot_df["MonthName"] = pivot_df["Month"].map(month_map)
    pivot_df = pivot_df[pivot_df["UT%"].notna()]

    if pivot_df.empty:
        st.info("No fresher UT% data available after applying filters.")
        return

    # Table prep
    table_df = pivot_df.groupby(["MonthName", "Segment", "FresherAgeingCategory"])["UT%"].mean().reset_index()
    table_df = table_df.pivot_table(index=["MonthName", "Segment"], columns="FresherAgeingCategory", values="UT%", fill_value=0).reset_index()

    # Sort by month
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    table_df["MonthName"] = pd.Categorical(table_df["MonthName"], categories=month_order, ordered=True)
    table_df = table_df.sort_values("MonthName")

    # Insights section
    st.subheader("🔍 Key Insights")
    trends = []
    for col in table_df.columns[2:]:
        values = table_df[col]
        values = values[values != 0]
        if len(values) >= 2:
            change = values.iloc[-1] - values.iloc[0]
            trend_type = "↑ Increasing" if change > 0 else "↓ Decreasing" if change < 0 else "→ Stable"
            trends.append((col, trend_type, values.mean(), values.iloc[0], values.iloc[-1]))

    if trends:
        sorted_trends = sorted(trends, key=lambda x: abs(x[4] - x[3]), reverse=True)[:2]
        for cat, trend, avg, first, last in sorted_trends:
            st.markdown(f"• **{cat}**: Avg UT% = {avg:.1f}%, Trend = {trend} ({first:.1f}% → {last:.1f}%)")
    else:
        st.markdown("• No significant fresher UT% trends detected.")

    # 📊 Table and Chart side by side
    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        st.subheader("🏋️ Monthly UT% Table")
        display_df = table_df.copy()
        for col in display_df.columns[2:]:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
        st.dataframe(display_df.style.set_table_styles([
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("border", "1px solid #ccc"), ("padding", "4px")]}
        ]), use_container_width=True)

    with col2:
        st.subheader("🌐 UT% Trend by Fresher Category")
        fig, ax = plt.subplots(figsize=(8, 4))
        for cat in table_df.columns[2:]:
            sns.lineplot(data=table_df, x="MonthName", y=cat, label=cat, linewidth=2, ax=ax)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#ccc")
        ax.spines["bottom"].set_color("#ccc")
        plt.grid(False)
        plt.xlabel("Month")
        plt.ylabel("UT%")
        plt.title("Fresher UT% Trends (Monthly)")
        plt.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize="small")
        st.pyplot(fig)
