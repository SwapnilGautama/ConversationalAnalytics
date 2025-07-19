import pandas as pd

def load_pnl_data(filepath: str = "sample_data/LnTPnL.xlsx", sheet_name: int = 0) -> pd.DataFrame:
    """
    Loads P&L data from the given Excel file.
    
    Args:
        filepath (str): Path to the P&L Excel file.
        sheet_name (int/str): Sheet name or index in the Excel file.

    Returns:
        pd.DataFrame: Loaded dataframe.
    """
    df = pd.read_excel(filepath, sheet_name=sheet_name)
    return df


def calculate_total_revenue(df: pd.DataFrame) -> float:
    """
    Calculates total revenue by summing values in 'Amount in USD' for relevant Group1 categories.

    Args:
        df (pd.DataFrame): The P&L dataframe.

    Returns:
        float: Total revenue.
    """
    revenue_groups = ["ONSITE", "OFFSHORE", "INDIRECT REVENUE"]
    filtered = df[df["Group1"].isin(revenue_groups)]
    return filtered["Amount in USD"].sum()


def calculate_revenue_by_type(df: pd.DataFrame, revenue_type: str) -> float:
    """
    Calculates revenue for a specific type like 'ONSITE', 'OFFSHORE', or 'INDIRECT REVENUE'.

    Args:
        df (pd.DataFrame): The P&L dataframe.
        revenue_type (str): One of the allowed types.

    Returns:
        float: Revenue for the given type.
    """
    if revenue_type not in ["ONSITE", "OFFSHORE", "INDIRECT REVENUE"]:
        raise ValueError("Invalid revenue_type. Must be one of: 'ONSITE', 'OFFSHORE', 'INDIRECT REVENUE'")
    
    filtered = df[df["Group1"] == revenue_type]
    return filtered["Amount in USD"].sum()


# Example (for testing or CLI execution)
if __name__ == "__main__":
    df_pnl = load_pnl_data()
    total = calculate_total_revenue(df_pnl)
    onsite = calculate_revenue_by_type(df_pnl, "ONSITE")
    print(f"Total Revenue: ${total:,.2f}")
    print(f"Onsite Revenue: ${onsite:,.2f}")
