import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from io import BytesIO

def run(prompt=None):
    st.subheader("Fresher UT% Monthly Trends by Bucket")

    # Load data from correct path
    df = pd.read_excel("sample_data/LNTData.xlsx")

    # Filter only relevant fresher categories
    fresher_buckets = [
        "Freshers ET(0-3 Months)",
        "Freshers ET(4-6 Months)",
        "Freshers PGET(0-3 Months)",
        "Freshers ETPremium(0-3 Months)"
    ]
    df = df[df["FresherAgeingCategory"].isin(fresher_buckets)]

    # Convert month and extract as string
    df["Month"] = pd.to_datetime(df["Month"], format="%m", errors="coerce")
    df["Month_str"] = df["Month"].dt.strftime("%b %Y")

    # Segment multiselect for filtering
    segments = sorted(df["Segment"].dropna().unique())
    selected_segments = st.multiselect("Filter by Segment", segments, default=segments)

    if selected_segments:
        df = df[df["Segment"].isin(selected_segments)]

    # Calculate UT%
    df["NetAvailableHours"] = pd.to_numeric(df["NetAvailableHours"], errors="coerce")
    df["TotalBillableHours"] = pd.to_numeric(df["TotalBillableHours"], errors="coerce")
    df["UT%"] = (df["TotalBillableHours"] / df["NetAvailableHours"]) * 100

    # Grouped by month and fresher category
    grouped = df.groupby(["Month_str", "FresherAgeingCategory"]).agg({
        "PSNo": "nunique",  # Count of unique agents
        "NetAvailableHours": "sum",
        "TotalBillableHours": "sum",
        "UT%": "mean"
    }).reset_index()

    grouped.rename(columns={
        "PSNo": "Unique Freshers",
        "NetAvailableHours": "Total Available Hrs",
        "TotalBillableHours": "Total Billable Hrs"
    }, inplace=True)

    # Pivoted table view
    pivot_table = grouped.pivot(index="Month_str", columns="FresherAgeingCategory", values="UT%").fillna(0)
    styled_table = pivot_table.style.format("{:.1f}%").set_properties(**{
        'border': '1px solid lightgrey',
        'color': 'black'
    })

    # Plot
    pastel_palette = sns.color_palette("pastel")
    fig, ax = plt.subplots(figsize=(10, 4))
    pivot_table.plot(ax=ax, marker="o", linewidth=2, palette=pastel_palette)
    ax.set_title("Monthly UT% Trend by Fresher Bucket")
    ax.set_ylabel("UT%")
    ax.set_xlabel("Month")
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
    ax.legend(title="Fresher Category", bbox_to_anchor=(1.05, 1), loc='upper left')

    # Layout: Table and Chart side-by-side
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### UT% Table")
        st.dataframe(styled_table, use_container_width=True)
    with col2:
        st.pyplot(fig)

    # Export option
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    st.download_button(
        label="📥 Download Chart as PNG",
        data=buffer.getvalue(),
        file_name="fresher_ut_trend.png",
        mime="image/png"
    )
