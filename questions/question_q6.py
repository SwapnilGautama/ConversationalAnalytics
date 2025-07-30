import pandas as pd
import streamlit as st

def run(realized_rate_threshold=3):
    st.header("Accounts with Significant Realized Rate Drop")

    # Load UT file
    try:
        ut_df = pd.read_excel("sample_data/LNTData.xlsx", engine='openpyxl')
    except:
        st.error("Could not load UT data file.")
        return

    # Load P&L file
    try:
        pnl_df = pd.read_excel("sample_data/LnTPnL.xlsx", sheet_name="LnTPnL", engine='openpyxl')
    except:
        st.error("Could not load P&L data file.")
        return

    # Clean columns
    ut_df.columns = ut_df.columns.str.strip()
    pnl_df.columns = pnl_df.columns.str.strip()

    # Rename for consistency
    if 'Final Customer name' in pnl_df.columns:
        pnl_df.rename(columns={'Final Customer name': 'FinalCustomerName'}, inplace=True)
    if 'Final Customer name' in ut_df.columns:
        ut_df.rename(columns={'Final Customer name': 'FinalCustomerName'}, inplace=True)

    if 'Amount in USD' in pnl_df.columns:
        pnl_df.rename(columns={'Amount in USD': 'Amount'}, inplace=True)
    if 'Company Code' in pnl_df.columns:
        pnl_df.rename(columns={'Company Code': 'Client'}, inplace=True)

    # Month/Year checks
    if 'Month' not in pnl_df.columns or 'Year' not in pnl_df.columns:
        st.error("Month/Year column missing in P&L data.")
        return
    if 'Month' not in ut_df.columns or 'Year' not in ut_df.columns:
        st.error("Month/Year column missing in UT data.")
        return

    # Revenue Filter (Group1: ONSITE, OFFSHORE, INDIRECT REVENUE)
    revenue_df = pnl_df[pnl_df['Group1'].isin(["ONSITE", "OFFSHORE", "INDIRECT REVENUE"])].copy()
    revenue_df['Quarter'] = pd.PeriodIndex(
        pd.to_datetime(revenue_df['Month'].astype(str) + '-' + revenue_df['Year'].astype(str), format='%m-%Y'),
        freq='Q'
    )
    revenue_grouped = revenue_df.groupby(['FinalCustomerName', 'Quarter'])['Amount'].sum().reset_index()
    revenue_grouped.rename(columns={'Amount': 'Revenue'}, inplace=True)

    # UT preprocessing
    ut_df['Quarter'] = pd.PeriodIndex(
        pd.to_datetime(ut_df['Month'].astype(str) + '-' + ut_df['Year'].astype(str), format='%m-%Y'),
        freq='Q'
    )
    ut_grouped = ut_df.groupby(['FinalCustomerName', 'Quarter'])['Net Available Hrs'].sum().reset_index()

    # Merge Revenue + UT
    merged = pd.merge(revenue_grouped, ut_grouped, on=['FinalCustomerName', 'Quarter'], how='inner')
    merged['Realized Rate'] = merged['Revenue'] / merged['Net Available Hrs']
    merged = merged.dropna()

    # Get last two quarters
    available_quarters = sorted(merged['Quarter'].unique())
    if len(available_quarters) < 2:
        st.warning("Not enough quarters for comparison.")
        return

    q_latest, q_previous = available_quarters[-1], available_quarters[-2]
    q_latest_df = merged[merged['Quarter'] == q_latest][['FinalCustomerName', 'Realized Rate']].rename(
        columns={'Realized Rate': 'RR_Latest'})
    q_prev_df = merged[merged['Quarter'] == q_previous][['FinalCustomerName', 'Realized Rate']].rename(
        columns={'Realized Rate': 'RR_Previous'})

    compare_df = pd.merge(q_prev_df, q_latest_df, on='FinalCustomerName')
    compare_df['Rate Drop'] = compare_df['RR_Previous'] - compare_df['RR_Latest']
    compare_df = compare_df[compare_df['Rate Drop'] > realized_rate_threshold]

    compare_df[['RR_Previous', 'RR_Latest', 'Rate Drop']] = compare_df[['RR_Previous', 'RR_Latest', 'Rate Drop']].round(2)

    st.markdown(f"### Realized Rate Drop > ${realized_rate_threshold}")
    if compare_df.empty:
        st.info("No clients found with significant drop.")
    else:
        st.dataframe(compare_df.sort_values(by='Rate Drop', ascending=False).reset_index(drop=True))

# For Streamlit UI
if __name__ == "__main__":
    threshold = st.slider("Select Realized Rate Drop Threshold ($)", min_value=1, max_value=10, value=3)
    run(realized_rate_threshold=threshold)
