# question_q9.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from revenue_aggregated import revenue_aggregated
from headcount_aggregated import headcount_aggregated

def run(df=None, user_question=None):
    st.title("Revenue per Person by Account")

    # ✅ Load cleaned and aggregated revenue and headcount
    df_revenue = get_revenue_aggregated('sample_data/LnTPnL.xlsx')
    df_headcount = get_headcount_aggregated('sample_data/LNTData.xlsx')

    # ✅ Merge on FinalCustomerName, Month, and Segment
    merged = pd.merge(
        df_revenue,
        df_headcount,
        on=["FinalCustomerName", "Month", "Segment"],
        how="inner"
    )

    # ✅ Calculate Revenue per Person
    merged['Revenue per Person'] = merged['Revenue'] / merged['Headcount']
    merged = merged.dropna(subset=['Revenue per Person'])

    # ✅ Month ordering
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    merged['Month'] = pd.Categorical(merged['Month'], categories=month_order, ordered=True)

    tabs = st.tabs(["Segment", "BU", "DU"])

    def render_table(tab, group_by_col):
        with tab:
            st.subheader(f"Revenue per Person by {group_by_col}")
            grouped = merged.groupby([group_by_col, 'FinalCustomerName', 'Month'])['Revenue per Person'].mean().reset_index()
            pivot_table = grouped.pivot_table(
                index=['FinalCustomerName'],
                columns='Month',
                values='Revenue per Person',
                aggfunc='mean'
            ).fillna(0)
            st.dataframe(pivot_table.style.format("{:,.0f}"), use_container_width=True)

    render_table(tabs[0], "Segment")
    render_table(tabs[1], "BU")
    render_table(tabs[2], "DU")
