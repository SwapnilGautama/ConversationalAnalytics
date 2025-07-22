import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def run(df, user_question=None):
    try:
        # Ensure necessary columns are present
        required_columns = ['Month', 'Company_code', 'segment', 'Type', 'Group 1', 'Group 2', 'Group 3', 'Group 4', 'Amount in INR']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return f"❌ Missing columns: {', '.join(missing_columns)}"

        # Convert Month to datetime
        df['Month'] = pd.to_datetime(df['Month'])

        # Filter for Transportation segment only
        df = df[df['segment'].str.lower() == 'transportation']

        # Split revenue and cost
        revenue_df = df[df['Type'].str.lower() == 'revenue']
        cost_df = df[df['Type'].str.lower() == 'cost']

        # Aggregate revenue and cost per company and month
        revenue_agg = revenue_df.groupby(['Company_code', 'Month'])['Amount in INR'].sum().reset_index(name='Revenue')
        cost_agg = cost_df.groupby(['Company_code', 'Month'])['Amount in INR'].sum().reset_index(name='Cost')

        # Merge revenue and cost
        merged = pd.merge(revenue_agg, cost_agg, on=['Company_code', 'Month'], how='inner')

        # Calculate margin and margin %
        merged['Margin'] = merged['Revenue'] - merged['Cost']
        merged['Margin %'] = ((merged['Revenue'] - merged['Cost']) / merged['Cost']) * 100

        # Get latest 2 months
        latest_months = sorted(merged['Month'].unique())[-2:]
        if len(latest_months) < 2:
            return "❌ Not enough data to compare two months."

        current_month, previous_month = latest_months[1], latest_months[0]
        current_df = merged[merged['Month'] == current_month]
        previous_df = merged[merged['Month'] == previous_month]

        # Merge current and previous month
        combined = pd.merge(current_df, previous_df, on='Company_code', suffixes=('_current', '_previous'))

        # Filter where margin dropped, but revenue remained ~same (within 5% tolerance)
        combined['Revenue_change_pct'] = 100 * (combined['Revenue_current'] - combined['Revenue_previous']) / combined['Revenue_previous'].replace(0, 1)
        combined['Margin_drop'] = combined['Margin_current'] < combined['Margin_previous']
        filtered = combined[(abs(combined['Revenue_change_pct']) < 5) & (combined['Margin_drop'])]

        if filtered.empty:
            return "✅ No clients with margin drop caused by stable revenue but increased costs."

        # Now analyze cost group breakdowns
        group_cols = ['Group 1', 'Group 2', 'Group 3', 'Group 4']
        cost_df = cost_df[cost_df['Company_code'].isin(filtered['Company_code']) & cost_df['Month'].isin(latest_months)]
        group_summary = cost_df.groupby(['Company_code', 'Month'])[group_cols].sum().reset_index()

        # Pivot to have current and previous group costs side-by-side
        pivot = group_summary.pivot(index='Company_code', columns='Month')[group_cols]
        pivot.columns = [f"{grp}_{dt.strftime('%b-%Y')}" for grp, dt in pivot.columns]
        pivot.reset_index(inplace=True)

        # Merge with filtered margin drop clients
        final = pd.merge(filtered, pivot, on='Company_code', how='left')

        # Calculate changes in group costs
        for grp in group_cols:
            col_prev = f"{grp}_{previous_month.strftime('%b-%Y')}"
            col_curr = f"{grp}_{current_month.strftime('%b-%Y')}"
            final[f"{grp}_change"] = final[col_curr] - final[col_prev]

        # Select top rows to show
        display_cols = ['Company_code', 'Revenue_previous', 'Revenue_current', 'Cost_previous', 'Cost_current',
                        'Margin_previous', 'Margin_current', 'Margin %_previous', 'Margin %_current'] + [f"{g}_change" for g in group_cols]
        st.subheader("🧾 Clients with Margin Drop Due to Increased Costs in Transportation")
        st.dataframe(final[display_cols].sort_values(by='Margin %_current').reset_index(drop=True))

        # Visual
        st.subheader("📊 Margin % Drop by Client")
        fig, ax = plt.subplots()
        ax.bar(final['Company_code'], final['Margin %_previous'] - final['Margin %_current'], color='red')
        ax.set_ylabel("Margin % Drop")
        ax.set_title("Clients with Margin % Drop (Revenue Stable)")
        st.pyplot(fig)

        return "✅ Analysis complete."

    except Exception as e:
        return f"❌ Error: {str(e)}"
