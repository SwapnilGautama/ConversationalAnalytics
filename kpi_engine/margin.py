# kpi_engine/margin.py

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
    df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
    df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce')
    df['Margin (₹)'] = df['Revenue'] - df['Cost']
    df['Margin %'] = (df['Margin (₹)'] / df['Revenue']) * 100
    return df.dropna(subset=['Month', 'Revenue', 'Cost'])

def total_margin(df):
    return df['Margin (₹)'].sum().round(2)

def overall_margin_percent(df):
    return df['Margin %'].mean().round(2)

def margin_by_client(df):
    return df.groupby('Client')[['Margin (₹)', 'Margin %']].sum().reset_index().round(2)

def margin_by_type(df):
    return df.groupby('Type')[['Margin (₹)', 'Margin %']].sum().reset_index().round(2)

def margin_by_location(df):
    return df.groupby('Location')[['Margin (₹)', 'Margin %']].sum().reset_index().round(2)

def margin_trend(df):
    return df.groupby('Month')[['Margin (₹)', 'Margin %']].sum().reset_index().round(2)

def margin_summary(df):
    summary = [
        f"Total margin earned is ₹{total_margin(df):,.2f}.",
        f"Overall average margin percentage is {overall_margin_percent(df)}%.",
        f"Top client by margin: {margin_by_client(df).sort_values('Margin (₹)', ascending=False).iloc[0].to_dict()}.",
        f"Best performing month: {margin_trend(df).sort_values('Margin (₹)', ascending=False).iloc[0].to_dict()}"
    ]
    return summary
