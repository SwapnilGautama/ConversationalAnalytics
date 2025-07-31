import pandas as pd

def get_revenue_aggregated(pnl_path):
    df = pd.read_excel(pnl_path)

    df.columns = df.columns.str.strip()
    amount_col = next((col for col in df.columns if col.lower() in ['amount in usd', 'amount', 'amountinusd']), None)

    if amount_col is None or 'Month' not in df.columns:
        return pd.DataFrame()

    df['Month'] = df['Month'].astype(int).map({
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    })

    df['Segment'] = df.get('Segment', 'Unknown')
    df['BU'] = df.get('Exec DG', 'Unknown')
    df['DU'] = df.get('Exec DU', 'Unknown')

    df_rev = df[df['Type'].str.lower() == 'revenue']
    df_rev = df_rev.groupby(['FinalCustomerName', 'Segment', 'BU', 'DU', 'Month'])[amount_col].sum().reset_index()
    df_rev = df_rev.rename(columns={amount_col: 'Revenue'})
    return df_rev
