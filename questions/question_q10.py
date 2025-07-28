import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from io import BytesIO

def run(prompt=None):
    st.subheader("Fresher UT% Monthly Trends by Bucket")

    # ✅ Load data from correct folder
    df = pd.read_excel("sample_data/LNTData.xlsx")

    # Filter only relevant fresher categories
    fresher_buckets = [
        "Freshers ET(0-3 Months)",
        "Freshers ET(4-6 Months)",
        "Freshers PGET(0-3 Months)",
        "Freshers ETPremium(0-3 Months)"
    ]
    df = df[df["FresherAgeingCategory"].isin(fresher_buckets)]

    # Clean and format month
    df["Month"] = pd.to_datetime(df["Month"])
    df["Month_str"] = df["Month"].dt.strftime("%b %Y")

    # ✅ Segment filter embedded in table
    segments = df["Segment"].dropna().unique().tolist()
    selected_segment = st.multiselect("Filter by Segment", segments, default=segments)
    df = df[df["Segment"].isin(selected_segment)]

    # Grouping and calculating UT%
    summary = df.groupby(["Month_str", "FresherAgeingCategory"]).agg(
        Total_Resources=("Resource Name", "count"),
        Total_Billable=("IsBillable", lambda x: (x == "Yes").sum())
    ).reset_index()
    summary["UT%"] = (summary["Total_Billable"] / summary["Total_Resources"]) * 100

    # Pivot table for display
    pivot_table = summary.pivot(index="Month_str", columns="FresherAgeingCategory", values="UT%").fillna(0)
    pivot_table = pivot_table.sort_index()

    # Display table with soft grey borders
    st.markdown("### UT% Table by Fresher Category")
    st.dataframe(
        pivot_table.style.format("{:.1f}").set_table_styles(
            [{"selector": "th, td", "props": [("border", "1px solid lightgrey")]}]
        )
    )

    # Line chart with pastel colors
    st.markdown("### Monthly UT% Trend Line Chart")
    fig, ax = plt.subplots(figsize=(10, 5))
    pastel_palette = sns.color_palette("pastel", len(pivot_table.columns))
    pivot_table.plot(kind="line", ax=ax, linewidth=2, marker="o", color=pastel_palette)

    ax.set_ylabel("Utilization %")
    ax.set_xlabel("Month")
    ax.set_title("Monthly UT% Trend by Fresher Bucket")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('lightgrey')
    ax.spines['left'].set_color('lightgrey')
    ax.grid(False)
    ax.legend(title="Fresher Bucket", loc="lower center", bbox_to_anchor=(0.5, -0.4), ncol=2)
    plt.xticks(rotation=45)

    # Smoothen the lines
    for line in ax.get_lines():
        line.set_linestyle('-')
        line.set_linewidth(1.5)

    st.pyplot(fig)
