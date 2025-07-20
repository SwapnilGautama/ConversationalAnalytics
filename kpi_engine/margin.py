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

    # Rename for consistency using correct column names from your data
    df = df.rename(columns={
        'Month': 'Month',
        'Company_Code': 'Client',
        'Amount in INR': 'Amount',
        'Type': 'Type'
    })

    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')

    # Clean & filter
    df = df[df['Type'].isin(['Cost', 'Revenue'])]
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna(subset=['Month', 'Client', 'Amount'])

    return df

def calculate_margin(df):
    # Pivot to get Revenue and Cost per Client-Month
    pivot_df = df.pivot_table(index=['Client', 'Month'], columns='Type', values='Amount', aggfunc='sum').reset_index()

    # Fill missing values
    pivot_df = pivot_df.fillna(0)

    # Calculate margin %
    pivot_df['Margin %'] = ((pivot_df['Revenue'] - pivot_df['Cost']) / pivot_df['Revenue']) * 100
    pivot_df['Margin %'] = pivot_df['Margin %'].round(2)

    return pivot_df
