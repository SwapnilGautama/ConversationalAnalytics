import pandas as pd

def load_pnl_data(filepath, sheet_name="LnTPnL"):
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name, engine="openpyxl")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def preprocess_pnl_data(df):
    df.columns = df.columns.str.strip()

    # Dynamically rename columns based on what's present
    column_map = {}

    if 'Company Code' in df.columns:
        column_map['Company Code'] = 'Client'
    elif 'Company_Code' in df.columns:
        column_map['Company_Code'] = 'Client'

    if 'Amount in INR' in df.columns:
        column_map['Amount in INR'] = 'Amount'
    elif 'Amount' in df.columns:
        column_map['Amount'] = 'Amount'

    if 'Month' in df.columns:
        column_map['Month'] = 'Month'

    if 'Type' in df.columns:
        column_map['Type'] = 'Type'

    if 'segment' in df.columns:
        column_map['segment'] = 'segment'  # preserve as-is

    df = df.rename(columns=column_map)

    # Ensure Month is datetime
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')

    # Keep only Cost and Revenue rows
    df = df[df['Type'].isin(['Cost', 'Revenue'])]

    # Convert Amount to numeric and drop invalid rows
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna(subset=['Month', 'Amount'])

    return df

def compute_margin(df):
    # Check if 'segment' exists and include in groupby if present
    groupby_cols = ['Month', 'Client']
    if 'segment' in df.columns:
        groupby_cols.append('segment')

    grouped = df.groupby(groupby_cols + ['Type'])['Amount'].sum().unstack().fillna(0)

    grouped['Margin'] = grouped['Revenue'] - grouped['Cost']
    grouped['CM%'] = (grouped['Margin'] / grouped['Revenue']) * 100
    grouped['Margin %'] = grouped['CM%']

    grouped = grouped.reset_index()

    return grouped
