
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run(data, user_question):
    try:
        df = data.copy()
        df.columns = df.columns.str.strip()

        # Rename common inconsistencies
        col_map = {
            'Amount': 'Amount in INR',
            'amount in inr': 'Amount in INR',
            'Company Code': 'Company_code',
            'company_code': 'Company_code',
        }
        df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

        if 'Month' not in df.columns or 'Amount in INR' not in df.columns:
            st.error("Missing required columns: 'Month' or 'Amount in INR'")
            return

        df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
        df = df.dropna(subset=['Month'])

        df['Amount in INR'] = pd.to_numeric(df['Amount in INR'], errors='coerce')
        df = df.dropna(subset=['Amount in INR'])

        group_cols = ['Group1', 'Group2', 'Group3', 'Group4']
        for col in group_cols:
            if col not in df.columns:
                st.error(f"Missing expected column: {col}")
                return

        if 'Segment' not in df.columns:
            st.error("Missing expected column: Segment")
            return

        if 'Company_code' not in df.columns:
            st.error("Missing expected column: Company_code")
            return

        # Identify Segment
        Segment = None
        for s in df['Segment'].dropna().unique():
            if s.lower() in user_question.lower():
                Segment = s
                break

        if not Segment:
            st.warning("Could not identify Segment from your question.")
            return

        df = df[df['Segment'] == Segment]

        # Split cost vs revenue
        df_cost = df[df['Type'] == 'Cost']
        df_rev = df[df['Type'] == 'Revenue']

        cost_by_month = df_cost.groupby('Month')['Amount in INR'].sum().sort_index()
        rev_by_month = df_rev.groupby('Month')['Amount in INR'].sum().sort_index()

        if len(cost_by_month) < 2 or len(rev_by_month) < 2:
            st.warning("Not enough monthly data to compare.")
            return

        current_month = cost_by_month.index[-1]
        previous_month = cost_by_month.index[-2]

        cost_current = cost_by_month[current_month]
        cost_prev = cost_by_month[previous_month]
        rev_current = rev_by_month[current_month]
        rev_prev = rev_by_month[previous_month]

        margin_pct_current = (rev_current - cost_current) / cost_current * 100
        margin_pct_prev = (rev_prev - cost_prev) / cost_prev * 100

        margin_change_pct = margin_pct_current - margin_pct_prev
        cost_pct_change = ((cost_current - cost_prev) / cost_prev) * 100

        clients = df['Company_code'].unique()
        margin_health = []

        for client in clients:
            sub_cost = df_cost[df_cost['Company_code'] == client].groupby('Month')['Amount in INR'].sum()
            sub_rev = df_rev[df_rev['Company_code'] == client].groupby('Month')['Amount in INR'].sum()
            if previous_month in sub_cost and current_month in sub_cost and previous_month in sub_rev and current_month in sub_rev:
                cm_prev = (sub_rev[previous_month] - sub_cost[previous_month]) / sub_cost[previous_month]
                cm_curr = (sub_rev[current_month] - sub_cost[current_month]) / sub_cost[current_month]
                if cm_curr < cm_prev:
                    margin_health.append(client)

        # HEADER
        st.subheader(f"Margin Drop Analysis for {Segment} Segment")

        # SUMMARY
        st.markdown("### 🔍 Summary")
        st.markdown(f"""
        - **Segment margin dropped** by {abs(margin_change_pct):.1f}% (from {margin_pct_prev:.1f}% to {margin_pct_current:.1f}%)  
        - **{len(margin_health)} out of {len(clients)} clients** ({len(margin_health)/len(clients)*100:.1f}%) saw margin decline  
        - **Segment cost increased** by {cost_pct_change:.1f}% (₹{cost_prev/1e7:.2f} Cr → ₹{cost_current/1e7:.2f} Cr)
        """)

        # GROUP4 DRIVERS
        st.markdown("### 🔎 Group 4: Top Increasing Cost Drivers")

        df_g4 = df_cost[df_cost['Group4'].notna()]
        g4_costs = df_g4[df_g4['Group4'] != ''].copy()
        g4_costs = g4_costs[g4_costs['Month'].isin([previous_month, current_month])]
        pivot = g4_costs.pivot_table(index='Group4', columns='Month', values='Amount in INR', aggfunc='sum').fillna(0)
        pivot['% Change'] = ((pivot[current_month] - pivot[previous_month]) / pivot[previous_month].replace(0, 1e-5)) * 100
        pivot = pivot.sort_values('% Change', ascending=False).head(8)
        pivot = pivot.round(2)
        pivot.columns = ['May Cost (INR)', 'June Cost (INR)', '% Change']
        pivot['May Cost (Cr)'] = pivot['May Cost (INR)'] / 1e7
        pivot['June Cost (Cr)'] = pivot['June Cost (INR)'] / 1e7
        display_df = pivot[['May Cost (Cr)', 'June Cost (Cr)', '% Change']].reset_index()

        st.dataframe(display_df.style.format({'May Cost (Cr)': '{:.2f}', 'June Cost (Cr)': '{:.2f}', '% Change': '{:.1f}%'}))

    except Exception as e:
        st.error(f"Error running analysis: {str(e)}")
