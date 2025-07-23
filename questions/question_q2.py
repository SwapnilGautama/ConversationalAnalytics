import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run(data, user_question):
    try:
        df = data.copy()
        df.columns = df.columns.str.strip()

        # Normalize columns
        df.columns = [col.strip().replace(" ", "_") for col in df.columns]

        # Fix inconsistent naming if any
        col_map = {
            'Amount': 'Amount_in_INR',
            'amount_in_inr': 'Amount_in_INR',
            'Amount_in_INR': 'Amount_in_INR',
            'Company_code': 'Company_Code',
            'company_code': 'Company_Code',
            'Company_Code': 'Company_Code'
        }
        df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

        # Required columns
        required_cols = ['Month', 'Amount_in_INR', 'Segment', 'Company_Code', 'Type',
                         'Group1', 'Group2', 'Group3', 'Group4']
        for col in required_cols:
            if col not in df.columns:
                st.error(f"Missing expected column: {col}")
                return

        df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
        df = df.dropna(subset=['Month'])

        df['Amount_in_INR'] = pd.to_numeric(df['Amount_in_INR'], errors='coerce')
        df = df.dropna(subset=['Amount_in_INR'])

        # Identify segment from user question
        segment_match = [s for s in df['Segment'].dropna().unique() if s.lower() in user_question.lower()]
        if not segment_match:
            st.warning("Could not identify Segment from your question.")
            return
        segment = segment_match[0]
        df = df[df['Segment'] == segment]

        df_cost = df[df['Type'] == 'Cost']
        df_rev = df[df['Type'] == 'Revenue']

        cost_by_month = df_cost.groupby('Month')['Amount_in_INR'].sum().sort_index()
        rev_by_month = df_rev.groupby('Month')['Amount_in_INR'].sum().sort_index()

        if len(cost_by_month) < 2 or len(rev_by_month) < 2:
            st.warning("Not enough monthly data to compare.")
            return

        current_month = cost_by_month.index[-1]
        previous_month = cost_by_month.index[-2]

        cost_curr = cost_by_month[current_month]
        cost_prev = cost_by_month[previous_month]
        rev_curr = rev_by_month[current_month]
        rev_prev = rev_by_month[previous_month]

        margin_curr_pct = (rev_curr - cost_curr) / cost_curr * 100
        margin_prev_pct = (rev_prev - cost_prev) / cost_prev * 100
        margin_diff_pct = margin_curr_pct - margin_prev_pct
        cost_pct_change = ((cost_curr - cost_prev) / cost_prev) * 100

        clients = df['Company_Code'].unique()
        margin_drop_clients = []

        for client in clients:
            sub_cost = df_cost[df_cost['Company_Code'] == client].groupby('Month')['Amount_in_INR'].sum()
            sub_rev = df_rev[df_rev['Company_Code'] == client].groupby('Month')['Amount_in_INR'].sum()
            if previous_month in sub_cost and current_month in sub_cost and previous_month in sub_rev and current_month in sub_rev:
                cm_prev = (sub_rev[previous_month] - sub_cost[previous_month]) / sub_cost[previous_month]
                cm_curr = (sub_rev[current_month] - sub_cost[current_month]) / sub_cost[current_month]
                if cm_curr < cm_prev:
                    margin_drop_clients.append(client)

        # HEADER
        st.subheader(f"Margin Drop Analysis for {segment} Segment")

        # SUMMARY
        st.markdown("### 🔍 Summary")
        st.markdown(f"""
        - **Segment margin dropped** by {abs(margin_diff_pct):.1f}% (from {margin_prev_pct:.1f}% to {margin_curr_pct:.1f}%)  
        - **{len(margin_drop_clients)} out of {len(clients)} clients** ({len(margin_drop_clients)/len(clients)*100:.1f}%) saw margin decline  
        - **Segment cost increased** by {cost_pct_change:.1f}% (₹{cost_prev/1e7:.2f} Cr → ₹{cost_curr/1e7:.2f} Cr)
        """)

        # GROUP4 DRIVERS
        st.markdown("### 🔎 Group 4: Top Increasing Cost Drivers")

        df_g4 = df_cost[df_cost['Group4'].notna()]
        df_g4 = df_g4[df_g4['Group4'] != '']
        df_g4 = df_g4[df_g4['Month'].isin([previous_month, current_month])]

        pivot = df_g4.pivot_table(index='Group4', columns='Month', values='Amount_in_INR', aggfunc='sum').fillna(0)
        pivot['% Change'] = ((pivot[current_month] - pivot[previous_month]) / pivot[previous_month].replace(0, 1e-5)) * 100
        pivot = pivot.sort_values('% Change', ascending=False).head(8)
        pivot = pivot.round(2)

        pivot.columns = ['May Cost (INR)', 'June Cost (INR)', '% Change']
        pivot['May Cost (Cr)'] = pivot['May Cost (INR)'] / 1e7
        pivot['June Cost (Cr)'] = pivot['June Cost (INR)'] / 1e7

        display_df = pivot[['May Cost (Cr)', 'June Cost (Cr)', '% Change']].reset_index()
        st.dataframe(display_df.style.format({
            'May Cost (Cr)': '{:.2f}', 
            'June Cost (Cr)': '{:.2f}', 
            '% Change': '{:.1f}%'
        }))

    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
