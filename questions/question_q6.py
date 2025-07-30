import pandas as pd
import streamlit as st

def run(realized_rate_threshold=3):
    st.header("Accounts with Significant Realized Rate Drop")

    # Load UT data
    try:
        ut_df = pd.read_excel("sample_data/LNTData.xlsx", engine='openpyxl')
    except:
        st.error("Could not load UT data file.")
        return

    # Load P&L data
    try:
        pnl_df = pd.read_excel("sample_data/LnTPnL.xlsx", sheet_name="LnTPnL", engine='openpyxl')
    except:
        st.error("Could not load P&L data file.")
        return

    # Clean columns
    ut_df.columns = ut_df.columns.str.strip()
    pnl_df.columns = pnl_df.columns.str.strip()

    # Rename common fields
    if 'Final Customer name' in pnl_df.columns:
        pnl_df.rename(columns={'Final Customer name': 'FinalCustomerName'}, inplace=True)
    if 'Final Customer name' in ut_df.columns:
        ut_df.rename(columns={'Final Customer name': 'FinalCustomerName'}, inplace=True)
    if 'Amount in USD' in pnl_df.columns:
        pnl_df.rename(columns={'Amount in USD': 'Amount'}, inplace=True)

    # Fill missing Month/Year columns
    for df, name in [(pnl_df, 'P&L'), (ut_df, 'UT')]:
        if 'Month' not in df.columns or 'Year' not in df.columns:
            st.warning(f"Month or Year column missing in {name} data. Attempting to construct from Month_Year...")
            if 'Month_Year' in df.columns:
                df[['Month', 'Year']] = df['Month_Year'].astype(str).str.split('-', expand=True)
            else:
                st.error(f"{name} data is missing both Month/Year and Month_Year columns.")
                return

        df['Month'] = df['Month'].astype(str).str.zfill(2)
        df['Year'] = df['Year'].astype(str)

    # Create unified Quarter column
    pnl_df['Quarter'] = pd.PeriodIndex(
        pd.to_datetime(pnl_df['Month'] + '-01-' + pnl_df['Year'], format='%m-%d-%Y'),
        freq='Q'
    )
    ut_df['Quarter'] = pd.PeriodIndex(
        pd.to_datetime(ut_df['Month'] + '-01-' + ut_df['Year'], format='%m-%d-%Y'),
        freq='Q'
    )

    # Add segment filter
    segments = sorted(set(pnl_df['Segment'].dropna().unique()) | set(ut_df['Segment'].dropna().unique()))
    selected_segment = st.selectbox("Select Segment (Optional)", ["All"] + segments)

    # Filter by segment if selected
    if selected_segment != "All":
        pnl_df = pnl_df[pnl_df['Segment'] == selected_segment]
        ut_df = ut_df[ut_df['Segment'] == selected_segment]

    # Revenue filtering from Group1
    revenue_df = pnl_df[pnl_df['Group1'].isin(["ONSITE", "OFFSHORE", "INDIRECT REVENUE"])].copy()
    revenue_df = revenue_df.groupby(['FinalCustomerName', 'Quarter'])['Amount'].sum().reset_index()
    revenue_df.rename(columns={'Amount': 'Revenue'}, inplace=True)

    # Aggregate UT
    ut_grouped = ut_df.groupby(['FinalCustomerName', 'Quarter'])['Net Available Hrs'].sum().reset_index()

    # Merge
    merged = pd.merge(revenue_df, ut_grouped, on=['FinalCustomerName', 'Quarter'], how='inner')
    merged['Realized Rate'] = merged['Revenue'] / merged['Net Available Hrs']
    merged = merged.dropna()

    # Compare last two quarters
    quarters = sorted(merged['Quarter'].unique())
    if len(quarters) < 2:
        st.warning("Not enough quarters of data.")
        return

    q1, q2 = quarters[-2], quarters[-1]
    prev_q = merged[merged['Quarter'] == q1][['FinalCustomerName', 'Realized Rate']]
    curr_q = merged[merged['Quarter'] == q2][['FinalCustomerName', 'Realized Rate']]
    prev_q.rename(columns={'Realized Rate': 'Previous RR'}, inplace=True)
    curr_q.rename(columns={'Realized Rate': 'Current RR'}, inplace=True)

    final = pd.merge(prev_q, curr_q, on='FinalCustomerName')
    final['Drop'] = final['Previous RR'] - final['Current RR']
    final = final[final['Drop'] > realized_rate_threshold]
    final = final.round(2)

    st.markdown(f"### Realized Rate Drop > ${realized_rate_threshold} (from {q1} to {q2})")
    if final.empty:
        st.info("No significant realized rate drop found.")
    else:
        st.dataframe(final.sort_values(by='Drop', ascending=False).reset_index(drop=True))

# For Streamlit interface
if __name__ == "__main__":
    threshold = st.slider("Realized Rate Drop Threshold ($)", 1, 10, 3)
    run(realized_rate_threshold=threshold)
