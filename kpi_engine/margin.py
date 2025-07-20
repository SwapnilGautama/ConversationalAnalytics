# kpi_engine/margin.py

import pandas as pd

def load_pnl_data(filepath, sheet_name="LnTPnL"):
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name, engine="openpyxl")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def preprocess_pnl_data(df):
    df.columns = df.columns.str.strip()

    # Rename columns for consistency
    df = df.rename(columns={
        'Month': 'Month',
        'Company Code': 'Client',
        'Amount': 'Amount',
        'Type': 'Type'
    })

    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df['Type'] = df['Type'].str.strip()
    df['Client'] = df['Client'].astype(str).str.strip()
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

    # Filter only Cost and Revenue rows
    df = df[df['Type'].isin(['Cost', 'Revenue'])].copy()

    # Pivot data to get separate Revenue and Cost columns
    df_pivot = df.pivot_table(
        index=['Client', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Rename columns back to flat names
    df_pivot.columns.name = None

    # Calculate Margin %
    df_pivot['Margin %'] = (
        (df_pivot['Revenue'] - df_pivot['Cost']) / df_pivot['Revenue'].replace(0, pd.NA)
    ) * 100

    return df_pivot
