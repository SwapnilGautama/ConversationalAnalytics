# kpi_engine/utilization.py

import pandas as pd

def load_data(filepath, sheet_name="LnTPnL"):
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def preprocess(df):
    df.columns = df.columns.str.strip()
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df['Utilization %'] = pd.to_numeric(df['Utilization %'], errors='coerce')
    return df.dropna(subset=['Month', 'Utilization %'])

def overall_utilization(df):
    return df['Utilization %'].mean().round(2)

def utilization_by_client(df):
    return df.groupby('Client')['Utilization %'].mean().reset_index().round(2)

def utilization_by_type(df):
    return df.groupby('Type')['Utilization %'].mean().reset_index().round(2)

def utilization_trend(df):
    return df.groupby('Month')['Utilization %'].mean().reset_index().round(2)

def utilization_summary(df):
    summary = [
        f"Overall utilization across all clients is {overall_utilization(df)}%.",
        f"Highest utilization by client: {utilization_by_client(df).sort_values('Utilization %', ascending=False).iloc[0].to_dict()}.",
        f"Lowest utilization by client: {utilization_by_client(df).sort_values('Utilization %').iloc[0].to_dict()}.",
        f"Peak month for utilization: {utilization_trend(df).sort_values('Utilization %', ascending=False).iloc[0].to_dict()}"
    ]
    return summary
