import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run(data, user_question):
    try:
        df = data.copy()

        # Clean column names
        df.columns = df.columns.str.strip()

        # Rename common variants
        if 'Amount' in df.columns:
            df.rename(columns={'Amount': 'Amount in INR'}, inplace=True)
        if 'amount in inr' in df.columns:
            df.rename(columns={'amount in inr': 'Amount in INR'}, inplace=True)
        if 'Company Code' in df.columns:
            df.rename(columns={'Company Code': 'Company_code'}, inplace=True)

        # Ensure essential columns exist
        expected_cols = ['Month', 'Amount in INR', 'Company_code', 'Segment', 'Type', 'Group1', 'Group2', 'Group3', 'Group4']
        for col in expected_cols:
            if col not in df.columns:
                st.error(f"Missing expected column: {col}")
                return

        df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
        df = df.dropna(subset=['Month'])

        df['Amount in INR'] = pd.to_numeric(df['Amount in INR'], errors='coerce')
        df = df.dropna(subset=['Amount in INR'])

        # Identify segment from user query
        Segment = None
        for s in df['Segment'].dropna().unique():
            if s.lower() in user_question.lower():
                Segment = s
                break

        if not Segment:
            st.warning("Could not identify Segment from your question.")
            return

        df = df[df['Segment'] == Segment]

        # Revenue and Cost split
        df_cost = df[df['Type'] == 'Cost']
        df_rev = df[df['Type'] == 'Revenue']

        # Monthly aggregates
        cost_by_month = df_cost.groupby('Month')['Amount in INR'].sum().sort_index()
        rev_by_month = df_rev.groupby('Month')['Amount in INR'].sum().sort_index()

        if len(cost_by_month) < 2 or len(rev_by_month) < 2:
            st.warning("Not enough monthly data to compare.")
            return

        current_month = cost_by_month.index[-1]
        previous_month = cost_by_month.index[-2]

        cost_curr, cost_prev = cost_by_month[current_month], cost_by_month[previous_month]
        rev_curr, rev_prev = rev_by_month[current_month], rev_by_month[previous_month]

        margin_curr = (rev_curr - cost_curr) / cost_curr * 100
        margin_prev = (rev_prev - cost_prev) / cost_prev * 100

        margin_change_pct = margin_curr - margin_prev
        cost_increase_pct = ((cost_curr - cost_prev) / cost_prev) * 100

        # Segment health: % of clients with margin drop
        df_cost_grouped = df_cost.groupby(['Month', 'Company_code'])['Amount in INR'].sum().unstack()
        df_rev_grouped = df_rev.groupby(['Month', 'Company_code'])['Amount in INR'].sum().unstack()

        margin_df = (df_rev_grouped - df_cost_grouped) / df_cost_grouped * 100
        margin_df = margin_df.dropna()
        if margin_df.shape[0] < 2:
            client_margin_change = pd.Series(dtype=float)
        else:
            client_margin_change = margin_df.iloc[-1] - margin_df.iloc[-2]
        num_clients = len(client_margin_change)
        clients_with_drop = (client_margin_change < 0).sum()
        segment_health_pct = (clients_with_drop / num_clients * 100) if num_clients > 0 else 0

        # Output Header
        st.subheader(f"Margin Drop Analysis for {Segment} Segment")

        # Summary Section
        st.markdown("### 🔍 Summary")
        st.markdown(f"""
        - **Margin**: {Segment} margin reduced **{abs(margin_change_pct):.2f}%** MoM — from **{margin_prev:.2f}%** to **{margin_curr:.2f}%**
        - **Segment health**: {clients_with_drop} out of {num_clients} clients (**{segment_health_pct:.1f}%**) saw a margin drop MoM
        - **Cost increase**: Segment cost rose **{cost_increase_pct:.2f}%** MoM
        """)

        # Group4 Cost Breakdown
        st.markdown("### 📊 Top Group4 Cost Drivers (MoM)")

        df_group4 = df_cost[df_cost['Group4'].notna()]
        df_group4 = df_group4[['Month', 'Group4', 'Amount in INR']]

        pivot = df_group4.pivot_table(index='Group4', columns='Month', values='Amount in INR', aggfunc='sum').fillna(0)
        pivot = pivot[[previous_month, current_month]]
        pivot['MoM % Change'] = ((pivot[current_month] - pivot[previous_month]) / pivot[previous_month].replace(0, 1)) * 100
        pivot = pivot.rename(columns={
            previous_month: f"{previous_month.strftime('%b-%Y')} (₹ Cr)",
            current_month: f"{current_month.strftime('%b-%Y')} (₹ Cr)"
        })
        pivot = pivot / 1e7  # Convert to ₹ Cr
        pivot = pivot.round(2)

        top_8 = pivot.sort_values(by='MoM % Change', ascending=False).head(8)
        st.dataframe(top_8)

        # Optional: Add Chart Here
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(top_8.index, top_8['MoM % Change'], color='darkorange')
        ax.set_title("Top Group4 Cost Drivers – MoM % Change")
        ax.set_ylabel("% Increase")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error running analysis: {e}")
