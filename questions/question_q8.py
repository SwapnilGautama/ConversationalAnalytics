import pandas as pd
import streamlit as st

def run(prompt=None):
    st.title("Utilization % Trends")

    @st.cache_data
    def load_data():
        df = pd.read_excel("sample_data/LNTData.xlsx")
        df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
        df['Month_Year'] = df['Date_a'].dt.strftime('%b')
        df['Quarter'] = df['Date_a'].dt.to_period("Q").astype(str)
        df['Year'] = df['Date_a'].dt.year
        df['NetAvailableHours'] = pd.to_numeric(df['NetAvailableHours'], errors='coerce')
        df['TotalBillableHours'] = pd.to_numeric(df['TotalBillableHours'], errors='coerce')
        df['UT%'] = (df['TotalBillableHours'] / df['NetAvailableHours']) * 100
        return df

    df = load_data()

    # Fix month order
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df['Month_Year'] = pd.Categorical(df['Month_Year'], categories=month_order, ordered=True)

    # Sidebar filters
    st.sidebar.header("Filters")
    segments = st.sidebar.multiselect("Segment:", df['Segment'].dropna().unique())
    bus = st.sidebar.multiselect("BU:", df['BusinessUnit'].dropna().unique())
    dus = st.sidebar.multiselect("DU:", df['Delivery_Unit'].dropna().unique())
    quarters = st.sidebar.multiselect("Quarter:", df['Quarter'].dropna().unique())

    df_filtered = df.copy()
    if segments:
        df_filtered = df_filtered[df_filtered['Segment'].isin(segments)]
    if bus:
        df_filtered = df_filtered[df_filtered['BusinessUnit'].isin(bus)]
    if dus:
        df_filtered = df_filtered[df_filtered['Delivery_Unit'].isin(dus)]
    if quarters:
        df_filtered = df_filtered[df_filtered['Quarter'].isin(quarters)]

    # Helper to build UT + side-by-side billable/available hours table
    def show_tables(df, group_cols, level_name):
        st.subheader(f"Utilization % by {level_name}")
        ut_pivot = df.groupby(group_cols + ['Month_Year'])['UT%'].mean().reset_index()
        ut_df = ut_pivot.pivot_table(index=group_cols, columns='Month_Year', values='UT%', aggfunc='mean').fillna(0)

        # Add Total row
        ut_df.loc['Total'] = ut_df.sum(numeric_only=True)
        st.dataframe(ut_df.style.format("{:.2f}"))

        # Side-by-side tables
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("🔷 **TotalBillableHours**")
            b_pivot = df.groupby(group_cols + ['Month_Year'])['TotalBillableHours'].sum().reset_index()
            b_df = b_pivot.pivot_table(index=group_cols, columns='Month_Year', values='TotalBillableHours').fillna(0)
            b_df.loc['Total'] = b_df.sum(numeric_only=True)
            st.dataframe(b_df.style.format("{:,.0f}"))

        with col2:
            st.markdown("🔷 **NetAvailableHours**")
            a_pivot = df.groupby(group_cols + ['Month_Year'])['NetAvailableHours'].sum().reset_index()
            a_df = a_pivot.pivot_table(index=group_cols, columns='Month_Year', values='NetAvailableHours').fillna(0)
            a_df.loc['Total'] = a_df.sum(numeric_only=True)
            st.dataframe(a_df.style.format("{:,.0f}"))

    # Tabs: BU, DU, Segment
    tabs = st.tabs(["🏢 BU Level", "🏭 DU Level", "📊 Segment Level"])

    with tabs[0]:
        show_tables(df_filtered, ['BusinessUnit'], "BU")

    with tabs[1]:
        show_tables(df_filtered, ['Delivery_Unit'], "DU")

    with tabs[2]:
        show_tables(df_filtered, ['Segment'], "Segment")
