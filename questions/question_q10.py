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
    if "2024" in user_query or "2024-25" in user_query:
        selected_year = "2024"
    elif "2025" in user_query or "2025-26" in user_query:
        selected_year = "2025"
    if selected_year:
        df = df[df["Year"] == selected_year]

    # Infer segment from user_query
    possible_segments = df["Segment"].dropna().unique()
    selected_segment = None
    for seg in possible_segments:
        if seg.lower() in user_query.lower():
            selected_segment = seg
            break
    if selected_segment:
        df = df[df["Segment"] == selected_segment]

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

    # 🔍 Key Insights – show top 2 trends
    st.subheader("🔍 Key Insights")
    trends = []
    for cat in table_df.columns[1:]:
        trend = table_df[cat]
        valid = trend[(~trend.isna()) & (trend != 0)]
        if len(valid) >= 2:
            first, last = valid.iloc[0], valid.iloc[-1]
            change = last - first
            trends.append({
                "category": cat,
                "first": first,
                "last": last,
                "change": change,
                "avg": valid.mean(),
                "direction": "↑ Increasing" if change > 0 else "↓ Decreasing" if change < 0 else "→ Stable"
            })
    top_trends = sorted(trends, key=lambda x: abs(x["change"]), reverse=True)[:2]

    if top_trends:
        for t in top_trends:
            st.markdown(f"• **{t['category']}**: Avg UT% = {t['avg']:.1f}%, Trend = {t['direction']} ({t['first']:.1f}% → {t['last']:.1f}%)")
    else:
        st.markdown("• No meaningful UT% trends detected for fresher categories.")

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
