import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from kpi_engine.revenue_aggregated import revenue_aggregated
from kpi_engine.headcount_aggregated import headcount_aggregated

def run(df_pnl: pd.DataFrame, df_ut: pd.DataFrame):
    st.header("Revenue per Person Analysis by Account")

    # Load revenue and headcount aggregates
    df_rev = revenue_aggregated(df_pnl)
    df_hc = headcount_aggregated(df_ut)

    # Merge on keys
    df_merged = pd.merge(
        df_rev,
        df_hc,
        on=["FinalCustomerName", "Segment", "Year", "Month_Num"],
        how="inner"
    )

    # Calculate Revenue per Person
    df_merged["Revenue_per_Person"] = (
        df_merged["Total_Revenue_USD"] / df_merged["Distinct_Headcount"]
    )

    # Format Month Name
    df_merged["Month_Name"] = pd.to_datetime(df_merged["Month_Num"], format="%m").dt.strftime("%b")

    # UI: Segment filter
    segments = sorted(df_merged["Segment"].dropna().unique())
    selected_segment = st.selectbox("Select Segment", options=segments)

    df_segment = df_merged[df_merged["Segment"] == selected_segment]

    # Output Table
    table = df_segment[[
        "FinalCustomerName", "Year", "Month_Name",
        "Total_Revenue_USD", "Distinct_Headcount", "Revenue_per_Person"
    ]].sort_values(["FinalCustomerName", "Year", "Month_Name"])

    table_display = table.rename(columns={
        "FinalCustomerName": "Account",
        "Total_Revenue_USD": "Revenue ($)",
        "Distinct_Headcount": "Headcount",
        "Revenue_per_Person": "Revenue per Person ($)",
        "Month_Name": "Month"
    })

    st.subheader("Revenue per Person Table")
    st.dataframe(table_display.style
        .format({
            "Revenue ($)": "{:,.0f}",
            "Headcount": "{:,.0f}",
            "Revenue per Person ($)": "{:,.0f}"
        })
        .set_properties(**{"border-color": "#ccc", "border-width": "1px", "border-style": "solid"})
    )

    # Plot: Line chart of Revenue per Person by Month (avg across accounts)
    st.subheader("Monthly Revenue per Person Trend (Average Across Accounts)")
    df_plot = (
        df_segment.groupby(["Year", "Month_Num"], as_index=False)["Revenue_per_Person"]
        .mean()
    )
    df_plot["Month_Label"] = pd.to_datetime(df_plot["Month_Num"], format="%m").dt.strftime("%b")
    df_plot["Label"] = df_plot["Month_Label"] + " " + df_plot["Year"].astype(str)

    plt.figure(figsize=(10, 5))
    plt.plot(df_plot["Label"], df_plot["Revenue_per_Person"], marker="o")
    plt.xticks(rotation=45)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.xlabel("Month")
    plt.ylabel("Avg Revenue per Person ($)")
    plt.tight_layout()
    st.pyplot(plt)
