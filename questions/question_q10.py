import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

def run(user_query):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    # Load data
    df = pd.read_excel("sample_data/LNTData.xlsx")
    df = df[df['Status'] == 'Billable']
    df = df.dropna(subset=['FresherAgeingCategory'])

    # Convert Month column
    month_map = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    df["MonthName"] = df["Month"].map(month_map)

    # 🧠 Extract year and segment from chatbot query
    selected_year = None
    selected_segment = None
    try:
        user_query = str(user_query).lower()
    except Exception:
        user_query = ""

    # Match year
    for y in df["Year"].dropna().unique():
        if str(y) in user_query:
            selected_year = y

    # Match segment
    if "Segment" in df.columns:
        for seg in df["Segment"].dropna().unique():
            if str(seg).lower() in user_query:
                selected_segment = seg

    # Show selected filters
    with st.expander("🔍 Filter Applied"):
        st.markdown(f"**Selected Year:** `{selected_year if selected_year else 'All'}`")
        st.markdown(f"**Selected Segment:** `{selected_segment if selected_segment else 'All'}`")

    # Compute UT%
    grouped = df.groupby(["Year", "Month", "MonthName", "Segment", "FresherAgeingCategory"])["Utilization %"].mean().reset_index()
    grouped.rename(columns={"Utilization %": "UT%"}, inplace=True)

    # Apply filters
    pivot_df = grouped.copy()
    if selected_year:
        pivot_df = pivot_df[pivot_df["Year"] == selected_year]
    if selected_segment:
        pivot_df = pivot_df[pivot_df["Segment"] == selected_segment]

    # ➕ Key Insights
    st.subheader("🔍 Key Insights")
    latest_month = pivot_df["Month"].max()
    prev_month = latest_month - 1
    insights = []
    for bucket in pivot_df["FresherAgeingCategory"].unique():
        df_bucket = pivot_df[pivot_df["FresherAgeingCategory"] == bucket]
        avg_ut = df_bucket["UT%"].mean()
        if prev_month in df_bucket["Month"].values and latest_month in df_bucket["Month"].values:
            prev_val = df_bucket[df_bucket["Month"] == prev_month]["UT%"].mean()
            curr_val = df_bucket[df_bucket["Month"] == latest_month]["UT%"].mean()
            trend = "↑ Increasing" if curr_val > prev_val else "↓ Decreasing"
            insights.append(f"**{bucket}**: Avg UT% = {avg_ut:.1f}%, Trend = {trend} ({prev_val:.1f}% → {curr_val:.1f}%)")
        else:
            insights.append(f"**{bucket}**: Avg UT% = {avg_ut:.1f}%")

    for line in insights:
        st.markdown(f"- {line}")

    # 👉 Filter for table
    filtered_table_df = pivot_df.copy()
    if selected_year:
        filtered_table_df = filtered_table_df[filtered_table_df["Year"] == selected_year]
    if selected_segment:
        filtered_table_df = filtered_table_df[filtered_table_df["Segment"] == selected_segment]

    # Prepare UT% summary table
    table_df = filtered_table_df.groupby(["MonthName", "Segment", "FresherAgeingCategory"])["UT%"].mean().reset_index()
    table_df = table_df.pivot_table(index=["MonthName", "Segment"], columns="FresherAgeingCategory", values="UT%", fill_value=0).reset_index()

    # Sort month order
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    table_df["MonthName"] = pd.Categorical(table_df["MonthName"], categories=month_order, ordered=True)
    table_df = table_df.sort_values("MonthName")

    st.subheader("📅 Monthly UT% Table")
    st.dataframe(table_df.style.format("{:.1f}%").set_table_styles(
        [{'selector': 'th', 'props': [('border', '1px solid #ccc')]},
         {'selector': 'td', 'props': [('border', '1px solid #ccc')]}]
    ), use_container_width=True)

    # ➗ Line chart
    st.subheader("📈 UT% Trend by Fresher Category")
    fig, ax = plt.subplots(figsize=(10, 5))
    for cat in pivot_df["FresherAgeingCategory"].unique():
        df_line = pivot_df[pivot_df["FresherAgeingCategory"] == cat]
        df_line = df_line.groupby("MonthName")["UT%"].mean().reindex(month_order)
        ax.plot(df_line.index, df_line.values, label=cat)
    ax.set_ylabel("UT%")
    ax.set_title("Fresher UT% Trends (Monthly)")
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    ax.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig)
