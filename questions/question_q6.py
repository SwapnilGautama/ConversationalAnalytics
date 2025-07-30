import pandas as pd
import streamlit as st
from kpi_engine.revenue import calculate_revenue
from kpi_engine.utilization import calculate_utilization
from style_utils import style_table_grey_and_white

# Title
st.subheader("Accounts with Significant Realized Rate Drop")

# Inputs
threshold = st.number_input("Realized Rate Drop Threshold ($):", min_value=0.0, value=3.0)
segment_filter = st.text_input("Optional Segment Filter (leave blank for all):").strip().lower()

# Load data
try:
    pnl_df = st.session_state['pnl_df'].copy()
    ut_df = st.session_state['ut_df'].copy()
except:
    st.error("Required data not found in session_state.")
    st.stop()

# Clean and prepare date fields
if 'Month' in pnl_df.columns:
    pnl_df['Month'] = pd.to_datetime(pnl_df['Month'], errors='coerce')
    pnl_df['Quarter'] = pnl_df['Month'].dt.to_period('Q').astype(str)
    pnl_df['Year'] = pnl_df['Month'].dt.year
    pnl_df['Month_Year'] = pnl_df['Month'].dt.strftime('%b-%Y')
else:
    st.error("P&L data is missing 'Month' column.")
    st.stop()

if 'Month' in ut_df.columns:
    ut_df['Month'] = pd.to_datetime(ut_df['Month'], errors='coerce')
    ut_df['Quarter'] = ut_df['Month'].dt.to_period('Q').astype(str)
    ut_df['Year'] = ut_df['Month'].dt.year
    ut_df['Month_Year'] = ut_df['Month'].dt.strftime('%b-%Y')
else:
    st.error("UT data is missing 'Month' column.")
    st.stop()

# Filter by segment if provided
if segment_filter:
    pnl_df = pnl_df[pnl_df['Segment'].str.lower() == segment_filter]
    ut_df = ut_df[ut_df['Segment'].str.lower() == segment_filter]

# Compute Revenue (filtered to revenue entries only)
revenue_df = pnl_df[
    (pnl_df['Group1'].str.upper().isin(['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE'])) &
    (pnl_df['Type'].str.lower() == 'revenue')
]
revenue_grouped = revenue_df.groupby(['FinalCustomerName', 'Quarter'])['Amount in USD'].sum().reset_index()
revenue_grouped.rename(columns={'Amount in USD': 'Revenue'}, inplace=True)

# Compute Available Hours
ut_grouped = ut_df.groupby(['FinalCustomerName', 'Quarter'])['Net Available Hrs'].sum().reset_index()
ut_grouped.rename(columns={'Net Available Hrs': 'AvailableHrs'}, inplace=True)

# Merge and calculate Realized Rate
merged = pd.merge(revenue_grouped, ut_grouped, on=['FinalCustomerName', 'Quarter'], how='inner')
merged['RealizedRate'] = merged['Revenue'] / merged['AvailableHrs']

# Pivot to compare 2 most recent quarters
latest_quarters = sorted(merged['Quarter'].unique())[-2:]
if len(latest_quarters) < 2:
    st.warning("Not enough quarter data to compare.")
    st.stop()

pivot = merged.pivot(index='FinalCustomerName', columns='Quarter', values='RealizedRate')
pivot['Drop'] = pivot[latest_quarters[1]] - pivot[latest_quarters[0]]
pivot['DropAbs'] = pivot['Drop'].abs()

# Filter by threshold
result = pivot[pivot['DropAbs'] >= threshold].reset_index()
result = result[['FinalCustomerName', latest_quarters[0], latest_quarters[1], 'Drop']]
result.columns = ['FinalCustomerName', f'{latest_quarters[0]} Rate', f'{latest_quarters[1]} Rate', 'Rate Change']
result = result.sort_values(by='Rate Change')

# Show table
if result.empty:
    st.info("No accounts found with significant realized rate drop.")
else:
    st.dataframe(style_table_grey_and_white(result))
