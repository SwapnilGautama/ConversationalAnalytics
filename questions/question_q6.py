import pandas as pd
import streamlit as st
from kpi_engine.realized_rate import calculate_realized_rate
from dateutil.relativedelta import relativedelta

def run(df_pnl: pd.DataFrame, df_ut: pd.DataFrame):
    st.title("Realized Rate Drop Analysis")

    # Sidebar filters
    segment_filter = st.sidebar.selectbox("Select Segment", options=sorted(df_pnl["Segment"].dropna().unique()))
    threshold = st.sidebar.slider("Drop Threshold ($)", min_value=1, max_value=10, value=5)

    # Apply segment filter
    df_pnl_filtered = df_pnl[df_pnl["Segment"] == segment_filter]

    # Calculate realized rate
    realized_df = calculate_realized_rate(df_pnl_filtered, df_ut)

    if realized_df.empty:
        st.warning("No data available after filtering.")
        return

    # Convert month to quarter
    realized_df["Quarter"] = realized_df["Month"].dt.to_period("Q")

    # Average realized rate per customer per quarter
    quarter_df = (
        realized_df.groupby(["FinalCustomerName", "Quarter"], as_index=False)
        .agg({"Realized_Rate": "mean"})
    )

    # Sort and pivot to compare latest vs previous quarter
    quarter_df.sort_values(["FinalCustomerName", "Quarter"], inplace=True)

    # Get the latest two quarters
    latest_quarters = sorted(quarter_df["Quarter"].unique())[-2:]
    if len(latest_quarters) < 2:
        st.warning("Not enough quarters to compare.")
        return

    q1, q2 = latest_quarters  # e.g., Q4, Q1
    pivot_df = quarter_df[quarter_df["Quarter"].isin([q1, q2])].pivot(index="FinalCustomerName", columns="Quarter", values="Realized_Rate").reset_index()
    pivot_df.columns.name = None  # Clean column name

    # Rename columns
    pivot_df = pivot_df.rename(columns={q1: f"{q1} Rate", q2: f"{q2} Rate"})

    # Calculate difference
    pivot_df["Drop"] = pivot_df[f"{q1} Rate"] - pivot_df[f"{q2} Rate"]

    # Filter where drop > threshold
    result_df = pivot_df[pivot_df["Drop"] > threshold].sort_values("Drop", ascending=False)

    # Show results
    if result_df.empty:
        st.success(f"No accounts had a realized rate drop greater than ${threshold}.")
    else:
        st.markdown(f"### Accounts with Realized Rate Drop > ${threshold}")
        st.dataframe(result_df.style.format({"Drop": "${:,.2f}"}))
