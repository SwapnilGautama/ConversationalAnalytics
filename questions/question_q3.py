import pandas as pd

def analyze_cb_variation(df: pd.DataFrame) -> dict:
    """
    Analyze quarter-on-quarter variation in C&B cost from the P&L table.

    Args:
        df (pd.DataFrame): DataFrame containing P&L data with columns like 'Group Description', 'TimePeriod', 'Amount in USD'

    Returns:
        dict: Summary including variation value and breakdown by month if available
    """
    # Filter for C&B related costs
    cb_keywords = ["C&B Cost Onsite", "C&B Cost Offshore"]
    df_cb = df[df["Group Description"].isin(cb_keywords)].copy()

    # Ensure TimePeriod is datetime for proper quarter extraction
    df_cb["TimePeriod"] = pd.to_datetime(df_cb["TimePeriod"])
    df_cb["Quarter"] = df_cb["TimePeriod"].dt.to_period("Q")

    # Aggregate C&B cost by quarter
    cb_by_quarter = (
        df_cb.groupby("Quarter")["Amount in USD"].sum().sort_index().reset_index()
    )

    if len(cb_by_quarter) < 2:
        return {"error": "Insufficient data for quarter-on-quarter comparison."}

    # Compare last two quarters
    current_qtr = cb_by_quarter.iloc[-1]
    previous_qtr = cb_by_quarter.iloc[-2]
    diff = current_qtr["Amount in USD"] - previous_qtr["Amount in USD"]
    pct_change = (diff / previous_qtr["Amount in USD"]) * 100 if previous_qtr["Amount in USD"] else None

    return {
        "previous_quarter": str(previous_qtr["Quarter"]),
        "previous_cb": previous_qtr["Amount in USD"],
        "current_quarter": str(current_qtr["Quarter"]),
        "current_cb": current_qtr["Amount in USD"],
        "difference": diff,
        "percentage_change": pct_change,
        "trend": "increase" if diff > 0 else "decrease" if diff < 0 else "no change",
    }
