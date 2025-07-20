import pandas as pd
from utils.helpers import extract_month, extract_quarter, extract_fy

def answer_question_q8(ut_df: pd.DataFrame, account_name: str) -> dict:
    """
    Returns the MoM trend of Headcount (HC) for a given account.

    Parameters:
    - ut_df (pd.DataFrame): Unified table with UT data
    - account_name (str): Name of the final customer / account

    Returns:
    - dict: Contains summary, table (DataFrame), and chart metadata
    """

    # Step 1: Filter for the selected account
    df = ut_df.copy()
    df = df[df['Final Customer Name'].str.lower() == account_name.lower()]

    if df.empty:
        return {
            "answer": f"No headcount data found for account '{account_name}'.",
            "table": pd.DataFrame(),
            "chart": None,
        }

    # Step 2: Extract month and year
    df["Month"] = pd.to_datetime(df["Month"]).dt.strftime("%b-%Y")

    # Step 3: Group by Month
    monthly_hc = df.groupby("Month")["HC"].sum().reset_index().sort_values("Month")

    # Step 4: Calculate MoM difference
    monthly_hc["MoM_Change"] = monthly_hc["HC"].diff().fillna(0)

    # Step 5: Format response
    latest_month = monthly_hc["Month"].iloc[-1]
    latest_hc = monthly_hc["HC"].iloc[-1]
    change = monthly_hc["MoM_Change"].iloc[-1]

    trend = "increased" if change > 0 else "decreased" if change < 0 else "remained stable"
    summary = (
        f"Headcount for account '{account_name}' in {latest_month} was {latest_hc} "
        f"and has {trend} by {abs(int(change))} from the previous month."
    )

    return {
        "answer": summary,
        "table": monthly_hc.rename(columns={"HC": "Headcount"}),
        "chart": {
            "type": "line",
            "x": monthly_hc["Month"].tolist(),
            "y": monthly_hc["HC"].tolist(),
            "title": f"Monthly Headcount Trend for {account_name}"
        }
    }
