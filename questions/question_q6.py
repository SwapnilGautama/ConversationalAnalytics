import pandas as pd
import streamlit as st
import re

def run(pnl_df: pd.DataFrame, ut_df: pd.DataFrame):
    st.markdown("## Q6. Realized Rate Analysis")

    # Left filter pane
    with st.sidebar:
        st.markdown("### 🛠️ Filters")
        segment = st.selectbox("Select Segment (optional)", options=[""] + sorted(pnl_df['Segment'].dropna().unique().tolist()))
        rate_threshold = st.slider("Realized Rate Threshold", min_value=0.0, max_value=50.0, value=5.0, step=0.5)

    pnl_df.columns = pnl_df.columns.str.strip()
    ut_df.columns = ut_df.columns.str.strip()

    # Dynamically identify the amount column
    amount_col = next((col for col in pnl_df.columns if col.lower().strip() in ['amount', 'amount in usd', 'amountinusd']), None)
    if not amount_col:
        st.error("❌ Column not found: Amount in USD")
        return

    # Parse month and quarter
    pnl_df['Month'] = pd.to_datetime(pnl_df['Month'], errors='coerce')
    pnl_df['Quarter'] = pnl_df['Month'].dt.to_period('Q').astype(str)

    # Filter revenue
    revenue_df = pnl_df[
        (pnl_df['Type'].str.lower() == 'revenue') &
        (pnl_df['Group1'].str.upper().isin(['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']))
    ].copy()

    if segment:
        revenue_df = revenue_df[revenue_df['Segment'].str.lower() == segment.lower()]

    rev_grouped = revenue_df.groupby(['FinalCustomerName', 'Quarter'])[amount_col].sum().reset_index()
    rev_grouped.rename(columns={amount_col: 'Revenue'}, inplace=True)

    # UT data
    ut_df['Month'] = pd.to_datetime(ut_df['Month'], errors='coerce')
    ut_df['Quarter'] = ut_df['Month'].dt.to_period('Q').astype(str)
    if segment:
        ut_df = ut_df[ut_df['Segment'].str.lower() == segment.lower()]

    ut_grouped = ut_df.groupby(['FinalCustomerName', 'Quarter'])['Net Available Hrs'].sum().reset_index()
    ut_grouped.rename(columns={'Net Available Hrs': 'AvailableHrs'}, inplace=True)

    # Merge and compute Realized Rate
    merged = pd.merge(rev_grouped, ut_grouped, on=['FinalCustomerName', 'Quarter'], how='inner')
    merged['RealizedRate'] = merged['Revenue'] / merged['AvailableHrs']

    filtered = merged[merged['RealizedRate'] < rate_threshold]

    st.markdown(f"### 🔍 Accounts with Realized Rate below {rate_threshold}")
    if filtered.empty:
        st.success("✅ No accounts found below the threshold.")
    else:
        st.dataframe(filtered.sort_values(by='RealizedRate'), use_container_width=True)
