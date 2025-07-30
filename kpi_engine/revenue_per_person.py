import pandas as pd

def calculate_revenue_per_person(pnl_df: pd.DataFrame, ut_df: pd.DataFrame,
                                  segment: str = None,
                                  customer: str = None,
                                  quarter: str = None) -> pd.DataFrame:
    """
    Revenue per Person = Revenue / Total Billable Headcount

    Revenue filtered using:
        - Type == 'Revenue'
        - Group1 in ['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']

    Headcount filtered using:
        - Status == 'Billable'

    Optional filters:
        - segment
        - customer
        - quarter (format: '2024Q4')
    """
    # Prepare P&L
    pnl_df = pnl_df.copy()
    pnl_df['Month'] = pd.to_datetime(pnl_df['Month'], errors='coerce')
    pnl_df['Quarter'] = pnl_df['Month'].dt.to_period('Q').astype(str)

    pnl_df = pnl_df[(pnl_df['Type'].str.lower() == 'revenue') &
                    (pnl_df['Group1'].str.upper().isin(['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']))]

    if segment:
        pnl_df = pnl_df[pnl_df['Segment'].str.lower() == segment.lower()]
    if customer:
        pnl_df = pnl_df[pnl_df['FinalCustomerName'].str.lower() == customer.lower()]
    if quarter:
        pnl_df = pnl_df[pnl_df['Quarter'] == quarter]

    rev_grouped = pnl_df.groupby(['FinalCustomerName', 'Quarter'])['Amount in USD'].sum().reset_index()
    rev_grouped.rename(columns={'Amount in USD': 'Revenue'}, inplace=True)

    # Prepare UT headcount
    ut_df = ut_df.copy()
    ut_df['Month'] = pd.to_datetime(ut_df['Month'], errors='coerce')
    ut_df['Quarter'] = ut_df['Month'].dt.to_period('Q').astype(str)

    ut_df = ut_df[ut_df['Status'].str.lower() == 'billable']

    if segment:
        ut_df = ut_df[ut_df['Segment'].str.lower() == segment.lower()]
    if customer:
        ut_df = ut_df[ut_df['FinalCustomerName'].str.lower() == customer.lower()]
    if quarter:
        ut_df = ut_df[ut_df['Quarter'] == quarter]

    hc_grouped = ut_df.groupby(['FinalCustomerName', 'Quarter'])['PSNo'].nunique().reset_index()
    hc_grouped.rename(columns={'PSNo': 'BillableHeadcount'}, inplace=True)

    # Merge and calculate
    merged = pd.merge(rev_grouped, hc_grouped, on=['FinalCustomerName', 'Quarter'], how='inner')
    merged['RevenuePerPerson'] = merged['Revenue'] / merged['BillableHeadcount']

    return merged
