# question_q1.py

import pandas as pd
from kpi_engine.margin import compute_margin

def answer(df_pnl: pd.DataFrame, df_ut: pd.DataFrame = None):
    """
    Which accounts had CM% < 30 in the last quarter?
    """

    # Compute margin KPIs
    df_margin = compute_margin(df_pnl)

    # Extract last quarter from the data
    latest_quarter = df_margin['Quarter'].max()

    # Filter for CM% < 30 in last quarter
    df_filtered = df_margin[
        (df_margin['Quarter'] == latest_quarter) &
        (df_margin['CM%'] < 30)
    ]

    if df_filtered.empty:
        return {
            "answer": f"No accounts had CM% below 30 in the last quarter ({latest_quarter}).",
            "tables": [],
            "charts": []
        }

    summary_text = f"{len(df_filtered)} accounts had CM% below 30 in the last quarter ({latest_quarter})."

    result_table = df_filtered[['Company Code', 'Quarter', 'Revenue', 'Cost', 'CM%', 'Margin']].sort_values(by='CM%')

    return {
        "answer": summary_text,
        "tables": [result_table],
        "charts": []
    }
