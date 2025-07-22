# question_q2.py

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from io import BytesIO

def run(df_pnl: pd.DataFrame, user_input: str):
    try:
        # 🧠 Extract segment from user input
        import re
        segment_match = re.search(r"in (\w[\w\s&-]+)", user_input, re.IGNORECASE)
        segment = segment_match.group(1).strip() if segment_match else "Transportation"

        st.info(f"🔍 Running Q2 analysis for segment: **{segment}**")

        # 🧼 Basic cleanup
        df = df_pnl.copy()
        df['Month'] = pd.to_datetime(df['Month'])
        df['Amount in INR'] = pd.to_numeric(df['Amount in INR'], errors='coerce').fillna(0)

        # ✅ Filter to relevant segment
        df = df[df['Segment'].str.strip().str.lower() == segment.lower()]

        # 🧾 Separate Revenue and Cost
        df_revenue = df[df['Type'].str.lower() == 'revenue']
        df_cost = df[df['Type'].str.lower() == 'cost']

        # 📊 Aggregate revenue
        revenue_by_month = (
            df_revenue.groupby(['Company_Code', 'Month'])['Amount in INR']
            .sum()
            .reset_index()
            .rename(columns={'Amount in INR': 'Revenue'})
        )

        # 📊 Aggregate total cost
        cost_by_month = (
            df_cost.groupby(['Company_Code', 'Month'])['Amount in INR']
            .sum()
            .reset_index()
            .rename(columns={'Amount in INR': 'Cost'})
        )

        # 💹 Join revenue and cost
        pnl = pd.merge(revenue_by_month, cost_by_month, on=['Company_Code', 'Month'], how='outer').fillna(0)
        pnl['Margin %'] = ((pnl['Revenue'] - pnl['Cost']) / pnl['Cost'].replace(0, 1)) * 100

        # 🪜 Sort by Month and create lag columns
        pnl = pnl.sort_values(['Company_Code', 'Month'])
        pnl['Prev_Revenue'] = pnl.groupby('Company_Code')['Revenue'].shift(1)
        pnl['Prev_Cost'] = pnl.groupby('Company_Code')['Cost'].shift(1)
        pnl['Prev_Margin %'] = pnl.groupby('Company_Code')['Margin %'].shift(1)

        # 🎯 Focus on clients where Revenue stayed constant but Cost increased → Margin dropped
        pnl['Cost_Increase'] = pnl['Cost'] - pnl['Prev_Cost']
        pnl['Revenue_Change'] = pnl['Revenue'] - pnl['Prev_Revenue']
        pnl['Margin_Drop'] = pnl['Margin %'] - pnl['Prev_Margin %']

        condition = (
            (pnl['Cost_Increase'] > 0) &
            (abs(pnl['Revenue_Change']) < 0.05 * pnl['Prev_Revenue']) &
            (pnl['Margin_Drop'] < 0)
        )

        dropped_clients = pnl[condition].copy()
        if dropped_clients.empty:
            st.warning("No clients found with cost-triggered margin drop for the given segment.")
            return

        # 🔍 Deep dive into cost components
        latest_month = dropped_clients['Month'].max()
        prev_month = latest_month - pd.DateOffset(months=1)

        df_cost_latest = df_cost[df_cost['Month'] == latest_month]
        df_cost_prev = df_cost[df_cost['Month'] == prev_month]

        # ⛏️ Aggregate Group1–Group4 by Company_Code
        cost_groups = ['Group1', 'Group2', 'Group3', 'Group4']
        all_group_contrib = []

        for grp in cost_groups:
            group_cost_current = (
                df_cost_latest.groupby(['Company_Code', grp])['Amount in INR']
                .sum()
                .reset_index()
                .rename(columns={'Amount in INR': 'Current'})
            )
            group_cost_prev = (
                df_cost_prev.groupby(['Company_Code', grp])['Amount in INR']
                .sum()
                .reset_index()
                .rename(columns={'Amount in INR': 'Previous'})
            )
            group_merged = pd.merge(group_cost_current, group_cost_prev, on=['Company_Code', grp], how='outer').fillna(0)
            group_merged['Group'] = grp
            group_merged['GroupValue'] = group_merged[grp]
            group_merged['Increase'] = group_merged['Current'] - group_merged['Previous']
            all_group_contrib.append(group_merged[['Company_Code', 'Group', 'GroupValue', 'Increase']])

        cost_contrib_df = pd.concat(all_group_contrib)
        top_cost_causes = (
            cost_contrib_df.sort_values(['Company_Code', 'Increase'], ascending=[True, False])
            .groupby('Company_Code')
            .head(1)
            .reset_index(drop=True)
        )

        # 🔗 Merge with margin drop clients
        result = pd.merge(dropped_clients, top_cost_causes, on='Company_Code', how='left')
        final_cols = [
            'Company_Code', 'Month', 'Prev_Margin %', 'Margin %', 'Margin_Drop',
            'Prev_Cost', 'Cost', 'Cost_Increase', 'Group', 'GroupValue', 'Increase'
        ]
        st.subheader("📉 Clients with Margin Drop Caused by Cost Increase")
        st.dataframe(result[final_cols].sort_values('Margin_Drop'))

        # 📊 Chart: Cost increase by top clients
        fig, ax = plt.subplots(figsize=(10, 5))
        top_5 = result.nlargest(5, 'Cost_Increase')
        ax.bar(top_5['Company_Code'], top_5['Cost_Increase'], color='red')
        ax.set_title(f"Top 5 Cost Increases - {segment}")
        ax.set_ylabel("Cost Increase (INR)")
        st.pyplot(fig)

        # ✅ Done
    except Exception as e:
        st.error(f"Q2 execution failed: {e}")
