import pandas as pd
import streamlit as st

def run(realized_rate_threshold=3):
    st.header("Accounts with Significant Realized Rate Drop")

    # Load LNTData (UT) file
    try:
        ut_df = pd.read_excel("sample_data/LNTDataSample.xlsx", engine='openpyxl')
    except:
        st.error("Could not load UT sample file.")
        return

    # Load LnTPnL (P&L) file
    try:
        pnl_df = pd.read_excel("sample_data/LnTPnLSample.xlsx", sheet_name="LnTPnLSample", engine='openpyxl')
    except:
        st.error("Could not load P&L sample file.")
        return

    # Strip and rename columns
    ut_df.columns = ut_df.columns.str.strip()
    pnl_df.columns = pnl_df.columns.str.strip()

    # Preprocess: map column names for consistency
    if 'Company Code' in pnl_df.columns:
        pnl_df.rename(columns={'Company Code': 'Client'}, inplace=True)
    if 'Amount in USD' in pnl_df.columns:
        pnl_df.rename(columns={'Amount in USD': 'Amount'}, inplace=True)
    if 'FinalCustomerName' not in pnl_df.columns and 'Final Customer name' in pnl_df.columns:
        pnl_df.rename(columns={'Final Customer name': 'FinalCustomerName'}, inplace=True)

    if 'FinalCustomerName' not in ut_df.columns and 'Final Customer name' in ut_df.columns:
        ut_df.rename(columns={'Final Customer name': 'FinalCustomerName'}, inplace=True)

    # Ensure Month and Year are present
    if 'Month' not in pnl_df.columns or 'Year' not in pnl_df.columns:
        st.error("Month/Year column missing in P&L data.")
        return
    if 'Month' not in ut_df.columns or 'Year' not in ut_df.columns:
        st.error("Month/Year column missing in UT data.")
        return

    # Filter revenue data from P&L using Group1 condition
    revenue_df = pnl_df[(pnl_df['Group1'].isin(["ONSITE", "OFFSHORE", "INDIRECT REVENUE"]))].copy()
    revenue_df['Quarter'] = pd.PeriodIndex(
        pd.to_datetime(revenue_df['Month'].astype(str) + ' ' + revenue_df['Year'].astype(str), format='%m %Y'),
        freq='Q'
    )
    revenue_grouped = revenue_df.groupby(['FinalCustomerName', 'Quarter'])['Amount'].sum().reset_index()
    revenue_grouped.rename(columns={'Amount': 'Revenue'}, inplace=True)

    # Preprocess UT data for Net Available Hours
    ut_df['Quarter'] = pd.PeriodIndex(
        pd.to_datetime(ut_df['Month'].astype(str) + ' ' + ut_df['Year'].astype(str), format='%m %Y'),
        freq='Q'
    )
    ut_grouped = ut_df.groupby(['FinalCustomerName', 'Quarter'])['Net Available Hrs'].sum().reset_index()

    # Merge Revenue and UT
    merged = pd.merge(revenue_grouped, ut_grouped, on=['FinalCustomerName', 'Quarter'], how='inner')

    # Calculate Realized Rate
    merged['Realized Rate'] = merged['Revenue'] / merged['Net Available Hrs']
    merged = merged.dropna()

    # Sort and identify last two quarters
    available_quarters = sorted(merged['Quarter'].unique())
    if len(available_quarters) < 2:
        st.warning("Not enough quarters for comparison.")
        return
    q_latest, q_previous = available_quarters[-1], available_quarters[-2]

    q_latest_df = merged[merged['Quarter'] == q_latest][['FinalCustomerName', 'Realized Rate']].rename(
        columns={'Realized Rate': 'RR_Latest'})
    q_previous_df = merged[merged['Quarter'] == q_previous][['FinalCustomerName', 'Realized Rate']].rename(
        columns={'Realized Rate': 'RR_Previous'})

    rr_compare = pd.merge(q_latest_df, q_previous_df, on='FinalCustomerName', how='inner')
    rr_compare['Rate Drop'] = rr_compare['RR_Previous'] - rr_compare['RR_Latest']
    rr_compare = rr_compare[rr_compare['Rate Drop'] > realized_rate_threshold]

    # Round values for display
    rr_compare[['RR_Previous', 'RR_Latest', 'Rate Drop']] = rr_compare[['RR_Previous', 'RR_Latest', 'Rate Drop']].round(2)

    st.markdown(f"### Realized Rate Drop > ${realized_rate_threshold}")
    if rr_compare.empty:
        st.info("No clients found with Realized Rate drop greater than threshold.")
    else:
        st.dataframe(rr_compare.sort_values(by='Rate Drop', ascending=False).reset_index(drop=True))

# To allow Streamlit interaction
if __name__ == "__main__":
    import streamlit as st
    threshold = st.slider("Select Realized Rate Drop Threshold ($)", min_value=1, max_value=10, value=3)
    run(realized_rate_threshold=threshold)
