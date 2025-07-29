import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import re

def run(df, chat_input):
    st.markdown("## 📊 **Fresher UT% Monthly Trends by Bucket**")

    # --- Preprocess Data ---
    df["TotalBillableHours"] = pd.to_numeric(df["TotalBillableHours"], errors="coerce").fillna(0)
    df["NetAvailableHours"] = pd.to_numeric(df["NetAvailableHours"], errors="coerce").replace(0, 1)
    df["Utilization %"] = (df["TotalBillableHours"] / df["NetAvailableHours"]) * 100

    df["Year_clean"] = df["Year"].astype(str).str.extract(r"(\d{4})").astype(float)
    df["Month"] = df["Month"].astype(int)
    df["MonthName"] = pd.to_datetime(df["Month"], format="%m").dt.strftime("%b")

    # --- Extract filters from chatbot ---
    year_filter = None
    segment_filter = None

    match = re.search(r"(20\d{2})", chat_input)
    if match:
        year_filter = int(match.group(1))

    possible_segments = df["Segment"].dropna().unique()
    for seg in possible_segments:
        if seg.lower() in chat_input.lower():
            segment_filter = seg
            break

    # --- Apply filters ---
    st.markdown("### 🔍 Filters Applied")
    if year_filter:
        df = df[df["Year_clean"] == year_filter]
        st.markdown(f"- Year: `{year_filter}`")
    if segment_filter:
        df = df[df["Segment"].str.lower() == segment_filter.lower()]
        st.markdown(f"- Segment: `{segment_filter}`")

    if df.empty:
        st.error("No data found for the selected filters.")
        return

    # --- Prepare Data for Visualization ---
    fresher_cats = df["FresherAgeingCategory"].dropna().unique()
    pivot_df = df[df["Status"] == "Billable"].groupby(
        ["MonthName", "Segment", "FresherAgeingCategory"]
    )["Utilization %"].mean().reset_index()

    # --- Table ---
    table_df = pivot_df.pivot_table(index=["MonthName", "Segment"],
                                    columns="FresherAgeingCategory",
                                    values="Utilization %",
                                    fill_value=0).reset_index()

    st.markdown("### 🔎 **Key Insights**")
    top_2 = []
    for cat in fresher_cats:
        cat_df = pivot_df[pivot_df["FresherAgeingCategory"] == cat].sort_values("MonthName")
        if cat_df.empty: continue
        start = cat_df["Utilization %"].iloc[0]
        end = cat_df["Utilization %"].iloc[-1]
        trend = "↑ Increasing" if end > start else "↓ Decreasing"
        avg_ut = cat_df["Utilization %"].mean()
        top_2.append((cat, avg_ut, trend, start, end))
    top_2 = sorted(top_2, key=lambda x: x[1], reverse=True)[:2]
    for cat, avg_ut, trend, start, end in top_2:
        st.markdown(f"- **{cat}**: Avg UT% = {avg_ut:.1f}%, Trend = {trend} ({start:.1f}% → {end:.1f}%)")

    # --- Styled Table ---
    st.markdown("### 🐣 **Monthly UT% Table**")
    st.dataframe(table_df.style.format("{:.1f}%").set_table_styles(
        [{'selector': 'th, td', 'props': [('border', '1px solid lightgrey')]}]
    ))

    # --- Line Chart ---
    st.markdown("### 📈 **UT% Trend by Fresher Category**")
    fig, ax = plt.subplots(figsize=(10, 5))
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for cat in fresher_cats:
        temp = pivot_df[pivot_df["FresherAgeingCategory"] == cat]
        temp = temp.groupby("MonthName")["Utilization %"].mean().reindex(month_order)
        ax.plot(temp.index, temp.values, label=cat)

    ax.set_ylabel("UT%")
    ax.set_title("Fresher UT% Trends (Monthly)")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('lightgrey')
    ax.spines['bottom'].set_color('lightgrey')
    ax.grid(False)
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    st.pyplot(fig)
