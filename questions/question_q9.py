import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Title
st.markdown("### Revenue per Person Analysis by Account")

# Load data
df_pnl = pd.read_excel("/mnt/data/LnTPnL.xlsx")
df_ut = pd.read_excel("/mnt/data/LNTData.xlsx")

# 🟢 Ensure date format in UT data
df_ut['Date_a'] = pd.to_datetime(df_ut['Date_a'], errors='coerce')
df_ut = df_ut.dropna(subset=['Date_a'])  # Drop rows with invalid dates
df_ut['Month'] = df_ut['Date_a'].dt.month

# 🟢 Filter only billable resources
df_ut = df_ut[df_ut['Status'].str.lower().str.contains("bill", na=False)]

# ✅ Group PnL revenue by Month only (no Company_code)
df_revenue = df_pnl[df_pnl['Type'].str.lower() == 'revenue']
df_revenue = df_revenue.groupby(['Month'])['Amount in USD'].sum().reset_index()

# ✅ Count FTEs from UT by Month only
df_ut_grouped = df_ut.groupby(['Month'])['PSNo'].nunique().reset_index()
df_ut_grouped = df_ut_grouped.rename(columns={'PSNo': 'FTEs'})

# ✅ Merge datasets by Month only
merged = pd.merge(df_revenue, df_ut_grouped, on='Month', how='inner')
merged['Revenue per Person'] = merged['Amount in USD'] / merged['FTEs']

# ✅ Month name mapping (FIXED LINE)
month_map = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
}
merged['Month'] = merged['Month'].map(month_map)

# ✅ Show table
st.dataframe(merged[['Month', 'Revenue per Person']].set_index('Month').style.format("{:.0f}"))

# ✅ Plot trend
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(merged['Month'], merged['Revenue per Person'], marker='o', color='steelblue')
ax.set_title("Revenue per Person Trend")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue per Person")
ax.grid(True)
st.pyplot(fig)
