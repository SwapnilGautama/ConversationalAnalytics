import pandas as pd
import streamlit as st
from kpi_engine.realized_rate import calculate_realized_rate  # ✅ Using KPI engine

def load_pnl_data():
    return pd.read_excel("sample_data/LnTPnL.xlsx")

def load_utilization_data():
    return pd.read_excel("sample_data/LNTData.xlsx")

def run():
    # Load data
    df_pnl = load_pnl_data()
    df_ut = load_utilization_data()

    # Standardize column names
    df_pnl.rename(columns={"Company code": "Company_Code"}, inplace=True)
    df_ut.rename(columns={"Company code": "Company_Code"}, inplace=True)

    # Apply Realized Rate KPI logic
    df_realized = calculate_realized_rate(df_pnl, df_ut)

    # Filters
    st.sidebar.header("🛠 Filters")
    segment_filter = st.sidebar.text_input("Enter Segment (optional)", "")
    rate_threshold = st.sidebar.slider("Realized Rate Threshold", 0.0, 50.0, 5.0, step=0.5)

    # Apply segment filter if present
    if segment_filter:
        df_realized = df_realized[df_realized["Segment"].str.lower() == segment_filter.lower()]

    # Apply threshold
    filtered_df = df_realized[df_realized["Realized Rate"] < rate_threshold]

    # Output accounts
    accounts_below_threshold = filtered_df["Company_Code"].unique()

    st.markdown("### Q6. Realized Rate Analysis")
    if len(accounts_below_threshold) == 0:
        st.success("✅ No accounts below the threshold.")
    else:
        st.warning("⚠️ Accounts with Realized Rate below threshold:")
        st.dataframe(pd.DataFrame(accounts_below_threshold, columns=["Company_Code"]))
