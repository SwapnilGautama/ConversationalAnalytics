import pandas as pd

def calculate_realized_rate(pnl_df: pd.DataFrame, ut_df: pd.DataFrame,
                             segment: str = None,
                             customer: str = None,
                             quarter: str = None) -> pd.DataFrame:
    """
    Calculate Realized Rate = Revenue / Available Hours

    Filters:
        - Group1 must be in ['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']
        - Type must be 'Revenue'

    Optional filters:
        - segment: Filter by Segment
        - customer: Filter by FinalCustomerName
        - quarter: Filter by Quarter (e.g. '2024Q4')
    """

    # Prepare P&L data
    pnl_df = pnl_df.copy()
    pnl_df['Month'] = pd.to_datetime(pnl_df['Month'], errors='coerce')
    pnl_df['Quarter'] = pnl_df['Month'].dt.to_period('Q').astype(str)

    # Filter revenue
    revenue_df = pnl_df[
        (pnl_df['Type'].str.lower() == 'revenue') &
        (pnl_df['Group1'].str.upper().isin(['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']))
    ].copy()

    # Apply optional filters
    if segment:
        revenue_df = revenue_df[revenue_df['Segment'].str.lower() == segment.lower()]
    if customer:
        revenue_df = revenue_df[revenue_df['FinalCustomerName'].str.lower() == customer.lower()]
    if quarter:
        revenue_df = revenue_df[revenue_df['Quarter'] == quarter]

    rev_grouped = revenue_df.groupby(['FinalCustomerName', 'Quarter'])['Amount in USD'].sum().reset_index()
    rev_grouped.rename(columns={'Amount in USD': 'Revenue'}, inplace=True)

    # Prepare UT data
    ut_df = ut_df.copy()
    ut_df['Month'] = pd.to_datetime(ut_df['Month'], errors='coerce')
    ut_df['Quarter'] = ut_df['Month'].dt.to_period('Q').astype(str)

    if segment:
        ut_df = ut_df[ut_df['Segment'].str.lower() == segment.lower()]
    if customer:
        ut_df = ut_df[ut_df['FinalCustomerName'].str.lower() == customer.lower()]
    if quarter:
        ut_df = ut_df[ut_df['Quarter'] == quarter]

    ut_grouped = ut_df.groupby(['FinalCustomerName', 'Quarter'])['Net Available Hrs'].sum().reset_index()
    ut_grouped.rename(columns={'Net Available Hrs': 'AvailableHrs'}, inplace=True)

    # Merge and calculate
    merged = pd.merge(rev_grouped, ut_grouped, on=['FinalCustomerName', 'Quarter'], how='inner')
    merged['RealizedRate'] = merged['Revenue'] / merged['AvailableHrs']

    return merged
