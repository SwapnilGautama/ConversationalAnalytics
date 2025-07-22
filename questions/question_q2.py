import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run(data, user_question):
    try:
        df = data.copy()

        # Normalize column names (strip spaces, standardize casing)
        df.columns = df.columns.str.strip()

        # Rename common inconsistencies
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

        cost_diff = cost_by_month[current_month] - cost_by_month[previous_month]
        rev_diff = rev_by_month[current_month] - rev_by_month[previous_month]

        margin_pct_current = (rev_by_month[current_month] - cost_by_month[current_month]) / cost_by_month[current_month] * 100
        margin_pct_prev = (rev_by_month[previous_month] - cost_by_month[previous_month]) / cost_by_month[previous_month] * 100

        st.subheader(f"Margin Drop Analysis for {Segment} Segment")

        # 🔹 TEXT SUMMARY
        st.markdown("### 🔍 Summary")
        st.markdown(f"""
        - **Revenue movement**: ₹{rev_diff:,.0f} (from ₹{rev_by_month[previous_month]:,.0f} to ₹{rev_by_month[current_month]:,.0f})
        - **Cost movement**: ₹{cost_diff:,.0f} (from ₹{cost_by_month[previous_month]:,.0f} to ₹{cost_by_month[current_month]:,.0f})
        """)

        # 🔍 COST GROUPS
        st.markdown("### 📊 Group-wise Cost Increase")

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

        st.dataframe(group_df)

        # 📈 CHART
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(group_df['Group'], group_df['Total Increase'], color='steelblue')
        ax.set_title("Group-wise Cost Increase")
        ax.set_ylabel("INR Increase")
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error running analysis: {e}")
