import pandas as pd

def get_revenue_aggregated(pnl_path):
    df = pd.read_excel(pnl_path)
    df.columns = df.columns.str.strip()

    df = df[df['Type'] == 'Revenue']
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce').dt.month
    df['Month'] = df['Month'].map({
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    })

    if 'Segment' not in df.columns:
        df['Segment'] = 'Unknown'
    if 'Exec DG' in df.columns:
        df['BU'] = df['Exec DG']
    else:
        df['BU'] = 'Unknown'
    if 'Exec DU' in df.columns:
        df['DU'] = df['Exec DU']
    else:
        df['DU'] = 'Unknown'

    grouped = df.groupby(['FinalCustomerName', 'Segment', 'BU', 'DU', 'Month'])['Amount in USD'].sum().reset_index()
    grouped = grouped.rename(columns={'Amount in USD': 'Revenue'})
    return grouped
