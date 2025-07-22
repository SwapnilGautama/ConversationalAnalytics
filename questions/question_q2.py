import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from kpi_engine import margin as margin_module

def run(df, user_question=None):
    # Step 1: Compute margin
    margin_df = margin_module.compute_margin(df)

    # Step 2: Match segment from user question
    segment = None
    if user_question:
        all_segments = margin_df['Segment'].dropna().unique()
        for s in all_segments:
            if s.lower() in user_question.lower():
                segment = s
                break

    if not segment:
        return "❌ Could not identify a valid segment from your question."

    # Step 3: Filter for segment
    segment_df = margin_df[margin_df['Segment'].str.lower() == segment.lower()].copy()

    # Step 4: Parse latest and previous quarters
    quarter_order = sorted(segment_df['Quarter'].dropna().unique())[-2:]  # last 2 quarters
    if len(quarter_order) < 2:
        return "❌ Not enough data to compute quarter-on-quarter comparison."

    current_q, prev_q = quarter_order[1], quarter_order[0]
    curr_df = segment_df[segment_df['Quarter'] == current_q]
    prev_df = segment_df[segment_df['Quarter'] == prev_q]

    # Step 5: Prepare comparison table
    curr_df = curr_df.groupby('Client')['CM%'].mean().reset_index().rename(columns={'CM%': 'CM%_current'})
    prev_df = prev_df.groupby('Client')['CM%'].mean().reset_index().rename(columns={'CM%': 'CM%_previous'})

    comparison = pd.merge(curr_df, prev_df, on='Client', how='outer').fillna(0)
    comparison['CM%_Drop'] = comparison['CM%_previous'] - comparison['CM%_current']
    comparison = comparison.sort_values(by='CM%_Drop', ascending=False)

    # Step 6: Show summary and chart
    worst_clients = comparison.head(5)
    st.write(f"### Top 5 Clients with Highest Margin Drop in {segment}")
    st.dataframe(worst_clients)

    fig, ax = plt.subplots()
    ax.bar(worst_clients['Client'], worst_clients['CM%_Drop'], color='red')
    ax.set_ylabel("CM% Drop")
    ax.set_title(f"Margin Drop by Client - {segment}")
    st.pyplot(fig)

    return f"🟢 Analysis complete for segment **{segment}**. Highlighted top 5 clients with the steepest CM% drop from {prev_q} to {current_q}."
