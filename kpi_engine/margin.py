import pandas as pd

def load_pnl_data(filepath, sheet_name="LnTPnL"):
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name, engine="openpyxl")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def preprocess_pnl_data(df):
    df.columns = df.columns.str.strip()

    # Dynamic column renaming
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

    if 'Segment' in df.columns:
        column_map['Segment'] = 'Segment'

    df = df.rename(columns=column_map)

    # Convert Month column to datetime safely
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')

    # Filter to Cost/Revenue rows
    df = df[df['Type'].isin(['Cost', 'Revenue'])]

    # Coerce Amount column and remove rows with NaNs in key columns
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna(subset=['Month', 'Amount', 'Client'])

    return df

def compute_margin(df):
    # Add Quarter column
    df['Quarter'] = df['Month'].dt.to_period("Q").astype(str)

    # Grouping by Quarter, Month, Client, and optionally Segment
    groupby_cols = ['Quarter', 'Month', 'Client']
    if 'Segment' in df.columns:
        groupby_cols.append('Segment')

    grouped = df.groupby(groupby_cols + ['Type'])['Amount'].sum().unstack().fillna(0)

    grouped['Margin'] = grouped.get('Revenue', 0) - grouped.get('Cost', 0)
    grouped['CM%'] = (grouped['Margin'] / grouped.get('Revenue', 1).replace(0, 1)) * 100
    grouped['Margin %'] = grouped['CM%']

    return grouped.reset_index()
