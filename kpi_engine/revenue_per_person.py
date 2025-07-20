# kpi_engine/revenue_per_person.py

import pandas as pd

def load_data(pnl_path: str, ut_path: str):
    try:
        pnl_df = pd.read_excel(pnl_path, sheet_name="LnTPnL")
        ut_df = pd.read_excel(ut_path, sheet_name="LNTData")
        return pnl_df, ut_df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def calculate_revenue_per_person(pnl_df: pd.DataFrame, ut_df: pd.DataFrame) -> float:
    try:
        revenue = pnl_df[pnl_df["Group1"].isin(["ONSITE", "OFFSHORE", "INDIRECT REVENUE"])]["Amount in USD"].sum()
        total_headcount = ut_df["Total_Headcount"].sum()

        if total_headcount == 0:
            return 0.0

        return revenue / total_headcount
    except Exception as e:
        raise RuntimeError(f"Error calculating Revenue Per Person: {e}")
