import pandas as pd

def load_pnl_data(file_path="data/LnTPnL.xlsx"):
    """
    Loads and preprocesses the P&L data from Excel.
    """
    try:
        df = pd.read_excel(file_path)
        print("Loaded columns from file:", df.columns.tolist())  # Debugging
        df = preprocess_pnl_data(df)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load P&L data: {e}")

def preprocess_pnl_data(df):
    """
    Standardizes column names and ensures key fields are renamed and formatted.
    """
    # Clean and normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    print("Sanitized columns:", df.columns.tolist())  # Debugging

    # Rename critical columns to match app logic
    df = df.rename(columns={
        'company_code': 'Client',
        'amount_in_inr': 'Amount',
        'month': 'Month',
        'type': 'Type'
    })

    # Final check
    print("Final columns after renaming:", df.columns.tolist())

    # Ensure numeric 'Amount'
    if 'Amount' in df.columns:
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    else:
        raise ValueError("Column 'Amount' not found after renaming.")

    return df

def compute_margin(df):
    """
    Computes margin by grouping the data and calculating CM% per client per month.
    Assumes df has been processed already.
    """
    required_columns = {'Client', 'Month', 'Type', 'Amount'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Missing one or more required columns: {required_columns - set(df.columns)}")

    # Pivot and compute margin per month per client
    df_grouped = df.groupby(['Client', 'Month', 'Type'])['Amount'].sum().reset_index()

    # Pivot to wide format
    df_pivot = df_grouped.pivot_table(index=['Client', 'Month'], columns='Type', values='Amount', fill_value=0).reset_index()

    # Rename columns if they exist
    revenue_col = 'Revenue' if 'Revenue' in df_pivot.columns else None
    cost_col = 'Cost' if 'Cost' in df_pivot.columns else None

    if revenue_col and cost_col:
        df_pivot['Margin %'] = ((df_pivot[revenue_col] - df_pivot[cost_col]) / df_pivot[revenue_col]) * 100
    else:
        raise ValueError("Both 'Revenue' and 'Cost' columns are required to compute margin.")

    return df_pivot
