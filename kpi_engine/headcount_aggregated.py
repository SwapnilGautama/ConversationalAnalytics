import pandas as pd

def get_headcount_data(df_ut):
    df_ut = df_ut.copy()
    df_ut['Date_a'] = pd.to_datetime(df_ut['Date_a'], errors='coerce')
    df_ut = df_ut.dropna(subset=['Date_a', 'PSNo'])

    # ✅ Remove duplicates per PSNo + Date
    df_ut = df_ut.drop_duplicates(subset=['PSNo', 'Date_a'])

    # ✅ Convert date to monthly string
    df_ut['Month'] = df_ut['Date_a'].dt.to_period('M').astype(str)

    # ✅ Ensure required fields exist
    df_ut['Segment'] = df_ut.get('Segment', 'Unknown')
    df_ut['BU'] = df_ut.get('Exec DG', 'Unknown')
    df_ut['DU'] = df_ut.get('Exec DU', 'Unknown')
    df_ut['FinalCustomerName'] = df_ut.get('FinalCustomerName', 'Unknown')

    # ✅ Explicitly include both Billable and Non-Billable (no filter applied)
    result_frames = []
    for groupby_col in ['Segment', 'BU', 'DU', 'FinalCustomerName']:
        monthly_headcount = (
            df_ut.groupby([groupby_col, 'Month'])['PSNo']
            .nunique()
            .reset_index()
        )
        monthly_headcount['FTE'] = monthly_headcount['PSNo'].round(1)
        monthly_headcount = monthly_headcount.rename(columns={
            groupby_col: 'Group',
            'Month': 'Month',
            'FTE': 'Headcount'
        })[['Group', 'Month', 'Headcount']]
        monthly_headcount['Dimension'] = groupby_col
        result_frames.append(monthly_headcount)

    df_all = pd.concat(result_frames, ignore_index=True)
    df_all = df_all[['Dimension', 'Group', 'Month', 'Headcount']]

    return df_all
