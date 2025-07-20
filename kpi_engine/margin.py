import pandas as pd

def preprocess_pnl_data(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df = df.rename(columns={
        'company_code': 'Client',
        'amount_in_inr': 'Amount',
        'month': 'Month',
        'type': 'Type'
    })
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    return df

def compute_margin(pnl_df):
    pnl_df.columns = pnl_df.columns.str.strip()
    required_cols = ['Client', 'Type', 'Month', 'Amount']
    for col in required_cols:
        if col not in pnl_df.columns:
            raise KeyError(f"Missing column: '{col}' in P&L data")

    revenue_df = pnl_df[pnl_df['Type'].str.lower() == 'revenue']
    cost_df = pnl_df[pnl_df['Type'].str.lower() == 'cost']

    revenue_grouped = revenue_df.groupby(['Client', 'Month'])['Amount'].sum().reset_index()
    cost_grouped = cost_df.groupby(['Client', 'Month'])['Amount'].sum().reset_index()

    margin_df = pd.merge(revenue_grouped, cost_grouped, on=['Client', 'Month'], suffixes=('_revenue', '_cost'))
    margin_df['CM%'] = ((margin_df['Amount_revenue'] - margin_df['Amount_cost']) / margin_df['Amount_revenue']) * 100
    margin_df = margin_df.rename(columns={'Amount_revenue': 'Revenue', 'Amount_cost': 'Cost'})

    return margin_df

def load_pnl_data(file_path="data/LnTPnL.xlsx"):
    """Loads and preprocesses P&L data from Excel file"""
    try:
        df = pd.read_excel(file_path)
        df = preprocess_pnl_data(df)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load P&L data: {e}")
