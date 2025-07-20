# questions/question_q1.py

import pandas as pd
from kpi_engine.margin import compute_margin

def run(df):
    df = df.copy()

    # Step 1: Ensure margin is computed
    df = compute_margin(df)

    # Step 2: Add quarter column
    df['Quarter'] = df['Month'].dt.to_period("Q")

    # Step 3: Filter latest quarter
    latest_qtr = df['Quarter'].max()
    latest_df = df[df['Quarter'] == latest_qtr]

    # Step 4: Filter accounts with Margin % < 30
    if 'Margin %' not in latest_df.columns:
        return "❌ Error: 'Margin %' not found in data. Please ensure margin calculation is applied."

    result = latest_df[latest_df['Margin %'] < 30]

    # Step 5: Return output
    if result.empty:
        return "🎯 No accounts had margin < 30% in the latest quarter."

    summary = result.groupby('Client')[['Margin %']].mean().sort_values('Margin %').reset_index()
    summary.columns = ['Client', 'Avg Margin %']
    return summary
