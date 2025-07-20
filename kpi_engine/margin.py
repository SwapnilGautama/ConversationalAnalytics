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

    # Rename for consistency
    df = df.rename(columns={
        'Month': 'Month',
        'Company Code': 'Client',
        'Amount': 'Amount',
        'Type': 'Type'
    })

    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')

    # Clean & filter
    df = df[df['Type'].isin(['Cost', 'Revenue'])]
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    
    # Pivot to get Revenue and Cost per row
    pivot_df = df.pivot_table(
        index=['Client', 'Month'],
        columns='Type',
        values='Amount',
        aggfunc='sum'
    ).reset_index()

    pivot_df = pivot_df.fillna(0)
    pivot_df['Margin (₹)'] = pivot_df['Revenue'] - pivot_df['Cost']
    pivot_df['Margin %'] = (pivot_df['Margin (₹)'] / pivot_df['Revenue']) * 100
    return pivot_df.dropna(subset=['Month', 'Revenue', 'Cost'])

def total_margin(df):
    return df['Margin (₹)'].sum().round(2)

def overall_margin_percent(df):
    return df['Margin %'].mean().round(2)

def margin_by_client(df):
    return df.groupby('Client')[['Margin (₹)', 'Margin %']].mean().reset_index().round(2)

def margin_by_type(df):
    return df.groupby('Type')[['Margin (₹)', 'Margin %']].mean().reset_index().round(2)

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
