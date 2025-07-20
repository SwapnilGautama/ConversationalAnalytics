# kpi_engine/onsite_revenue.py

import pandas as pd

def load_data(pnl_path: str):
    try:
        df = pd.read_excel(pnl_path, sheet_name="LnTPnL")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def calculate_onsite_revenue(df: pd.DataFrame) -> float:
    try:
        onsite_revenue = df[df["Group1"] == "ONSITE"]["Amount in USD"].sum()
        return onsite_revenue
    except Exception as e:
        raise RuntimeError(f"Error calculating Onsite Revenue: {e}")
