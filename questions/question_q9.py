import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Title
st.markdown("### Revenue per Person Analysis by Account")

# Load data directly from deployed Excel files
df_pnl = pd.read_excel("sample_data/LnTPnL.xlsx")
df_ut = pd.read_excel("sample_data/LNTData.xlsx")

# Ensure 'date_a' exists before converting
if 'date_a' not in df_ut.columns:
    st.error("❌ 'date_a' column not found in LNTData.xlsx. Please ensure it exists.")
    st.stop()

# Parse date and extract Month
df_ut['date_a'] = pd.to_datetime(df_ut['date_a'], errors='coerce')
df_ut['Month'] = df_ut['date_a'].dt.month

# Filter only billable resources
if 'Status' in df_ut.columns:
    df_ut = df_ut[df_ut['Status'].str.lower().str.contains("bill", na=False)]

# Check required columns for aggregation
if 'Company_code' not in df_ut.columns or 'PSNo' not in df_ut.columns:
    st.error("❌ Required columns 'Company_code' or 'PSNo' missing in UT data.")
    st.stop()

# Use common join keys
common_keys = ['Company_code', 'Month']

# Prepare revenue data from P&L
df_revenue = df_pnl[df_pnl['Type'].str.lower() == 'revenue']
df_revenue = df_revenue.groupby(common_keys)['Amount in USD'].sum().reset_index()

# Prepare UT (FTEs)
df_ut = df_ut.groupby(common_keys)['PSNo'].nunique().reset_index()
df_ut = df_ut.rename(columns={'PSNo': 'FTEs'})

# Merge and calculate Revenue per Person
merged = pd.merge(df_revenue, df_ut, on=common_keys, how='inner')
merged['Revenue per Person'] = merged['Amount in USD'] / merged['FTEs']

# Month formatting
merged['Month'] = merged['Month'].astype(int)
month_map = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
}
merged['Month'] = merged['Month'].map(month_map)

# Pivot table
table_df = merged.pivot_table(index='Company_code', columns='Month', values='Revenue per Person')
st.dataframe(table_df.style.format("{:.0f}"))

# Plot chart
fig, ax = plt.subplots(figsize=(10, 5))
for company in merged['Company_code'].unique():
    data = merged[merged['Company_code'] == company]
    ax.plot(data['Month'], data['Revenue per Person'], marker='o', label=company)

ax.set_title("Revenue per Person Trend by Account")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue per Person")
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
ax.grid(True)
st.pyplot(fig)
