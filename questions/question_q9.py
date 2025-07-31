import streamlit as st
import pandas as pd
from kpi_engine.revenue_aggregated import get_revenue_aggregated
from kpi_engine.headcount_aggregated import get_headcount_aggregated

def run(df=None, user_question=None):
    st.title("Revenue per Person by Account")

    df_revenue = get_revenue_aggregated('sample_data/LnTPnL.xlsx')
    df_headcount = get_headcount_aggregated('sample_data/LNTData.xlsx')

    # ✅ Merge on fewer keys
    merged = pd.merge(
        df_revenue,
        df_headcount,
        on=["FinalCustomerName", "Month"],
        how="inner",
        suffixes=('_rev', '_head')
    )

    # ✅ Reassign Segment, BU, DU from revenue dataset
    merged['Segment'] = merged['Segment_rev']
    merged['BU'] = merged['BU_rev']
    merged['DU'] = merged['DU_rev']

    # ✅ Drop old suffix columns
    merged = merged.drop(columns=[col for col in merged.columns if col.endswith('_rev') or col.endswith('_head')])

    # 🔢 Calculate revenue per person
    merged['Revenue per Person'] = merged['Revenue'] / merged['Headcount']
    merged.dropna(subset=['Revenue per Person'], inplace=True)

    # 🗓️ Order months
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    merged['Month'] = pd.Categorical(merged['Month'], categories=month_order, ordered=True)

    # 📊 Tabs
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
