import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run(df_pnl: pd.DataFrame, df_ut: pd.DataFrame):
    st.title("Revenue per Person Analysis by Account")

    if df_pnl is None or df_ut is None:
        st.error("❌ Required data not found. Please upload both P&L and UT data files.")
        return

    # Use date_a for all time-based grouping
    df_ut['date_a'] = pd.to_datetime(df_ut['date_a'], errors='coerce')
    df_ut['Month'] = df_ut['date_a'].dt.month
    df_ut['Year'] = df_ut['date_a'].dt.year
    df_ut['Month_Year'] = df_ut['date_a'].dt.strftime('%b %Y')

    # Revenue calculation from P&L table
    df_revenue = df_pnl[df_pnl['Type'] == 'Revenue'].copy()
    df_revenue['Month'] = pd.to_datetime(df_revenue['Month'], errors='coerce').dt.month
    df_revenue['Month_Year'] = pd.to_datetime(df_revenue['Month'], errors='coerce').dt.strftime('%b %Y')
    df_revenue['FinalCustomerName'] = df_revenue['FinalCustomerName'].astype(str)

    revenue_grouped = df_revenue.groupby(['FinalCustomerName', 'Month', 'Month_Year'])[['Amount in USD']].sum().reset_index()
    revenue_grouped.rename(columns={'Amount in USD': 'Total Revenue'}, inplace=True)

    # Headcount calculation from UT
    df_ut['FinalCustomerName'] = df_ut['FinalCustomerName'].astype(str)
    hc_grouped = df_ut.groupby(['FinalCustomerName', 'Month', 'Month_Year'])['PSNo'].nunique().reset_index()
    hc_grouped.rename(columns={'PSNo': 'Headcount'}, inplace=True)

    # Merge revenue and headcount
    merged = pd.merge(revenue_grouped, hc_grouped, on=['FinalCustomerName', 'Month', 'Month_Year'], how='inner')
    merged['Revenue per Person'] = merged['Total Revenue'] / merged['Headcount']
    merged['Revenue per Person'] = merged['Revenue per Person'].fillna(0)

    # Metadata
    metadata_cols = ['Segment', 'PVDG', 'PVDU', 'FinalCustomerName', 'Month_Year']
    df_meta = df_ut[metadata_cols].drop_duplicates()
    merged = pd.merge(merged, df_meta, on=['FinalCustomerName', 'Month_Year'], how='left')

    # Tabs for Segment / BU / DU
    tab1, tab2, tab3 = st.tabs(["📊 Segment Level", "🏢 BU Level", "📌 DU Level"])
    for tab, col in zip([tab1, tab2, tab3], ['Segment', 'PVDG', 'PVDU']):
        with tab:
            if col not in merged.columns:
                st.warning(f"⚠️ Column '{col}' not found.")
                continue

            pivot = merged.pivot_table(values='Revenue per Person', index='Month_Year', columns=col, aggfunc='mean').round(2)

            st.dataframe(pivot.style.format("{:,.2f}").set_properties(**{
                'border-color': 'lightgrey',
                'border-width': '1px',
                'border-style': 'solid'
            }))

            fig, ax = plt.subplots(figsize=(12, 5))
            pivot.plot(ax=ax)
            ax.set_title(f"Revenue per Person Trend by {col}")
            ax.set_ylabel("USD")
            ax.set_xlabel("Month")
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            st.pyplot(fig)
