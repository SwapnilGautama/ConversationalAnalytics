import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run(data, user_question):
    try:
        df = data.copy()
        df.columns = df.columns.str.strip()

        if 'Amount' in df.columns:
            df.rename(columns={'Amount': 'Amount in INR'}, inplace=True)
        if 'amount in inr' in df.columns:
            df.rename(columns={'amount in inr': 'Amount in INR'}, inplace=True)
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
            st.error("Missing 'Segment' column")
            return

        Segment = None
        for s in df['Segment'].dropna().unique():
            if s.lower() in user_question.lower():
                Segment = s
                break
        if not Segment:
            st.warning("Could not identify Segment from your question.")
            return

        df = df[df['Segment'] == Segment]
        df_cost = df[df['Type'] == 'Cost']
        df_rev = df[df['Type'] == 'Revenue']

        cost_by_month = df_cost.groupby('Month')['Amount in INR'].sum().sort_index()
        rev_by_month = df_rev.groupby('Month')['Amount in INR'].sum().sort_index()
        if len(cost_by_month) < 2 or len(rev_by_month) < 2:
            st.warning("Not enough monthly data to compare.")
            return

        current_month = cost_by_month.index[-1]
        previous_month = cost_by_month.index[-2]

        cost_diff = cost_by_month[current_month] - cost_by_month[previous_month]
        rev_diff = rev_by_month[current_month] - rev_by_month[previous_month]

        margin_pct_current = (rev_by_month[current_month] - cost_by_month[current_month]) / cost_by_month[current_month] * 100
        margin_pct_prev = (rev_by_month[previous_month] - cost_by_month[previous_month]) / cost_by_month[previous_month] * 100

        # ✅ Top summary insights
        total_clients = df['Company_code'].nunique()
        clients_prev = df[(df['Type'] == 'Revenue') & (df['Month'] == previous_month)].groupby('Company_code')['Amount in INR'].sum()
        clients_curr = df[(df['Type'] == 'Revenue') & (df['Month'] == current_month)].groupby('Company_code')['Amount in INR'].sum()
        cost_prev = df[(df['Type'] == 'Cost') & (df['Month'] == previous_month)].groupby('Company_code')['Amount in INR'].sum()
        cost_curr = df[(df['Type'] == 'Cost') & (df['Month'] == current_month)].groupby('Company_code')['Amount in INR'].sum()
        margin_prev = (clients_prev - cost_prev) / cost_prev * 100
        margin_curr = (clients_curr - cost_curr) / cost_curr * 100
        margin_change = (margin_curr - margin_prev).dropna()
        margin_drop_clients = (margin_change < 0).sum()
        pct_drop = margin_drop_clients / total_clients * 100
        cost_pct_change = ((cost_by_month[current_month] - cost_by_month[previous_month]) / cost_by_month[previous_month]) * 100

        st.subheader(f"Margin Drop Analysis for {Segment} Segment")

        st.markdown("### 🔍 Summary")
        st.markdown(f"""
        - **{Segment} margin reduced {margin_pct_prev - margin_pct_current:.1f}%** from **{margin_pct_prev:.1f}% to {margin_pct_current:.1f}%** from **{previous_month.strftime('%B')} to {current_month.strftime('%B')}**
        - **{pct_drop:.0f}% of clients** in {Segment} saw margin drop ({margin_drop_clients} out of {total_clients})
        - **{Segment} cost increased {cost_pct_change:.1f}%** from ₹{cost_by_month[previous_month]/1e7:.2f} Cr to ₹{cost_by_month[current_month]/1e7:.2f} Cr
        """)

        # 🔍 Group-wise summary
        st.markdown("### 📊 Group-wise Cost Increase")

        group4_df = df_cost[df_cost['Group4'].notna()]
        group4_types = group4_df.groupby(['Group4', 'Month'])['Amount in INR'].sum().unstack().fillna(0)
        if previous_month not in group4_types.columns or current_month not in group4_types.columns:
            st.warning("Insufficient data for group 4 cost types")
            return
        group4_types['% Change'] = ((group4_types[current_month] - group4_types[previous_month]) / group4_types[previous_month].replace(0, 1)) * 100
        group4_types['% Change'] = group4_types['% Change'].round(1)
        group4_types['May'] = (group4_types[previous_month] / 1e7).round(2)
        group4_types['June'] = (group4_types[current_month] / 1e7).round(2)
        table_df = group4_types[['May', 'June', '% Change']].sort_values(by='% Change', ascending=False).head(8)
        table_df.index.name = 'Cost Type'
        st.dataframe(table_df)

        # 📈 Group-wise Chart
        group_summary = []
        for group in group_cols:
            monthly_group = df_cost.groupby(['Month'])[group].value_counts().unstack().fillna(0)
            monthly_group = monthly_group.apply(pd.to_numeric, errors='coerce')
            if monthly_group.shape[0] < 2:
                continue
            increase = (monthly_group.iloc[-1] - monthly_group.iloc[-2]).sum()
            group_summary.append((group, increase))
        group_df = pd.DataFrame(group_summary, columns=["Group", "Total Increase"])
        group_df = group_df.sort_values(by="Total Increase", ascending=False)
        st.bar_chart(group_df.set_index("Group"))

    except Exception as e:
        st.error(f"Error running analysis: {e}")
