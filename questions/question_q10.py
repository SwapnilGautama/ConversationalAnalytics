# ✅ FILE: questions/question_q10.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from io import BytesIO

def run(prompt=None):
    st.subheader("Fresher UT% Monthly Trends by Bucket")

    # Load data
    df = pd.read_excel("sample_data/LNTData.xlsx")

    # Filter only fresher buckets
    fresher_buckets = [
        "Freshers ET(0-3 Months)",
        "Freshers ET(4-6 Months)",
        "Freshers PGET(0-3 Months)",
        "Freshers ETPremium(0-3 Months)"
    ]
    df = df[df["FresherAgeingCategory"].isin(fresher_buckets)]

    # Filter only billable agents
    df = df[df["Status"] == "Billable"]

    # Ensure necessary columns exist
    if "Month" not in df.columns or "PSNo" not in df.columns:
        st.error("Required columns missing in the data: 'Month' or 'PSNo'")
        return

    # Parse and format month
    df["Month"] = pd.to_datetime(df["Month"])
    df["Month_str"] = df["Month"].dt.strftime("%b %Y")

    # Compute UT% by fresher category
    agg = df.groupby(["Month_str", "FresherAgeingCategory"])["PSNo"].nunique().reset_index()
    agg_total = df.groupby("Month_str")["PSNo"].nunique().reset_index().rename(columns={"PSNo": "Total"})
    merged = pd.merge(agg, agg_total, on="Month_str")
    merged["UT%"] = round(100 * merged["PSNo"] / merged["Total"], 2)
    pivot_df = merged.pivot(index="Month_str", columns="FresherAgeingCategory", values="UT%").fillna(0)
    pivot_df = pivot_df.sort_index()

    # Insight generation
    latest_month = pivot_df.index[-1]
    insights = []
    for bucket in pivot_df.columns:
        values = pivot_df[bucket]
        if len(values) >= 2:
            trend = "increased" if values.iloc[-1] > values.iloc[-2] else "decreased"
            delta = abs(values.iloc[-1] - values.iloc[-2])
            insights.append(f"- **{bucket}** UT% has {trend} to **{values.iloc[-1]}%** (Δ {delta:.1f}%) in {latest_month}")
        else:
            insights.append(f"- **{bucket}** UT% in {latest_month} is **{values.iloc[-1]}%**")

    st.markdown("### 📊 Key Insights")
    for line in insights:
        st.markdown(line)

    # Show Table
    st.markdown("### 📋 Monthly UT% by Fresher Category")
    st.dataframe(pivot_df.style.set_table_styles([
        {"selector": "th, td", "props": [("border", "1px solid lightgrey")]}
    ]))

    # Plot
    st.markdown("### 📈 Trend Chart")
    pastel_palette = sns.color_palette("pastel")
    fig, ax = plt.subplots(figsize=(10, 4))
    for i, column in enumerate(pivot_df.columns):
        ax.plot(pivot_df.index, pivot_df[column], label=column, linewidth=2.5, linestyle='-', 
                color=pastel_palette[i % len(pastel_palette)], marker='o')
    ax.set_ylabel("UT%")
    ax.set_xlabel("Month")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    ax.set_facecolor("white")
    ax.legend(title="Fresher Category")
    sns.despine()
    st.pyplot(fig)
