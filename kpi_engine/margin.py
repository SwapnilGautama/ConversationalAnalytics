import pandas as pd

def preprocess_pnl_data(df):
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Rename to standardized names
    df = df.rename(columns={
        'Company_Code': 'Client',
        'Amount in Inr': 'Amount',
        'Month': 'Month',
        'Type': 'Type'
    })

    # Ensure 'Amount' is numeric
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    
    return df

def compute_margin(pnl_df):
    # Clean column names again for safety
    pnl_df.columns = pnl_df.columns.str.strip()

    # Check necessary fields exist
    required_cols = ['Client', 'Type', 'Month', 'Amount']
    for col in required_cols:
        if col not in pnl_df.columns:
            raise KeyError(f"Missing column: '{col}' in P&L data")

    # Filter Revenue and Cost
    revenue_df = pnl_df[pnl_df['Type'].str.lower() == 'revenue']
    cost_df = pnl_df[pnl_df['Type'].str.lower() == 'cost']

    # Group by Client and Month
    revenue_grouped = revenue_df.groupby(['Client', 'Month'])['Amount'].sum().reset_index()
    cost_grouped = cost_df.groupby(['Client', 'Month'])['Amount'].sum().reset_index()

    # Merge and compute CM%
    margin_df = pd.merge(revenue_grouped, cost_grouped, on=['Client', 'Month'], suffixes=('_revenue', '_cost'))
    margin_df['CM%'] = ((margin_df['Amount_revenue'] - margin_df['Amount_cost']) / margin_df['Amount_revenue']) * 100
    margin_df = margin_df.rename(columns={'Amount_revenue': 'Revenue', 'Amount_cost': 'Cost'})

    return margin_df
