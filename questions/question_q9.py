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

    # Clean currency formatting and strip whitespace
    df_revenue['Revenue'] = df_revenue['Revenue'].replace('[\$,]', '', regex=True).astype(float)
    df_headcount['Headcount'] = df_headcount['Headcount'].replace('[\$,]', '', regex=True).astype(float)
    df_revenue['Month'] = df_revenue['Month'].astype(str).str.strip()
    df_headcount['Month'] = df_headcount['Month'].astype(str).str.strip()

    # Aggregated Revenue and Headcount separately
    rev_agg = df_revenue.groupby(['Segment', 'Month'], as_index=False).agg({'Revenue': 'sum'})
    hc_agg = df_headcount.groupby(['Segment', 'Month'], as_index=False).agg({'Headcount': 'sum'})

    # Merge on Segment and Month only
    merged = pd.merge(rev_agg, hc_agg, on=['Segment', 'Month'], how='inner')
    merged['Revenue per Person'] = (merged['Revenue'] / merged['Headcount']).round(2)

    # Pivot tables for display
    rev_table = merged.pivot(index='Segment', columns='Month', values='Revenue').fillna(0).astype(int)
    hc_table = merged.pivot(index='Segment', columns='Month', values='Headcount').fillna(0).astype(int)
    rpp_table = merged.pivot(index='Segment', columns='Month', values='Revenue per Person').fillna(0).round(2)

    # Show in tabs
    tab1, tab2, tab3 = st.tabs(["Summary", "Segment", "BU", "DU"][:3])

    with tab1:
        st.subheader("Revenue per Person by Segment")
        st.dataframe(rpp_table.style.format("{:,.2f}"))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🔷 Total Revenue by Month")
            st.dataframe(rev_table.style.format("{:,.0f}"))
        with col2:
            st.markdown("### 🔷 Total Headcount by Month")
            st.dataframe(hc_table.style.format("{:,.0f}"))
