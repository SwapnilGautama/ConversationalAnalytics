import pandas as pd

def get_headcount_aggregated(ut_path):
    df = pd.read_excel(ut_path)
    df.columns = df.columns.str.strip()

    df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
    df = df.dropna(subset=['Date_a', 'FinalCustomerName', 'PSNo'])

    df['Month'] = df['Date_a'].dt.to_period('M').astype(str)

    df['Segment'] = df.get('Segment', 'Unknown')
    df['BU'] = df.get('Exec DG', 'Unknown')
    df['DU'] = df.get('Exec DU', 'Unknown')

    grouped = (
        df.groupby(['FinalCustomerName', 'Segment', 'BU', 'DU', 'Month'])['PSNo']
        .nunique()
        .reset_index()
        .rename(columns={'PSNo': 'FTE'})
    )

    grouped['FTE'] = grouped['FTE'].round(1)
    return grouped
