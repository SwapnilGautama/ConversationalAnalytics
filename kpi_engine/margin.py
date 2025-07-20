import pandas as pd

def load_pnl_data(pnl_path):
    try:
        df = pd.read_excel(pnl_path)

        # Rename critical columns safely
        rename_dict = {
            'Client Name': 'Client',
            'Company Code': 'Company_code',
            'Amount in INR': 'Amount',
            'Particulars': 'Particulars',
            'Month': 'Month',
            'Year': 'Year'
        }

        df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns}, inplace=True)

        required_columns = ['Client', 'Company_code', 'Amount', 'Particulars', 'Month', 'Year']
        for col in required_columns:
            if col not in df.columns:
                raise KeyError(f"Failed to load P&L data: '{col}'")

        return df

    except Exception as e:
        raise RuntimeError(f"Failed to load P&L data: {e}")

def compute_margin(pnl_df):
    try:
        # Filter revenue and cost data
        revenue_df = pnl_df[pnl_df['Particulars'].str.lower().str.contains('revenue')]
        cost_df = pnl_df[pnl_df['Particulars'].str.lower().str.contains('cost')]

        # Aggregate revenue and cost
        revenue = revenue_df.groupby(['Client', 'Month', 'Year'])['Amount'].sum().reset_index(name='Revenue')
        cost = cost_df.groupby(['Client', 'Month', 'Year'])['Amount'].sum().reset_index(name='Cost')

        # Merge revenue and cost
        margin_df = pd.merge(revenue, cost, on=['Client', 'Month', 'Year'], how='outer').fillna(0)

        # Compute margin and margin%
        margin_df['Margin'] = margin_df['Revenue'] - margin_df['Cost']
        margin_df['CM%'] = margin_df.apply(
            lambda row: round((row['Margin'] / row['Revenue']) * 100, 2) if row['Revenue'] != 0 else 0,
            axis=1
        )

        return margin_df

    except Exception as e:
        raise RuntimeError(f"Failed to compute margin: {e}")
