# ✅ FINAL FIXED: Matches question_q7 exactly (uses PSNo.nunique instead of FTE)
import pandas as pd

def compute_headcount(df_ut: pd.DataFrame) -> pd.DataFrame:
    df = df_ut.copy()

    # ✅ Basic clean-up
    df = df[df['Segment'].notna()]
    df['date_a'] = pd.to_datetime(df['date_a'], errors='coerce')
    df = df[df['date_a'].notna()]
    df = df[df['PSNo'].notna()]
    df['Month'] = df['date_a'].dt.to_period("M").astype(str)

    # ✅ Deduplicate based on Month and PSNo
    df = df.drop_duplicates(subset=['Month', 'PSNo'])

    # ✅ Aggregation using PSNo.nunique() instead of FTE sum
    segment = df.groupby(['Month', 'Segment'])['PSNo'].nunique().reset_index()
    segment['Group Type'] = 'Segment'
    segment.rename(columns={'Segment': 'Group', 'PSNo': 'Headcount'}, inplace=True)

    bu = df.groupby(['Month', 'Exec DG'])['PSNo'].nunique().reset_index()
    bu['Group Type'] = 'BU'
    bu.rename(columns={'Exec DG': 'Group', 'PSNo': 'Headcount'}, inplace=True)

    du = df.groupby(['Month', 'Exec DU'])['PSNo'].nunique().reset_index()
    du['Group Type'] = 'DU'
    du.rename(columns={'Exec DU': 'Group', 'PSNo': 'Headcount'}, inplace=True)

    combined = pd.concat([segment, bu, du], ignore_index=True)
    combined['Headcount'] = combined['Headcount'].astype(int)

    return combined[['Month', 'Group Type', 'Group', 'Headcount']]
