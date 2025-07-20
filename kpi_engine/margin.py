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
        'Company_Code': 'Client',
        'Amount in INR': 'Amount',
        'Type': 'Type'
    })

    # Ensure Month is datetime
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')

    # Keep only Cost and Revenue rows
    df = df[df['Type'].isin(['Cost', 'Revenue'])]

    # Convert Amount to numeric and drop invalid rows
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna(subset=['Month', 'Amount'])

    return df

def compute_margin(df):
    # Group by Month and Client
    grouped = df.groupby(['Month', 'Client', 'Type'])['Amount'].sum().unstack().fillna(0)

    # Calculate margin and CM%
    grouped['Margin'] = grouped['Revenue'] - grouped['Cost']
    grouped['CM%'] = (grouped['Margin'] / grouped['Revenue']) * 100
    grouped = grouped.reset_index()

    return grouped
