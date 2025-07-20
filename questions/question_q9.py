import pandas as pd

def answer_question_q9(pnl_df: pd.DataFrame, ut_df: pd.DataFrame, account_name: str) -> dict:
    """
    Calculates the monthly Revenue per Person for a given account.

    Parameters:
    - pnl_df (pd.DataFrame): P&L table with revenue data
    - ut_df (pd.DataFrame): UT table with headcount data
    - account_name (str): Final customer / account name to filter

    Returns:
    - dict: Contains summary, trend table, and chart metadata
    """
    # Step 1: Filter both datasets for the given account
    rev_df = pnl_df[pnl_df["Final Customer Name"].str.lower() == account_name.lower()].copy()
    hc_df = ut_df[ut_df["Final Customer Name"].str.lower() == account_name.lower()].copy()

    if rev_df.empty or hc_df.empty:
        return {
            "answer": f"Revenue per person trends not available for account '{account_name}'.",
            "table": pd.DataFrame(),
            "chart": None,
        }

    # Step 2: Standardize month format
    rev_df["Month"] = pd.to_datetime(rev_df["Month"]).dt.strftime("%b-%Y")
    hc_df["Month"] = pd.to_datetime(hc_df["Month"]).dt.strftime("%b-%Y")

    # Step 3: Aggregate monthly revenue and HC
    monthly_revenue = rev_df.groupby("Month")["Amount in USD"].sum().reset_index()
    monthly_revenue.rename(columns={"Amount in USD": "Revenue"}, inplace=True)

    monthly_hc = hc_df.groupby("Month")["HC"].sum().reset_index()
    monthly_hc.rename(columns={"HC": "Headcount"}, inplace=True)

    # Step 4: Merge revenue and HC
    merged = pd.merge(monthly_revenue, monthly_hc, on="Month", how="inner")
    merged["Revenue per Person"] = (merged["Revenue"] / merged["Headcount"]).round(2)

    # Step 5: Format output
    latest_month = merged["Month"].iloc[-1]
    latest_val = merged["Revenue per Person"].iloc[-1]

    summary = (
        f"Revenue per person for account '{account_name}' in {latest_month} was ${latest_val}."
    )

    return {
        "answer": summary,
        "table": merged[["Month", "Revenue", "Headcount", "Revenue per Person"]],
        "chart": {
            "type": "line",
            "x": merged["Month"].tolist(),
            "y": merged["Revenue per Person"].tolist(),
            "title": f"Revenue per Person Trend for {account_name}"
        }
    }
