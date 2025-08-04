import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    df_revenue = pd.read_csv('sample_data/revenue.csv')
    df_hours = pd.read_csv('sample_data/headcount.csv')  # using same file if NetAvailableHours lives here

    df_revenue['Revenue'] = df_revenue['Revenue'].replace('[\$,]', '', regex=True).astype(float)
    df_hours['NetAvailableHours'] = df_hours['NetAvailableHours'].replace('[\$,]', '', regex=True).astype(float)

    df_revenue['Month'] = df_revenue['Month'].astype(str).str.strip()
    df_hours['Month'] = df_hours['Month'].astype(str).str.strip()
    return df_revenue, df_hours

def pivot_summary(df, value_field, index_field='FinalCustomerName'):
    df_pivot = df.pivot(index=index_field, columns='Month', values=value_field).fillna(0)
    df_pivot = df_pivot[[m for m in ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'] if m in df_pivot.columns]]
    if value_field != 'Realized Rate':
        df_pivot = df_pivot.astype(int)
    else:
        df_pivot = df_pivot.round(2)
    return df_pivot

def generate_tab_view(df_revenue, df_hours, groupby_field, label):
    st.subheader(f"Realized Rate by {label}")
    rev = df_revenue.groupby([groupby_field, 'Month'], as_index=False)['Revenue'].sum()
    hrs = df_hours.groupby([groupby_field, 'Month'], as_index=False)['NetAvailableHours'].sum()
    df = pd.merge(rev, hrs, on=[groupby_field, 'Month'], how='outer')
    df['Revenue'] = df['Revenue'].fillna(0)
    df['NetAvailableHours'] = df['NetAvailableHours'].fillna(0)
    df['Realized Rate'] = df.apply(lambda row: round(row['Revenue'] / row['NetAvailableHours'], 2) if row['NetAvailableHours'] > 0 else 0, axis=1)

    st.dataframe(pivot_summary(df, 'Realized Rate', groupby_field))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💰 Total Revenue by Month")
        st.dataframe(pivot_summary(df, 'Revenue', groupby_field))
    with col2:
        st.markdown("### ⏱️ Total Net Available Hours by Month")
        st.dataframe(pivot_summary(df, 'NetAvailableHours', groupby_field))

def run(df=None, user_question=None):
    st.title("Realized Rate by Account")
    df_revenue, df_hours = load_data()

    with st.container():
        tabs = st.tabs(["Summary", "Segment", "BU", "DU"])
        with tabs[0]:
            st.subheader("Realized Rate by FinalCustomerName")
            merged = pd.merge(
                df_revenue.groupby(['FinalCustomerName', 'Month'], as_index=False)['Revenue'].sum(),
                df_hours.groupby(['FinalCustomerName', 'Month'], as_index=False)['NetAvailableHours'].sum(),
                on=['FinalCustomerName', 'Month'],
                how='outer'
            )
            merged['Revenue'] = merged['Revenue'].fillna(0)
            merged['NetAvailableHours'] = merged['NetAvailableHours'].fillna(0)
            merged['Realized Rate'] = merged.apply(
                lambda row: round(row['Revenue'] / row['NetAvailableHours'], 2) if row['NetAvailableHours'] > 0 else 0,
                axis=1
            )
            st.dataframe(pivot_summary(merged, 'Realized Rate', 'FinalCustomerName'))
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 💰 Total Revenue by Month")
                st.dataframe(pivot_summary(merged, 'Revenue', 'FinalCustomerName'))
            with col2:
                st.markdown("### ⏱️ Total Net Available Hours by Month")
                st.dataframe(pivot_summary(merged, 'NetAvailableHours', 'FinalCustomerName'))

        with tabs[1]:
            generate_tab_view(df_revenue, df_hours, 'Segment', 'Segment')
        with tabs[2]:
            generate_tab_view(df_revenue, df_hours, 'BU', 'BU')
        with tabs[3]:
            generate_tab_view(df_revenue, df_hours, 'DU', 'DU')
