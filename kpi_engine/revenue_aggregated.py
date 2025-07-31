import pandas as pd

def get_revenue_aggregated(pnl_path):
    df = pd.read_excel(pnl_path)

    df.columns = df.columns.str.strip()
    df = df[df['Type'].str.lower() == 'revenue']

    df['Segment'] = df.get('Segment', 'Unknown')
    df['BU'] = df.get('Exec DG', 'Unknown')
    df['DU'] = df.get('Exec DU', 'Unknown')

    # Ensure Month column is integer
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    
    df['Month'] = df['Month'].dt.month

    # Map to month name
    df['Month'] = df['Month'].map({
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    })

    grouped = df.groupby(['FinalCustomerName', 'Segment', 'BU', 'DU', 'Month'])['Amount in USD'].sum().reset_index()
    grouped = grouped.rename(columns={'Amount in USD': 'Revenue'})
    return grouped
