# questions/question_q1.py

import pandas as pd

def analyze_low_cm_accounts(pnl_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns accounts where CM% < 30% in any month of FY26-Q1 (Apr–Jun 2025).
    CM% = (Revenue - Cost) / Revenue
    """
    if pnl_df is None or pnl_df.empty:
        raise ValueError("P&L dataframe is empty or missing.")

    required_cols = ['Final Customer Name', 'Month', 'Revenue', 'Cost']
    for col in required_cols:
        if col not in pnl_df.columns:
            raise ValueError(f"Missing column: {col}")

    # Filter for Q1 FY26 months
    target_months = ["Apr'25", "May'25", "Jun'25"]
    df = pnl_df[pnl_df['Month'].isin(target_months)].copy()

    # Calculate Contribution Margin %
    df['CM%'] = (df['Revenue'] - df['Cost']) / df['Revenue']

    # Filter accounts with CM% < 30%
    flagged = df[df['CM%'] < 0.3][['Final Customer Name', 'Month', 'CM%']]
    return flagged.sort_values(by=['Final Customer Name', 'Month'])

def run(pnl_df: pd.DataFrame, ut_df: pd.DataFrame = None):
    """
    Executes the analysis for Question 1.
    """
    flagged_accounts = analyze_low_cm_accounts(pnl_df)
    return {
        "summary": f"Identified {flagged_accounts['Final Customer Name'].nunique()} accounts with contribution margin below 30% during Q1 FY26.",
        "table": flagged_accounts
    }
