# kpi_engine/realized_rate.py

import pandas as pd

def load_data(pnl_path: str, ut_path: str):
    try:
        pnl_df = pd.read_excel(pnl_path, sheet_name="LnTPnL")
        ut_df = pd.read_excel(ut_path, sheet_name="LNTData")
        return pnl_df, ut_df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def calculate_realized_rate(pnl_df: pd.DataFrame, ut_df: pd.DataFrame) -> float:
    # Calculate total revenue
    revenue = pnl_df[pnl_df["Group1"].isin(["ONSITE", "OFFSHORE", "INDIRECT REVENUE"])]["Amount in USD"].sum()

    # Calculate total available hours
    total_available_hours = ut_df["NetAvailableHours"].sum()

    if total_available_hours == 0:
        return 0.0

    return revenue / total_available_hours
