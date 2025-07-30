import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Title
st.markdown("### Revenue per Person Analysis by Account")

# Load data directly from uploaded files
df_pnl = pd.read_excel("/mnt/data/LnTPnL.xlsx")
df_ut = pd.read_excel("/mnt/data/LNTData.xlsx")

# ✅ Fix: Use correct column name 'Date_a' (capital D)
if 'Date_a' not in df_ut.columns:
    st.error("'Date_a' column not found in LNTData.xlsx. Please ensure it exists.")
    st.stop()

# Ensure date format in UT data
df_ut['Date_a'] = pd.to_datetime(df_ut['Date_a'])
df_ut['Month'] = df_ut['Date_a'].dt.month

# Filter only billable resources
df_ut = df_ut[df_ut['Status'].str.lower().str.contains("bill", na=False)]

# Use the common join keys
common_keys = ['Company_code', 'Month']

# Prepare revenue data from P&L
df_revenue = df_pnl[df_pnl['Type'].str.lower() == 'revenue']
df_revenue = df_revenue.groupby(['Company_code', 'Month'])['Amount in USD'].sum().reset_index()

# Count FTEs from UT
df_ut = df_ut.groupby(['Company_code', 'Month'])['PSNo'].nunique().reset_index()
df_ut = df_ut.rename(columns={'PSNo': 'FTEs'})

# Merge the datasets
merged = pd.merge(df_revenue, df_ut, on=['Company_code', 'Month'], how='inner')
merged['Revenue per Person'] = merged['Amount in USD'] / merged['FTEs']

# Month map
df_ut['Month'] = df_ut['Month'].astype(int)
month_map = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
}
merged['Month'] = merged['Month'].map(month_map)

# Pivot for table format
table_df = merged.pivot_table(index='Company_code', columns='Month', values='Revenue per Person')
st.dataframe(table_df.style.format("{:.0f}"))

# Plot trend lines
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
