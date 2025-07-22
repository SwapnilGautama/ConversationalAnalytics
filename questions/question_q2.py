import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def run(df: pd.DataFrame, user_question: str = ""):
    try:
        # Filter only Transportation segment
        df_transport = df[df['Segment'].str.lower() == 'transportation'].copy()

        # Separate Revenue and Cost
        df_transport['Month'] = pd.to_datetime(df_transport['Month'])
        df_rev = df_transport[df_transport['Type'].str.lower() == 'revenue']
        df_cost = df_transport[df_transport['Type'].str.lower() == 'cost']

        # Aggregate Revenue
        rev_summary = df_rev.groupby(['Company_Code', 'Month'])['Amount in INR'].sum().reset_index()
        rev_summary = rev_summary.rename(columns={'Amount in INR': 'Revenue'})

        # Aggregate Total Cost and break up by cost groups
        cost_summary = df_cost.groupby(['Company_Code', 'Month']).agg({
            'Amount in INR': 'sum',
            'Group 1': 'first',
            'Group 2': 'first',
            'Group 3': 'first',
            'Group 4': 'first'
        }).reset_index()
        cost_summary = cost_summary.rename(columns={'Amount in INR': 'Total Cost'})

        # Merge revenue and cost
        merged = pd.merge(rev_summary, cost_summary, on=['Company_Code', 'Month'], how='outer').fillna(0)

        # Get last 2 months with data
        last_two_months = sorted(merged['Month'].unique())[-2:]
        df_curr = merged[merged['Month'] == last_two_months[1]].copy()
        df_prev = merged[merged['Month'] == last_two_months[0]].copy()

        # Rename for merging
        df_curr = df_curr.rename(columns={
            'Revenue': 'Revenue_Curr',
            'Total Cost': 'Cost_Curr',
            'Group 1': 'G1_Curr',
            'Group 2': 'G2_Curr',
            'Group 3': 'G3_Curr',
            'Group 4': 'G4_Curr'
        })

        df_prev = df_prev.rename(columns={
            'Revenue': 'Revenue_Prev',
            'Total Cost': 'Cost_Prev',
            'Group 1': 'G1_Prev',
            'Group 2': 'G2_Prev',
            'Group 3': 'G3_Prev',
            'Group 4': 'G4_Prev'
        })

        combined = pd.merge(df_curr, df_prev, on='Company_Code', how='outer').fillna(0)

        # Margin Calculations
        combined['Margin_Prev'] = combined['Revenue_Prev'] - combined['Cost_Prev']
        combined['Margin_Curr'] = combined['Revenue_Curr'] - combined['Cost_Curr']
        combined['Margin_Change'] = combined['Margin_Curr'] - combined['Margin_Prev']
        combined['Margin_%_Curr'] = ((combined['Margin_Curr']) / combined['Cost_Curr'].replace(0, 1)) * 100

        # Only show clients where margin dropped and revenue didn't drop more than 5%
        combined = combined[(combined['Margin_Change'] < 0) & ((combined['Revenue_Curr'] >= 0.95 * combined['Revenue_Prev']))]

        # Compute group-level changes
        combined['G1_Diff'] = combined['G1_Curr'] - combined['G1_Prev']
        combined['G2_Diff'] = combined['G2_Curr'] - combined['G2_Prev']
        combined['G3_Diff'] = combined['G3_Curr'] - combined['G3_Prev']
        combined['G4_Diff'] = combined['G4_Curr'] - combined['G4_Prev']

        output_cols = ['Company_Code', 'Revenue_Prev', 'Revenue_Curr', 'Cost_Prev', 'Cost_Curr',
                       'Margin_Prev', 'Margin_Curr', 'Margin_Change', 'Margin_%_Curr',
                       'G1_Diff', 'G2_Diff', 'G3_Diff', 'G4_Diff']

        st.subheader("📉 Clients with Margin Drop in Transportation")
        st.dataframe(combined[output_cols].sort_values(by='Margin_Change'))

        # Pie chart
        pie_data = combined.groupby('Company_Code')['Margin_Change'].sum().abs()
        st.subheader("🔍 Margin Drop Contribution by Client")
        fig, ax = plt.subplots()
        ax.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%')
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Failed to generate Q2 analysis: {e}")
