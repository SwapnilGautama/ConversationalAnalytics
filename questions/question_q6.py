import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    df_revenue = pd.read_csv('sample_data/revenue.csv')
    df_hours = pd.read_csv('sample_data/netavailablehours.csv')

    # Clean numeric fields
    df_revenue['Revenue'] = df_revenue['Revenue'].replace('[\$,]', '', regex=True).astype(float)
    df_hours['NetAvailableHours'] = df_hours['NetAvailableHours'].replace('[\$,]', '', regex=True).astype(float)

    df_revenue['Month'] = df_revenue['Month'].astype(str).str.strip()
    df_hours['Month'] = df_hours['Month'].astype(str).str.strip()

    # Add Quarter
    month_to_qtr = {'Jan': 'Q4', 'Feb': 'Q4', 'Mar': 'Q4',
                    'Apr': 'Q1', 'May': 'Q1', 'Jun': 'Q1',
                    'Jul': 'Q2', 'Aug': 'Q2', 'Sep': 'Q2',
                    'Oct': 'Q3', 'Nov': 'Q3', 'Dec': 'Q3'}
    df_revenue['Quarter'] = df_revenue['Month'].map(month_to_qtr)
    df_hours['Quarter'] = df_hours['Month'].map(month_to_qtr)

    return df_revenue, df_hours

def pivot_summary(df, value_field, index_field='FinalCustomerName'):
    df_grouped = df.groupby([index_field, 'Month'])[value_field].sum().reset_index()
    df_pivot = df_grouped.pivot(index=index_field, columns='Month', values=value_field).fillna(0)
    df_pivot = df_pivot[[m for m in ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'] if m in df_pivot.columns]]
    if value_field != 'Realized Rate':
        df_pivot = df_pivot.astype(int)
    else:
        df_pivot = df_pivot.round(2)
    return df_pivot

def apply_filters(df_revenue, df_hours, min_rate, max_rate, segment, bu, du, quarter):
    # ✅ FIX: Aggregate hours to avoid inflation
    df_hours_agg = df_hours.groupby(['FinalCustomerName', 'Month'], as_index=False)['NetAvailableHours'].sum()

    # Merge
    merged = pd.merge(
        df_revenue,
        df_hours_agg,
        on=['FinalCustomerName', 'Month'],
        how='inner'
    )

    merged['Revenue'] = merged['Revenue'].fillna(0)
    merged['NetAvailableHours'] = merged['NetAvailableHours'].fillna(0)
    merged['Realized Rate'] = merged.apply(
        lambda row: round(row['Revenue'] / row['NetAvailableHours'], 2) if row['NetAvailableHours'] > 0 else 0,
        axis=1
    )

    # Add back filters from df_revenue
    for col in ['Segment', 'BU', 'DU', 'Quarter']:
        if col in df_revenue.columns and col not in merged.columns:
            merged[col] = df_revenue.set_index(['FinalCustomerName', 'Month']).loc[
                pd.MultiIndex.from_frame(merged[['FinalCustomerName', 'Month']]), col
            ].values

    if segment != "All":
        merged = merged[merged['Segment'] == segment]
    if bu != "All":
        merged = merged[merged['BU'] == bu]
    if du != "All":
        merged = merged[merged['DU'] == du]
    if quarter != "All":
        merged = merged[merged['Quarter'] == quarter]
    merged = merged[(merged['Realized Rate'] >= min_rate) & (merged['Realized Rate'] <= max_rate)]

    return merged

def run(df=None, user_question=None):
    st.title("Realized Rate by Account")
    df_revenue, df_hours = load_data()

    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    min_rate = st.sidebar.number_input("Minimum Realized Rate", min_value=0.0, max_value=1000.0, value=0.0, step=0.1)
    max_rate = st.sidebar.number_input("Maximum Realized Rate", min_value=0.0, max_value=1000.0, value=1000.0, step=0.1)

    segment_list = ['All'] + sorted(df_revenue['Segment'].dropna().unique())
    segment = st.sidebar.selectbox("Segment", segment_list)

    bu_list = ['All'] + sorted(df_revenue['BU'].dropna().unique())
    bu = st.sidebar.selectbox("BU", bu_list)

    du_list = ['All'] + sorted(df_revenue['DU'].dropna().unique())
    du = st.sidebar.selectbox("DU", du_list)

    quarter_list = ['All'] + ['Q1', 'Q2', 'Q3', 'Q4']
    quarter = st.sidebar.selectbox("Quarter", quarter_list)

    # Filtered data
    filtered_df = apply_filters(df_revenue, df_hours, min_rate, max_rate, segment, bu, du, quarter)

    # Summary Header
    st.subheader("Realized Rate by FinalCustomerName")

    # Show % passing threshold
    df_hours_agg = df_hours.groupby(['FinalCustomerName', 'Month'], as_index=False)['NetAvailableHours'].sum()
    full_df = pd.merge(df_revenue, df_hours_agg, on=['FinalCustomerName', 'Month'], how='inner')
    full_df['Revenue'] = full_df['Revenue'].fillna(0)
    full_df['NetAvailableHours'] = full_df['NetAvailableHours'].fillna(0)
    full_df['Realized Rate'] = full_df.apply(
        lambda row: round(row['Revenue'] / row['NetAvailableHours'], 2) if row['NetAvailableHours'] > 0 else 0,
        axis=1
    )
    all_accounts = set(full_df['FinalCustomerName'].dropna().unique())
    filtered_accounts = set(filtered_df['FinalCustomerName'].dropna().unique())

    total_count = len(all_accounts)
    filtered_count = len(filtered_accounts)
    pct = round((filtered_count / total_count) * 100, 1) if total_count > 0 else 0

    st.markdown(f"✅ **{filtered_count} of {total_count} accounts** met the selected Realized Rate threshold (**{pct}%**)")

    # Table outputs
    st.markdown("### 💸 Realized Rate by Account")
    st.dataframe(pivot_summary(filtered_df, 'Realized Rate', 'FinalCustomerName'))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💰 Total Revenue by Month")
        st.dataframe(pivot_summary(filtered_df, 'Revenue', 'FinalCustomerName'))
    with col2:
        st.markdown("### ⏱️ Total Net Available Hours by Month")
        st.dataframe(pivot_summary(filtered_df, 'NetAvailableHours', 'FinalCustomerName'))
