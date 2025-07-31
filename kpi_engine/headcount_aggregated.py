import pandas as pd

def get_headcount_aggregated(ut_path):
    df = pd.read_excel(ut_path)

    df.columns = df.columns.str.strip()

    df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
    df['Month'] = df['Date_a'].dt.month.map({
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

    grouped = df.groupby(['FinalCustomerName', 'Segment', 'BU', 'DU', 'Month'])['PSNo'].nunique().reset_index()
    grouped = grouped.rename(columns={'PSNo': 'Headcount'})
    return grouped
