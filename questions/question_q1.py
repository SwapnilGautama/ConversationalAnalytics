# questions/question_q1.py

import pandas as pd

def run(df):
    df = df.copy()
    df['Quarter'] = df['Month'].dt.to_period("Q")

    # Get latest quarter
    latest_qtr = df['Quarter'].max()
    latest_df = df[df['Quarter'] == latest_qtr]

    # Filter accounts with CM% < 30
    result = latest_df[latest_df['Margin %'] < 30]

    if result.empty:
        return "🎯 No accounts had margin < 30% in the latest quarter."

    summary = result.groupby('Client')[['Margin %']].mean().sort_values('Margin %').reset_index()
    summary.columns = ['Client', 'Avg Margin %']
    return summary
