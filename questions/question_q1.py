import pandas as pd
import streamlit as st
import re

def run(df, user_question=None):
    df.columns = df.columns.str.strip()

    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])
    df['Quarter'] = df['Month'].dt.to_period('Q')

    amount_col = next((col for col in df.columns if col.lower() in ['amount', 'amount in usd']), None)
    company_col = next((col for col in df.columns if 'company' in col.lower()), None)

    if amount_col is None or company_col is None or 'Type' not in df.columns:
        st.error("❌ Required columns not found.")
        return

    latest_q = df['Quarter'].max()

    rev_df = df[(df['Type'].str.lower() == 'revenue') & (df['Quarter'] == latest_q)]
    cost_df = df[(df['Type'].str.lower() == 'cost') & (df['Quarter'] == latest_q)]

    rev_by_client = rev_df.groupby(company_col)[amount_col].sum()
    cost_by_client = cost_df.groupby(company_col)[amount_col].sum()

    common_clients = rev_by_client.index.union(cost_by_client.index)
    data = []

    for client in common_clients:
        rev = rev_by_client.get(client, 0)
        cost = cost_by_client.get(client, 0)
        if rev == 0:
            continue
        margin_pct = ((rev - cost) / rev) * 100
        data.append({
            'Client': client,
            'Latest Margin %': round(margin_pct, 1),
            'Revenue (Million USD)': round(rev / 1e6, 2),
            'Cost (Million USD)': round(cost / 1e6, 2)
        })

    df_margin = pd.DataFrame(data)
    filtered_df = df_margin[df_margin['Latest Margin %'] < 30]

    total_clients = len(df_margin)
    low_margin_clients = len(filtered_df)
    percent = (low_margin_clients / total_clients) * 100 if total_clients else 0

    st.markdown("### 🧾 Accounts with Margin < 30.0% (non-zero revenue)")
    st.markdown(f"📌 **For the last quarter**, **{low_margin_clients} accounts** had an average margin below **30.0%** and non-zero revenue, which is **{percent:.1f}%** of all **{total_clients} accounts**.")
    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)
