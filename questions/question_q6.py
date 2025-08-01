import streamlit as st
import pandas as pd
from kpi_engine.revenue_aggregated import get_revenue_aggregated
from kpi_engine.net_available_hours_aggregated import get_net_available_hours_aggregated

@st.cache_data
def load_data():
    df_revenue = get_revenue_aggregated('sample_data/LnTPnL.xlsx')
    df_hours = get_net_available_hours_aggregated('sample_data/LNTData.xlsx')
    return df_revenue, df_hours

def run(df=None, user_question=None):
    st.title("Realized Rate by Account")

    # Load data
    df_revenue, df_hours = load_data()

    # Merge
    merged = pd.merge(
        df_revenue,
        df_hours,
        on=["FinalCustomerName", "Month"],
        how="inner",
        suffixes=('_rev', '_hrs')
    )

    # Assign Segment, BU, DU
    merged['Segment'] = merged['Segment_rev']
    merged['BU'] = merged['BU_rev']
    merged['DU'] = merged['DU_rev']

    # Drop suffix columns
    merged = merged.drop(columns=[col for col in merged.columns if col.endswith('_rev') or col.endswith('_hrs')])

    # Calculate Realized Rate
    merged['Realized Rate'] = merged['Revenue'] / merged['NetAvailableHours']
    merged.dropna(subset=['Realized Rate'], inplace=True)

    # Month ordering
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    merged['Month'] = pd.Categorical(merged['Month'], categories=month_order, ordered=True)

    # 🧾 Sidebar filters
    st.sidebar.header("🔍 Filter")
    selected_segment = st.sidebar.multiselect("Select Segment", merged['Segment'].dropna().unique())
    selected_bu = st.sidebar.multiselect("Select BU", merged['BU'].dropna().unique())
    selected_du = st.sidebar.multiselect("Select DU", merged['DU'].dropna().unique())

    # Apply filters
    if selected_segment:
        merged = merged[merged['Segment'].isin(selected_segment)]
    if selected_bu:
        merged = merged[merged['BU'].isin(selected_bu)]
    if selected_du:
        merged = merged[merged['DU'].isin(selected_du)]

    # 📊 Tabs
    tabs = st.tabs(["Summary", "Segment", "BU", "DU"])

    def render_table(tab, group_col, row_label):
        with tab:
            st.subheader(f"Realized Rate by {group_col}")
            grouped = merged.groupby([group_col, 'Month'])['Realized Rate'].mean().reset_index()
            pivot = grouped.pivot_table(index=group_col, columns='Month', values='Realized Rate', aggfunc='mean').fillna(0)
            pivot = pivot.sort_index()
            pivot.index.name = row_label
            st.dataframe(pivot.style.format("{:,.0f}"), use_container_width=True)

    render_table(tabs[0], 'FinalCustomerName', 'FinalCustomerName')
    render_table(tabs[1], 'Segment', 'Segment')
    render_table(tabs[2], 'BU', 'BU')
    render_table(tabs[3], 'DU', 'DU')
