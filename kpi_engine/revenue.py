import pandas as pd

def load_pnl_data(filepath: str = "sample_data/LnTPnL.xlsx", sheet_name: str = "LnTPnL") -> pd.DataFrame:
    """
    Loads P&L data from the given Excel file and sheet.
    
    Args:
        filepath (str): Path to the P&L Excel file.
        sheet_name (str): Sheet name in the Excel file.

    Returns:
        pd.DataFrame: Loaded dataframe.
    """
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")


def calculate_total_revenue(df: pd.DataFrame) -> float:
    """
    Calculates total revenue from specified Group1 categories.

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
    Calculates revenue for a specific Group1 type.

    Args:
        df (pd.DataFrame): The P&L dataframe.
        revenue_type (str): One of 'ONSITE', 'OFFSHORE', 'INDIRECT REVENUE'

    Returns:
        float: Revenue for the given type.
    """
    allowed_types = ["ONSITE", "OFFSHORE", "INDIRECT REVENUE"]
    if revenue_type not in allowed_types:
        raise ValueError(f"Invalid revenue_type. Must be one of: {allowed_types}")
    
    filtered = df[df["Group1"] == revenue_type]
    return filtered["Amount in USD"].sum()


# Test block
if __name__ == "__main__":
    df_pnl = load_pnl_data()
    total = calculate_total_revenue(df_pnl)
    onsite = calculate_revenue_by_type(df_pnl, "ONSITE")
    print(f"Total Revenue: ${total:,.2f}")
    print(f"Onsite Revenue: ${onsite:,.2f}")
