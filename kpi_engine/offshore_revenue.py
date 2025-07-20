# kpi_engine/offshore_revenue.py

import pandas as pd

def load_data(pnl_path: str):
    try:
        df = pd.read_excel(pnl_path, sheet_name="LnTPnL")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def calculate_offshore_revenue(df: pd.DataFrame) -> float:
    try:
        offshore_revenue = df[df["Group1"] == "OFFSHORE"]["Amount in USD"].sum()
        return offshore_revenue
    except Exception as e:
        raise RuntimeError(f"Error calculating Offshore Revenue: {e}")
