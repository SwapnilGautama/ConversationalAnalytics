# questions/question_q1.py

import pandas as pd

def run(df):
    df = df.copy()
    df['Quarter'] = df['Month'].dt.to_period('Q')

    # Use latest quarter
    latest_qtr = df['Quarter'].max()
    filtered = df[df['Quarter'] == latest_qtr]
    result = filtered[filtered['Margin %'] < 30]

    if result.empty:
        return "No accounts with margin below 30% in the latest quarter."

    summary = result.groupby('Client')[['Margin %']].mean().sort_values('Margin %').reset_index()
    return summary
