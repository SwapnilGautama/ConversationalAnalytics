# kpi_engine/indirect_revenue.py

import pandas as pd

def load_data(pnl_path: str):
    try:
        df = pd.read_excel(pnl_path, sheet_name="LnTPnL")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def calculate_indirect_revenue(df: pd.DataFrame) -> float:
    try:
        indirect_revenue = df[df["Type"] == "Indirect Revenue"]["Amount in USD"].sum()
        return indirect_revenue
    except Exception as e:
        raise RuntimeError(f"Error calculating Indirect Revenue: {e}")
