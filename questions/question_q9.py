import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Title
st.markdown("### Revenue per Person Analysis by Account")

df_pnl = st.session_state.get("df_pnl")
df_ut = st.session_state.get("df_ut")

if df_pnl is None or df_ut is None:
    st.error("❌ Required data not found. Please upload both P&L and UT data files.")
    st.stop()

# Ensure date format in UT data
df_ut['date_a'] = pd.to_datetime(df_ut['date_a'])
df_ut['Month'] = df_ut['date_a'].dt.month

# Filter only billable resources
df_ut = df_ut[df_ut['Status'].str.lower().str.contains("bill", na=False)]

# Use the common join keys
common_keys = [
    'Segment', 'PVDG', 'PVDU', 'Exec DG', 'Exec DU',
    'FinalCustomerName', 'Contract ID', 'wbs id'
]

# Add Month to P&L from date field
if 'Date' in df_pnl.columns:
    df_pnl['Date'] = pd.to_datetime(df_pnl['Date'])
    df_pnl['Month'] = df_pnl['Date'].dt.month

# Filter only revenue entries from P&L
df_revenue = df_pnl[df_pnl['Group1'].isin(["ONSITE", "OFFSHORE", "INDIRECT REVENUE"])]

# Aggregate revenue at the account/month level
revenue_group = df_revenue.groupby(common_keys + ['Month'], dropna=False).agg(
    Revenue=('Amount in USD', 'sum')
).reset_index()

# Aggregate UT to get headcount
ut_group = df_ut.groupby(common_keys + ['Month'], dropna=False).agg(
    Headcount=('PSNo', pd.Series.nunique)
).reset_index()

# Merge revenue and headcount
merged = pd.merge(revenue_group, ut_group, on=common_keys + ['Month'], how='inner')
merged['Revenue per Person'] = merged['Revenue'] / merged['Headcount']

# Prepare Month-Year label
month_map = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
             7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
merged['Month_Year'] = merged['Month'].map(month_map) + " 2025"

# Create tabbed layout
tabs = st.tabs(["📊 Segment Level", "🏢 BU Level", "🏗️ DU Level"])

with tabs[0]:
    pivot_seg = merged.pivot_table(index='Month_Year', columns='Segment', values='Revenue per Person', aggfunc='mean')
    st.dataframe(pivot_seg.style.format("{:.2f}"), use_container_width=True)

with tabs[1]:
    pivot_bu = merged.pivot_table(index='Month_Year', columns='PVDU', values='Revenue per Person', aggfunc='mean')
    st.dataframe(pivot_bu.style.format("{:.2f}"), use_container_width=True)

with tabs[2]:
    pivot_du = merged.pivot_table(index='Month_Year', columns='Exec DU', values='Revenue per Person', aggfunc='mean')
    st.dataframe(pivot_du.style.format("{:.2f}"), use_container_width=True)

st.success("✅ Revenue per Person analysis complete.")
