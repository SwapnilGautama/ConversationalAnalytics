import pandas as pd
import streamlit as st

def run(df_pnl, df_ut, user_question=None):
    st.markdown("### 📊 Revenue per Person Trends by Account")

    # Clean column names
    df_pnl.columns = df_pnl.columns.str.strip()
    df_ut.columns = df_ut.columns.str.strip()

    # ✅ Revenue logic
    revenue_df = df_pnl[
        (df_pnl['Group1'].isin(['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']))
    ].copy()

    if 'Amount in USD' not in revenue_df.columns:
        st.error("❌ 'Amount in USD' column not found in P&L data.")
        return

    # ✅ Use 'date_a' from UT for all temporal fields
    if 'date_a' not in df_ut.columns:
        st.error("❌ 'date_a' column not found in UT data.")
        return

    df_ut['Month'] = pd.to_datetime(df_ut['date_a'], errors='coerce').dt.to_period('M')
    df_pnl['Month'] = pd.to_datetime(df_pnl['Date'], errors='coerce').dt.to_period('M')

    # ✅ Join on overlapping fields
    join_cols = ['Segment', 'PVDG', 'PVDU', 'Exec DG', 'Exec DU',
                 'FinalCustomerName', 'Contract ID', 'Date', 'wbs id']
    available_cols = [col for col in join_cols if col in df_pnl.columns and col in df_ut.columns]

    if not available_cols:
        st.error("❌ No matching join columns found in both datasets.")
        return

    merged = pd.merge(
        revenue_df,
        df_ut,
        on=available_cols,
        how='inner'
    )

    if merged.empty:
        st.warning("⚠️ Merge resulted in empty dataset. Please verify join keys or data.")
        return

    # ✅ Revenue per Person calculation
    merged['Revenue'] = merged['Amount in USD']
    merged['Month'] = pd.to_datetime(merged['date_a'], errors='coerce').dt.to_period('M')
    merged = merged.dropna(subset=['Month'])

    if 'PSNo' not in merged.columns:
        st.error("❌ Column 'PSNo' not found for headcount calculation.")
        return

    # Group by Month, FinalCustomerName, and Segment/BU/DU
    merged['BU'] = merged['Exec DG']
    merged['DU'] = merged['Exec DU']
    merged['Segment'] = merged['Segment']
    merged['Account'] = merged['FinalCustomerName']

    # Pivot helper
    def build_pivot(index_dim):
        grouped = (
            merged.groupby(['Month', index_dim])
            .agg({
                'Revenue': 'sum',
                'PSNo': pd.Series.nunique
            })
            .reset_index()
        )
        grouped['Revenue per Person'] = grouped['Revenue'] / grouped['PSNo']
        pivot = grouped.pivot(index='Month', columns=index_dim, values='Revenue per Person')
        pivot = pivot.fillna(0).round(1)
        pivot.index = pivot.index.astype(str)
        return pivot

    # Build Subtabs
    tabs = st.tabs(["📊 By Segment", "🏢 By BU", "🏭 By DU"])
    dim_map = {'📊 By Segment': 'Segment', '🏢 By BU': 'BU', '🏭 By DU': 'DU'}

    for i, (tab, dim) in enumerate(dim_map.items()):
        with tabs[i]:
            st.markdown(f"#### Revenue per Person by Account and {dim}")
            pivot = build_pivot('Account' if dim == 'Segment' else dim)
            st.dataframe(pivot.reset_index(), hide_index=True)
