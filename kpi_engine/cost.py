import pandas as pd

# Define default cost categories
ONSITE_COST_GROUPS = ["COST - ONSITE"]
OFFSHORE_COST_GROUPS = ["COST - OFFSHORE"]
INDIRECT_COST_GROUPS = ["COST - INDIRECT"]

def load_pnl_data(filepath: str, sheet_name: str = "LnTPnL") -> pd.DataFrame:
    """
    Load the PnL data from the provided Excel file and sheet.
    """
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load cost data: {e}")

def calculate_total_cost(df: pd.DataFrame) -> float:
    """
    Calculate total cost by summing 'Amount in USD' across all records.
    """
    return df["Amount in USD"].sum()

def calculate_cost_by_type(df: pd.DataFrame, cost_type: str) -> float:
    """
    Calculate total cost filtered by type: 'ONSITE', 'OFFSHORE', or 'INDIRECT'.
    """
    cost_type = cost_type.upper()
    if cost_type == "ONSITE":
        groups = ONSITE_COST_GROUPS
    elif cost_type == "OFFSHORE":
        groups = OFFSHORE_COST_GROUPS
    elif cost_type == "INDIRECT":
        groups = INDIRECT_COST_GROUPS
    else:
        raise ValueError(f"Invalid cost type: {cost_type}")

    filtered_df = df[df["Group1"].isin(groups)]
    return filtered_df["Amount in USD"].sum()

def summarize_cost(df: pd.DataFrame) -> list:
    """
    Generate a simple 3-point AI-style summary for total and breakdown of costs.
    """
    total = calculate_total_cost(df)
    onsite = calculate_cost_by_type(df, "ONSITE")
    offshore = calculate_cost_by_type(df, "OFFSHORE")
    indirect = calculate_cost_by_type(df, "INDIRECT")

    summary = [
        f"💰 Total cost incurred: ${total:,.2f}",
        f"🏢 Onsite cost share: ${onsite:,.2f}, Offshore: ${offshore:,.2f}",
        f"📊 Indirect costs contribute: ${indirect:,.2f} to the total"
    ]
    return summary
