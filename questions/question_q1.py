# question_engine/question_q1.py

import pandas as pd

def analyze_low_cm_accounts(pnl_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns final customer accounts where CM% < 30 or CM% < 0
    for any of the months in FY26-Q1 (Apr'25, May'25, Jun'25).

    CM% = (Revenue - Cost) / Revenue
    """
    # Ensure relevant columns exist
    required_columns = [
        'Final Customer Name', 'Month', 'Revenue', 'Cost'
    ]
    for col in required_columns:
        if col not in pnl_df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Filter for months in FY26-Q1
    target_months = ["Apr'25", "May'25", "Jun'25"]
    df = pnl_df[pnl_df['Month'].isin(target_months)].copy()

    # Calculate CM%
    df['CM%'] = (df['Revenue'] - df['Cost']) / df['Revenue']

    # Filter rows where CM% < 0.3
    df_filtered = df[df['CM%'] < 0.3]

    # Get distinct Final Customer Names meeting the condition
    flagged_accounts = df_filtered[['Final Customer Name', 'Month', 'CM%']]

    return flagged_accounts.sort_values(by=['Final Customer Name', 'Month'])


# ✅ Required by the app: wrapper function to expose the module
def run(pnl_df: pd.DataFrame, ut_df: pd.DataFrame = None):
    """
    Wrapper for question execution. Required by app.py
    """
    return {
        "summary": "Accounts with contribution margin below 30% in Q1 FY26",
        "table": analyze_low_cm_accounts(pnl_df)
    }
