# kpi_engine/headcount.py

import pandas as pd

def load_resource_data(filepath, sheet_name="ResourceMaster"):
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def preprocess_resource_data(df):
    df.columns = df.columns.str.strip()
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df['Headcount'] = 1  # Each row is one resource
    return df.dropna(subset=['Month'])

def total_headcount(df):
    return df['Headcount'].sum()

def headcount_by_client(df):
    return df.groupby('Client')['Headcount'].sum().reset_index()

def headcount_by_type(df):
    return df.groupby('Type')['Headcount'].sum().reset_index()

def headcount_by_location(df):
    return df.groupby('Location')['Headcount'].sum().reset_index()

def headcount_trend(df):
    return df.groupby('Month')['Headcount'].sum().reset_index()

def headcount_summary(df):
    summary = [
        f"Total headcount: {total_headcount(df)}",
        f"Top client by headcount: {headcount_by_client(df).sort_values('Headcount', ascending=False).iloc[0].to_dict()}",
        f"Peak headcount month: {headcount_trend(df).sort_values('Headcount', ascending=False).iloc[0].to_dict()}"
    ]
    return summary
