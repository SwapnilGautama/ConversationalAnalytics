# ✅ FINAL: headcount_aggregated.py aligned to question_q7 logic
import pandas as pd

def compute_headcount(df_ut: pd.DataFrame) -> pd.DataFrame:
    df = df_ut.copy()
    
    # ✅ Clean segment and date
    df = df[df['Segment'].notna()]
    df['date_a'] = pd.to_datetime(df['date_a'], errors='coerce')
    df = df[df['date_a'].notna()]

    # ✅ Use both Billable and Non-Billable
    df['Status'] = df['Status'].fillna('').str.lower()
    df = df[df['Status'].isin(['billable', 'non-billable'])]

    # ✅ FTE handling
    df['FTE'] = df['FTE'].fillna(1)

    # ✅ Extract Month and Year
    df['Month'] = df['date_a'].dt.to_period("M")

    # ✅ Aggregation by Segment, BU, DU, Month
    segment = df.groupby(['Month', 'Segment'])['FTE'].sum().reset_index()
    segment['Group Type'] = 'Segment'
    segment.rename(columns={'Segment': 'Group', 'FTE': 'Headcount'}, inplace=True)

    bu = df.groupby(['Month', 'Exec DG'])['FTE'].sum().reset_index()
    bu['Group Type'] = 'BU'
    bu.rename(columns={'Exec DG': 'Group', 'FTE': 'Headcount'}, inplace=True)

    du = df.groupby(['Month', 'Exec DU'])['FTE'].sum().reset_index()
    du['Group Type'] = 'DU'
    du.rename(columns={'Exec DU': 'Group', 'FTE': 'Headcount'}, inplace=True)

    combined = pd.concat([segment, bu, du], ignore_index=True)
    combined['Headcount'] = combined['Headcount'].round(0).astype(int)
    combined['Month'] = combined['Month'].astype(str)

    return combined[['Month', 'Group Type', 'Group', 'Headcount']]
