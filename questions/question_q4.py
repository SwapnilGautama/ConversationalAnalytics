import pandas as pd

def get_mom_cb_cost_percentage_trend(pnl_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Month-over-Month trend of C&B cost as a percentage of total revenue.
    
    Args:
        pnl_df (pd.DataFrame): P&L data with 'Month', 'Type', and 'Amount in USD'
    
    Returns:
        pd.DataFrame: MoM trend showing Month, C&B %, and delta
    """
    # Filter for relevant rows
    cb_df = pnl_df[pnl_df["Type"].str.contains("C&B", case=False)].copy()
    revenue_df = pnl_df[pnl_df["Type"].str.lower() == "revenue"].copy()

    # Aggregate by month
    cb_monthly = cb_df.groupby("Month")["Amount in USD"].sum().rename("C&B Cost")
    rev_monthly = revenue_df.groupby("Month")["Amount in USD"].sum().rename("Total Revenue")

    # Combine and calculate %
    result = pd.concat([cb_monthly, rev_monthly], axis=1).dropna()
    result["C&B %"] = (result["C&B Cost"] / result["Total Revenue"]) * 100
    result["MoM Change (%)"] = result["C&B %"].diff().round(2)

    return result.reset_index()
