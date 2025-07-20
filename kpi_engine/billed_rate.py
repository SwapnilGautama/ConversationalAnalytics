# kpi_engine/billed_rate.py

import pandas as pd

def load_data(pnl_path: str, ut_path: str, pnl_sheet: str = "LnTPnL", ut_sheet: str = "LNTData") -> tuple:
    """Load data from Excel files."""
    try:
        pnl_df = pd.read_excel(pnl_path, sheet_name=pnl_sheet)
        ut_df = pd.read_excel(ut_path, sheet_name=ut_sheet)
        return pnl_df, ut_df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def calculate_billed_rate(pnl_df: pd.DataFrame, ut_df: pd.DataFrame) -> float:
    """Calculate Billed Rate = Revenue / Total Billable Hours"""
    try:
        # Filter revenue from P&L table
        revenue = pnl_df.loc[
            pnl_df["Group1"].str.upper().isin(["ONSITE", "OFFSHORE", "INDIRECT REVENUE"]),
            "Amount in USD"
        ].sum()

        # Total billable hours from UT table
        total_billable_hours = ut_df["TotalBillableHours"].sum()

        if total_billable_hours == 0:
            return 0.0

        return revenue / total_billable_hours
    except Exception as e:
        raise RuntimeError(f"Error in calculating billed rate: {e}")
