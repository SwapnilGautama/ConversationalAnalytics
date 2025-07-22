import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from kpi_engine import margin as margin_module
from kpi_engine.metadata import get_metadata

def run(df, user_question=None):
    # ✅ Compute margin table
    margin_df = margin_module.compute_margin(df)

    # ✅ Get valid segments from metadata
    metadata = get_metadata()
    valid_segments = set(metadata['Segment'].dropna().str.lower())

    # ✅ Extract segment from user question (case-insensitive match)
    segment = None
    if user_question:
        for seg in valid_segments:
            if seg in user_question.lower():
                segment = seg
                break

    if not segment:
        return "❌ Could not identify a valid segment from your question."

    # ✅ Filter margin table for selected segment
    filtered_df = margin_df[margin_df['Segment'].str.lower() == segment].copy()

    # ✅ Group by Client and Quarter and sum Revenue
    grouped = (
        filtered_df.groupby(['Client', 'Quarter'])['Revenue']
        .sum()
        .reset_index()
    )

    # ✅ Pivot to get Revenue by Client across Quarters
    pivot_df = grouped.pivot(index='Client', columns='Quarter', values='Revenue').fillna(0)

    # ✅ Sort quarters chronologically
    quarters = sorted(pivot_df.columns)
    if len(quarters) < 2:
        return "❌ Not enough data to compare two quarters."

    # ✅ Get last two quarters
    q_prev, q_curr = quarters[-2], quarters[-1]
    pivot_df['Revenue Drop'] = pivot_df[q_prev] - pivot_df[q_curr]
    pivot_df = pivot_df.sort_values('Revenue Drop', ascending=False)

    # ✅ Prepare result
    summary = f"📉 The biggest revenue drop in **{segment.title()}** from {q_prev} to {q_curr} occurred for the following clients:\n\n"
    top_clients = pivot_df.head(5)[['Revenue Drop']]
    summary += top_clients.to_markdown()

    # ✅ Plot chart
    fig, ax = plt.subplots()
    top_clients.plot(kind='bar', ax=ax, legend=False)
    ax.set_title(f'Revenue Drop by Client ({segment.title()})')
    ax.set_ylabel('Revenue Drop')
    st.pyplot(fig)

    return summary
