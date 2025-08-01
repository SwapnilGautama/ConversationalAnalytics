
import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    df_revenue = pd.read_csv('sample_data/revenue.csv')
    df_headcount = pd.read_csv('sample_data/headcount.csv')
    df_revenue['Revenue'] = df_revenue['Revenue'].replace('[\$,]', '', regex=True).astype(float)
    df_headcount['Headcount'] = df_headcount['Headcount'].replace('[\$,]', '', regex=True).astype(float)
    df_revenue['Month'] = df_revenue['Month'].astype(str).str.strip()
    df_headcount['Month'] = df_headcount['Month'].astype(str).str.strip()
    return df_revenue, df_headcount

def pivot_summary(df, value_field, index_field='Segment'):
    df_pivot = df.pivot(index=index_field, columns='Month', values=value_field).fillna(0)
    df_pivot = df_pivot[[m for m in ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'] if m in df_pivot.columns]]
    if value_field != 'Revenue per Person':
        df_pivot = df_pivot.astype(int)
    else:
        df_pivot = df_pivot.round(2)
    return df_pivot

def generate_tab_view(df_revenue, df_headcount, groupby_field, label):
    st.subheader(f"Revenue per Person by {label}")
    rev = df_revenue.groupby([groupby_field, 'Month'], as_index=False)['Revenue'].sum()
    hc = df_headcount.groupby([groupby_field, 'Month'], as_index=False)['Headcount'].sum()
    df = pd.merge(rev, hc, on=[groupby_field, 'Month'], how='outer')
    df['Revenue'] = df['Revenue'].fillna(0)
    df['Headcount'] = df['Headcount'].fillna(0)
    df['Revenue per Person'] = df.apply(lambda row: round(row['Revenue'] / row['Headcount'], 2) if row['Headcount'] > 0 else 0, axis=1)

    st.dataframe(pivot_summary(df, 'Revenue per Person', groupby_field))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💰 Total Revenue by Month")
        st.dataframe(pivot_summary(df, 'Revenue', groupby_field))
    with col2:
        st.markdown("### 👥 Total Headcount by Month")
        st.dataframe(pivot_summary(df, 'Headcount', groupby_field))

def run(df=None, user_question=None):
    st.title("Revenue per Person by Account")
    df_revenue, df_headcount = load_data()

    with st.container():
        tabs = st.tabs(["Summary", "Segment", "BU", "DU"])
        with tabs[0]:
            st.subheader("Revenue per Person by Segment")
            merged = pd.merge(
                df_revenue.groupby(['Segment', 'Month'], as_index=False)['Revenue'].sum(),
                df_headcount.groupby(['Segment', 'Month'], as_index=False)['Headcount'].sum(),
                on=['Segment', 'Month'],
                how='outer'
            )
            merged['Revenue'] = merged['Revenue'].fillna(0)
            merged['Headcount'] = merged['Headcount'].fillna(0)
            merged['Revenue per Person'] = merged.apply(
                lambda row: round(row['Revenue'] / row['Headcount'], 2) if row['Headcount'] > 0 else 0,
                axis=1
            )
            st.dataframe(pivot_summary(merged, 'Revenue per Person'))
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 💰 Total Revenue by Month")
                st.dataframe(pivot_summary(merged, 'Revenue'))
            with col2:
                st.markdown("### 👥 Total Headcount by Month")
                st.dataframe(pivot_summary(merged, 'Headcount'))

        with tabs[1]:
            generate_tab_view(df_revenue, df_headcount, 'Segment', 'Segment')
        with tabs[2]:
            generate_tab_view(df_revenue, df_headcount, 'BU', 'BU')
        with tabs[3]:
            generate_tab_view(df_revenue, df_headcount, 'DU', 'DU')
