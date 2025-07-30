import pandas as pd
import streamlit as st
from kpi_engine.realized_rate import calculate_realized_rate

# Load data
def load_pnl_data():
    return pd.read_excel("sample_data/LnTPnL.xlsx")

def load_utilization_data():
    return pd.read_excel("sample_data/LNTData.xlsx")

def run():
    # Load datasets
    df_pnl = load_pnl_data()
    df_ut = load_utilization_data()

    # Standardize column names
    df_pnl.rename(columns={"Company code": "Company_Code"}, inplace=True)
    df_ut.rename(columns={"Company code": "Company_Code"}, inplace=True)

    # Calculate realized rate per account
    df_realized = calculate_realized_rate(df_pnl, df_ut)

    # Filters
    st.sidebar.header("🧩 Filters")
    segment_filter = st.sidebar.selectbox("Select Segment", options=[""] + sorted(df_ut["Segment"].dropna().unique().tolist()))
    threshold = st.sidebar.slider("🎯 Realized Rate Threshold (USD/hr)", 0.0, 100.0, 30.0, step=1.0)

    # Merge to get segment data
    if "Segment" in df_ut.columns:
        df_realized = df_realized.merge(df_ut[["Company_Code", "Segment"]].drop_duplicates(), on="Company_Code", how="left")

    # Apply filters
    if segment_filter:
        df_realized = df_realized[df_realized["Segment"] == segment_filter]

    df_below_threshold = df_realized[df_realized["Realized_Rate"] < threshold]

    st.markdown("### 🔍 Accounts with Realized Rate below Threshold")
    if df_below_threshold.empty:
        st.success("✅ No accounts found below the threshold.")
    else:
        st.dataframe(df_below_threshold.sort_values("Realized_Rate"))
