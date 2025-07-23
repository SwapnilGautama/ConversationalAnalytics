# question_q2.py

import pandas as pd
import matplotlib.pyplot as plt

def run(df, user_question=None):
    import streamlit as st

    # Ensure consistent column names
    df.columns = df.columns.str.strip()

    # Convert month column to datetime
    df['Month'] = pd.to_datetime(df['Month'])

    # Get latest and previous month
    latest_month = df['Month'].max()
    prev_month = (latest_month - pd.DateOffset(months=1)).replace(day=1)

    # Segment detection from user input
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
    revenue_m = revenue_df.groupby(['Client', 'Month'])['Amount'].sum().unstack(fill_value=0)
    cost_m = cost_df.groupby(['Client', 'Month'])['Amount'].sum().unstack(fill_value=0)

    margin_m = (revenue_m - cost_m) / cost_m.replace(0, 1) * 100

    # Segment margin
    seg_rev = revenue_df.groupby('Month')['Amount'].sum()
    seg_cost = cost_df.groupby('Month')['Amount'].sum()
    seg_margin_pct = ((seg_rev - seg_cost) / seg_cost.replace(0, 1)) * 100

    # Insight 1: Margin % change
    try:
        margin_change = seg_margin_pct[latest_month] - seg_margin_pct[prev_month]
        margin_summary = f"{segment} margin {'increased' if margin_change > 0 else 'reduced'} {abs(margin_change):.1f}% from {prev_month.strftime('%b')} to {latest_month.strftime('%b')}, {'up' if margin_change > 0 else 'down'} from {seg_margin_pct[prev_month]:.1f}% to {seg_margin_pct[latest_month]:.1f}%."
    except:
        margin_summary = "Margin movement data unavailable."

    # Insight 2: Client margin drop
    client_margin_prev = ((revenue_m[prev_month] - cost_m[prev_month]) / cost_m[prev_month].replace(0, 1)) * 100
    client_margin_latest = ((revenue_m[latest_month] - cost_m[latest_month]) / cost_m[latest_month].replace(0, 1)) * 100
    client_movement = (client_margin_latest < client_margin_prev).sum()
    total_clients = len(client_margin_prev)
    client_summary = f"{client_movement} out of {total_clients} clients ({(client_movement/total_clients)*100:.1f}%) in {segment} saw a drop in margin."

    # Insight 3: Cost increase
    cost_prev = seg_cost.get(prev_month, 0)
    cost_latest = seg_cost.get(latest_month, 0)
    cost_growth = ((cost_latest - cost_prev) / cost_prev) * 100 if cost_prev else 0
    cost_summary = f"{segment} cost {'increased' if cost_growth > 0 else 'decreased'} by {abs(cost_growth):.1f}% from {prev_month.strftime('%b')} to {latest_month.strftime('%b')}."

    # Display insights
    st.markdown("### 🔍 Key Insights")
    st.markdown(f"- 📉 {margin_summary}")
    st.markdown(f"- 👥 {client_summary}")
    st.markdown(f"- 💸 {cost_summary}")

    # Group4 Cost Analysis
    group4_df = cost_df[['Month', 'Client', 'Amount', 'Group4']].copy()
    group4_df = group4_df.dropna(subset=['Group4'])

    g4 = group4_df.groupby(['Group4', 'Month'])['Amount'].sum().unstack(fill_value=0)

    if prev_month not in g4.columns or latest_month not in g4.columns:
        st.warning("Missing Group4 cost data for selected months.")
        return

    # % Share of total segment cost
    g4[prev_month] = (g4[prev_month] / seg_cost[prev_month]) * 100
    g4[latest_month] = (g4[latest_month] / seg_cost[latest_month]) * 100
    g4['% Change'] = ((g4[latest_month] - g4[prev_month]) / g4[prev_month].replace(0, 0.0001)) * 100

    # Rename columns
    g4 = g4.rename(columns={
        prev_month: f"{prev_month.strftime('%b')}",
        latest_month: f"{latest_month.strftime('%b')}"
    })

    # Round & Format
    g4 = g4.round(2)
    g4_fmt = g4.copy()
    g4_fmt[g4.columns[0]] = g4[g4.columns[0]].map(lambda x: f"{x:.2f}%")
    g4_fmt[g4.columns[1]] = g4[g4.columns[1]].map(lambda x: f"{x:.2f}%")
    g4_fmt['% Change'] = g4['% Change'].map(lambda x: f"{x:.2f}%")

    top8 = g4_fmt.sort_values(by='% Change', ascending=False).head(8).reset_index()

    # Layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"### 📊 Top 8 Group4 Cost Increases (as % of total segment cost)")
        st.dataframe(top8)

    with col2:
        g4_latest = g4[[g4.columns[1]]].copy().reset_index()
        g4_latest.columns = ['Group4', 'Share']
        g4_latest = g4_latest[g4_latest['Share'] > 0]

        top5 = g4_latest.sort_values(by='Share', ascending=False).head(5)
        others_share = max(0, 100 - top5['Share'].sum())
        pie_labels = list(top5['Group4']) + (['Others'] if others_share > 0 else [])
        pie_values = list(top5['Share']) + ([others_share] if others_share > 0 else [])

        fig, ax = plt.subplots()
        ax.pie(pie_values, labels=pie_labels, autopct='%1.1f%%', startangle=90)
        ax.set_title(f"Top Group4 Cost Types – {latest_month.strftime('%b')}")
        st.pyplot(fig)
