import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    df_revenue = pd.read_csv('sample_data/revenue.csv')
    df_headcount = pd.read_csv('sample_data/headcount.csv')
    return df_revenue, df_headcount

def run(df=None, user_question=None):
    st.title("Revenue per Person by Account")

    # Load data
    df_revenue, df_headcount = load_data()

    # Merge
    merged = pd.merge(
        df_revenue,
        df_headcount,
        on=["FinalCustomerName", "Month"],
        how="inner",
        suffixes=('_rev', '_head')
    )

    # Assign Segment, BU, DU
    merged['Segment'] = merged['Segment_rev']
    merged['BU'] = merged['BU_rev']
    merged['DU'] = merged['DU_rev']

    # Drop suffix columns
    merged = merged.drop(columns=[col for col in merged.columns if col.endswith('_rev') or col.endswith('_head')])

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
            st.subheader(f"Revenue per Person by {group_col}")

            # Aggregate revenue and headcount first
            agg = merged.groupby([group_col, 'Month']).agg({
                'Revenue': 'sum',
                'Headcount': 'sum'
            }).reset_index()

            # Calculate Revenue per Person
            agg['Revenue per Person'] = agg['Revenue'] / agg['Headcount']
            agg = agg.dropna(subset=['Revenue per Person'])

            # Pivot for display
            pivot = agg.pivot_table(index=group_col, columns='Month', values='Revenue per Person').fillna(0)
            pivot = pivot.reindex(columns=month_order, fill_value=0)
            pivot.index.name = row_label
            st.dataframe(pivot.style.format("{:,.0f}"), use_container_width=True)

            # Add grouped Total Revenue and Headcount tables
            revenue_pivot = agg.pivot_table(index=group_col, columns='Month', values='Revenue').reindex(columns=month_order, fill_value=0)
            headcount_pivot = agg.pivot_table(index=group_col, columns='Month', values='Headcount').reindex(columns=month_order, fill_value=0)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🔹 Total Revenue by Month")
                st.dataframe(revenue_pivot.style.format("{:,.0f}"), use_container_width=True)

            with col2:
                st.markdown("#### 🔹 Total Headcount by Month")
                st.dataframe(headcount_pivot.style.format("{:,.0f}"), use_container_width=True)

    render_table(tabs[0], 'FinalCustomerName', 'FinalCustomerName')
    render_table(tabs[1], 'Segment', 'Segment')
    render_table(tabs[2], 'BU', 'BU')
    render_table(tabs[3], 'DU', 'DU')
