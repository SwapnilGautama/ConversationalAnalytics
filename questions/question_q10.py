import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import re

def run(chat_input):
    st.markdown("## 📊 **Fresher UT% Monthly Trends by Bucket**")

    # --- Load Data ---
    file_path = "LNTData.xlsx"
    df = pd.read_excel('sample_data/LNTData.xlsx')
df.columns = df.columns.str.strip()

    # --- Compute Utilization % ---
    df["TotalBillableHours"] = pd.to_numeric(df["TotalBillableHours"], errors="coerce").fillna(0)
    df["NetAvailableHours"] = pd.to_numeric(df["NetAvailableHours"], errors="coerce").replace(0, 1)
    df["Utilization %"] = (df["TotalBillableHours"] / df["NetAvailableHours"]) * 100

    # --- Add Year_clean and MonthName ---
    df["Year_clean"] = df["Year"].astype(str).str.extract(r"(\d{4})").astype(float)
    df["Month"] = df["Month"].astype(int)
    df["MonthName"] = pd.to_datetime(df["Month"], format="%m").dt.strftime("%b")

    # --- Extract filters from chatbot input ---
    year_filter = None
    segment_filter = None
    match = re.search(r"(20\d{2})", chat_input)
    if match:
        year_filter = int(match.group(1))
    seg_match = re.search(r"\b(?:segment\s+)?([A-Za-z\s&]+)", chat_input, re.IGNORECASE)
    if seg_match:
        for seg in df["Segment"].dropna().unique():
            if seg.lower() in chat_input.lower():
                segment_filter = seg
                break

    # --- Apply filters ---
    st.markdown("### 🔍 Filter Applied")
    if year_filter:
        df = df[df["Year_clean"] == year_filter]
        st.markdown(f"- Year: `{year_filter}`")
    if segment_filter:
        df = df[df["Segment"].str.lower() == segment_filter.lower()]
        st.markdown(f"- Segment: `{segment_filter}`")

    if df.empty:
        st.error("No data found for the selected filters.")
        return

    # --- Prepare data for table/chart ---
    fresher_cats = df["FresherAgeingCategory"].dropna().unique()
    pivot_df = df[df["Status"] == "Billable"].groupby(
        ["MonthName", "Segment", "FresherAgeingCategory"]
    )["Utilization %"].mean().reset_index()

    # --- UT% Trend Table ---
    table_df = pivot_df.pivot_table(index=["MonthName", "Segment"],
                                    columns="FresherAgeingCategory",
                                    values="Utilization %",
                                    fill_value=0).reset_index()

    # --- Insights ---
    st.markdown("### 🔎 **Key Insights**")
    for cat in fresher_cats:
        cat_df = pivot_df[pivot_df["FresherAgeingCategory"] == cat].sort_values("MonthName")
        if cat_df.empty: continue
        start = cat_df["Utilization %"].iloc[0]
        end = cat_df["Utilization %"].iloc[-1]
        trend = "↑ Increasing" if end > start else "↓ Decreasing"
        st.markdown(f"- **{cat}**: Avg UT% = {cat_df['Utilization %'].mean():.1f}%, Trend = {trend} ({start:.1f}% → {end:.1f}%)")

    # --- Table ---
    st.markdown("### 🐣 **Monthly UT% Table**")
    st.dataframe(table_df.style.format("{:.1f}").set_table_styles(
        [{'selector': 'th, td', 'props': [('border', '1px solid lightgrey')]}]
    ))

    # --- Line Chart ---
    st.markdown("### 📈 **UT% Trend by Fresher Category**")
    fig, ax = plt.subplots(figsize=(10, 5))
    for cat in fresher_cats:
        temp = pivot_df[pivot_df["FresherAgeingCategory"] == cat]
        temp = temp.groupby("MonthName")["Utilization %"].mean().reindex(
            ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        )
        ax.plot(temp.index, temp.values, label=cat)
    ax.set_ylabel("UT%")
    ax.set_title("Fresher UT% Trends (Monthly)")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    st.pyplot(fig)
