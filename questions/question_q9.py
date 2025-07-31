import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from kpi_engine.revenue_aggregated import get_revenue_aggregated
from kpi_engine.headcount_aggregated import get_headcount_aggregated

def run(df=None, user_question=None):
    st.title("Revenue per Person by Account")

    df_revenue = get_revenue_aggregated('sample_data/LnTPnL.xlsx')
    df_headcount = get_headcount_aggregated('sample_data/LNTData.xlsx')

    if df_revenue.empty or df_headcount.empty:
        st.error("Data loading failed. Please check input files.")
        return

    merged = pd.merge(
        df_revenue,
        df_headcount,
        on=["FinalCustomerName", "Segment", "BU", "DU", "Month"],
        how="inner"
    )

    merged['Revenue per Person'] = merged['Revenue'] / merged['Headcount']
    merged.dropna(subset=['Revenue per Person'], inplace=True)

    # Sort month
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    # Strip whitespace and drop invalid months
    merged['Month'] = merged['Month'].astype(str).str.strip()
    merged = merged[merged['Month'].isin(month_order)]
    merged['Month'] = pd.Categorical(merged['Month'], categories=month_order, ordered=True)


    tabs = st.tabs(["Segment", "BU", "DU"])

    def render_table(tab, group_col):
        with tab:
            st.subheader(f"Revenue per Person by {group_col}")
            grouped = merged.groupby([group_col, 'FinalCustomerName', 'Month'])['Revenue per Person'].mean().reset_index()
            pivot = grouped.pivot_table(index='FinalCustomerName', columns='Month', values='Revenue per Person', aggfunc='mean').fillna(0)
            st.dataframe(pivot.style.format("{:,.0f}"), use_container_width=True)

    render_table(tabs[0], "Segment")
    render_table(tabs[1], "BU")
    render_table(tabs[2], "DU")
