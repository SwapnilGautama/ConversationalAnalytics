# question_q2.py

import pandas as pd
import matplotlib.pyplot as plt

def run(df, user_question=None):
    import streamlit as st

    # Standardize column names
    df.columns = df.columns.str.strip()

    # Convert month column
    df['Month'] = pd.to_datetime(df['Month'])

    # Get latest and previous month
    latest_month = df['Month'].max()
    prev_month = (latest_month - pd.DateOffset(months=1)).replace(day=1)

    # Segment detection
    segment = "Transportation"
    if user_question:
        for seg in df['Segment'].dropna().unique():
            if seg.lower() in user_question.lower():
                segment = seg
                break

    df = df[df['Segment'] == segment]

    # Revenue and Cost
    revenue_df = df[df['Type'] == 'Revenue']
    cost_df = df[df['Type'] == 'Cost']

    # Margin by client
    revenue_m = revenue_df.groupby(['Client', 'Month'])['Amount in USD'].sum().unstack(fill_value=0)
    cost_m = cost_df.groupby(['Client', 'Month'])['Amount in USD'].sum().unstack(fill_value=0)

    margin_m = (revenue_m - cost_m) / revenue_m.replace(0, 1) * 100

    # Segment-level margin
    seg_rev = revenue_df.groupby('Month')['Amount in USD'].sum()
    seg_cost = cost_df.groupby('Month')['Amount in USD'].sum()
    seg_margin_pct = ((seg_rev - seg_cost) / seg_rev.replace(0, 1)) * 100

    # Insight 1: Margin movement
    try:
        margin_change = seg_margin_pct[latest_month] - seg_margin_pct[prev_month]
        margin_summary = f"{segment} margin {'increased' if margin_change > 0 else 'reduced'} {abs(margin_change):.1f}% from {prev_month.strftime('%b')} to {latest_month.strftime('%b')}, {'up' if margin_change > 0 else 'down'} from {seg_margin_pct[prev_month]:.1f}% to {seg_margin_pct[latest_month]:.1f}%."
    except:
        margin_summary = "Margin movement data unavailable."

    # Insight 2: Client margin drops
    client_margin_prev = ((revenue_m[prev_month] - cost_m[prev_month]) / revenue_m[prev_month].replace(0, 1)) * 100
    client_margin_latest = ((revenue_m[latest_month] - cost_m[latest_month]) / revenue_m[latest_month].replace(0, 1)) * 100
    client_movement = (client_margin_latest < client_margin_prev).sum()
    total_clients = len(client_margin_prev)
    client_summary = f"{client_movement} out of {total_clients} clients ({(client_movement/total_clients)*100:.1f}%) in {segment} saw a drop in margin."

    # Insight 3: Segment cost growth
    cost_prev = seg_cost.get(prev_month, 0)
    cost_latest = seg_cost.get(latest_month, 0)
    cost_growth = ((cost_latest - cost_prev) / cost_prev) * 100 if cost_prev else 0
    cost_summary = f"{segment} cost {'increased' if cost_growth > 0 else 'decreased'} by {abs(cost_growth):.1f}% from {prev_month.strftime('%b')} to {latest_month.strftime('%b')}."

    # Display insights
    st.markdown("### 🔍 Key Insights")
    st.markdown(f"- 📉 {margin_summary}")
    st.markdown(f"- 👥 {client_summary}")
    st.markdown(f"- 💸 {cost_summary}")

    # Group4 analysis
    group4_df = cost_df[['Month', 'Client', 'Amount in USD', 'Group4']].dropna(subset=['Group4'])
    g4 = group4_df.groupby(['Group4', 'Month'])['Amount in USD'].sum().unstack(fill_value=0)

    if prev_month not in g4.columns or latest_month not in g4.columns:
        st.warning("Missing Group4 cost data for selected months.")
        return

    g4_raw = g4.copy()
    g4['% Change'] = ((g4_raw[latest_month] - g4_raw[prev_month]) / g4_raw[prev_month].replace(0, 0.0001)) * 100

    # Identify top 8 drivers by absolute increase
    g4_raw['abs_change'] = (g4_raw[latest_month] - g4_raw[prev_month]).abs()
    top8 = g4_raw.sort_values(by='abs_change', ascending=False).head(8)

    # Final table
    table_df = pd.DataFrame({
        'Group4': top8.index,
        'May (Mn USD)': top8[prev_month] / 1e6,
        'Jun (Mn USD)': top8[latest_month] / 1e6,
        '% Change': g4.loc[top8.index, '% Change']
    })

    table_df['May (Mn USD)'] = table_df['May (Mn USD)'].map(lambda x: f"{x:,.2f}")
    table_df['Jun (Mn USD)'] = table_df['Jun (Mn USD)'].map(lambda x: f"{x:,.2f}")
    table_df['% Change'] = table_df['% Change'].map(lambda x: f"{x:.2f}%")

    # Layout: Table and Pie side-by-side
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"### 📊 Top 8 Group4 Cost Increases (actual cost in Mn USD, % change from {prev_month.strftime('%b')} to {latest_month.strftime('%b')})")
        st.dataframe(table_df)

    with col2:
        g4_latest_cost = g4_raw[latest_month]
        g4_latest_cost = g4_latest_cost[g4_latest_cost > 0].sort_values(ascending=False)

        top5 = g4_latest_cost.head(5)
        others = g4_latest_cost.iloc[5:].sum()
        pie_labels = list(top5.index) + (['Others'] if others > 0 else [])
        pie_values = list(top5.values) + ([others] if others > 0 else [])

        # Pastel color palette
        pastel_colors = ['#AEC6CF', '#FFB347', '#77DD77', '#FF6961', '#CBAACB', '#FFFACD']

        fig, ax = plt.subplots()
        ax.pie(pie_values, labels=pie_labels, autopct='%1.1f%%', startangle=90, colors=pastel_colors[:len(pie_values)])
        ax.set_title(f"Top Group4 Cost Types – {latest_month.strftime('%b')}")
        st.pyplot(fig)
