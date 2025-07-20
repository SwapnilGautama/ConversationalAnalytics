import pandas as pd

def question_7_realized_rate_drop(pnl_df: pd.DataFrame, ut_df: pd.DataFrame, threshold: float = 3.0) -> dict:
    """
    Identifies accounts where realized rate dropped more than a given threshold from last quarter to current quarter.
    
    Args:
        pnl_df (pd.DataFrame): P&L data containing 'Final Customer name', 'Quarter', 'Revenue'
        ut_df (pd.DataFrame): UT data containing 'Final Customer name', 'Quarter', 'HC'
        threshold (float): The dollar value drop to flag (default is $3)
        
    Returns:
        dict: Dictionary with summary, table (DataFrame), and logic explanation.
    """
    # Merge P&L and UT data to compute realized rate = Revenue / HC
    merged_df = pd.merge(
        pnl_df,
        ut_df,
        on=["Final Customer name", "Quarter"],
        how="inner",
        suffixes=("_pnl", "_ut")
    )

    merged_df["Realized Rate"] = merged_df["Revenue"] / merged_df["HC"]
    
    # Pivot to get previous and current quarter for rate comparison
    pivot_df = merged_df.pivot(index="Final Customer name", columns="Quarter", values="Realized Rate").reset_index()
    pivot_df.columns.name = None

    # Assume last 2 quarters are sorted and labeled like 'FY25Q4', 'FY26Q1'
    last_two_quarters = sorted([col for col in pivot_df.columns if col != "Final Customer name"])[-2:]
    
    pivot_df["Rate Drop"] = pivot_df[last_two_quarters[1]] - pivot_df[last_two_quarters[0]]
    
    flagged = pivot_df[pivot_df["Rate Drop"] < -threshold].copy()
    
    summary = (
        f"{len(flagged)} account(s) had a realized rate drop greater than ${threshold} "
        f"from {last_two_quarters[0]} to {last_two_quarters[1]}."
    )
    
    return {
        "summary": summary,
        "table": flagged[["Final Customer name", last_two_quarters[0], last_two_quarters[1], "Rate Drop"]],
        "insight_logic": f"Compared realized rate (Revenue / HC) between {last_two_quarters[0]} and {last_two_quarters[1]}, flagged if drop > ${threshold}."
    }
