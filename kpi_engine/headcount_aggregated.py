import pandas as pd

def compute_headcount(df_ut):
    df_ut = df_ut.copy()

    # ✅ Parse Date and filter valid records
    df_ut['Date_a'] = pd.to_datetime(df_ut['Date_a'], errors='coerce')
    df_ut = df_ut.dropna(subset=['Date_a', 'PSNo'])

    # ✅ Optional: filter for billable only
    df_ut['Status'] = df_ut['Status'].fillna('').str.lower()
    df_ut = df_ut[df_ut['Status'] == 'billable']

    # ✅ Deduplicate by person-date
    df_ut = df_ut.drop_duplicates(subset=['PSNo', 'Date_a'])

    # ✅ Add formatted month
    df_ut['Month'] = df_ut['Date_a'].dt.strftime('%b %Y')

    result_frames = []

    for groupby_col in ['Segment', 'BU', 'DU', 'FinalCustomerName']:
        df_temp = df_ut.copy()

        # 🔍 Apply transportation filter ONLY for Segment grouping
        if groupby_col == 'Segment':
            df_temp['Segment'] = df_temp['Segment'].fillna('').str.strip()
            df_temp = df_temp[df_temp['Segment'].str.lower() == 'transportation']

        monthly_headcount = (
            df_temp.groupby([groupby_col, 'Month'])['PSNo']
            .nunique()
            .reset_index()
            .rename(columns={
                groupby_col: 'Group',
                'PSNo': 'Headcount'
            })
        )

        monthly_headcount['Group Type'] = groupby_col
        result_frames.append(monthly_headcount)

    final_df = pd.concat(result_frames, ignore_index=True)
    final_df = final_df[['Group Type', 'Group', 'Month', 'Headcount']]
    return final_df
