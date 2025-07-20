# kpi_engine/resources.py

import pandas as pd

def load_pnl_data(filepath, sheet_name="LnTPnL"):
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def preprocess_pnl_data(df):
    df.columns = df.columns.str.strip()
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    return df.dropna(subset=['Month'])

def calculate_total_resources(df):
    return df['Total Resources'].sum()

def calculate_resources_by_client(df):
    return df.groupby('Client')['Total Resources'].sum().reset_index()

def calculate_resources_by_type(df):
    return df.groupby('Type')['Total Resources'].sum().reset_index()

def calculate_resources_by_location(df):
    return df.groupby('Location')['Total Resources'].sum().reset_index()

def calculate_resources_trend(df):
    return df.groupby('Month')['Total Resources'].sum().reset_index()
