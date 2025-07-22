import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from kpi_engine import margin as margin_module

def run(df, user_query=None):
    # ✅ Recalculate margin table
    margin_df = margin_module.compute_margin(df)

    # ✅ Get segment from user query
    segment = None
    if user_query:
# ✅ Identify matching segment from query (case-insensitive partial match)
all_segments = margin_df['Segment'].dropna().unique()
segment = None
for s in all_segments:
    if s.lower() in user_query.lower():
        segment = s
        break

    if not segment:
        return "❌ Could not identify a valid segment from your question."

    # ✅ Filter for selected segment
    segment_df = margin_df[margin_df['Segment'].str.lower() == segment.lower()].copy()
    if segment_df.empty:
        return f"❌ No data available for segment '{segment}'."

    # ✅ Assign quarter
    segment_df['Quarter'] = segment_df['Month'].dt.to_period('Q')

    # ✅ Pivot to get margin by client & quarter
    pivot = segment_df.pivot_table(
        index='Client',
        columns='Quarter',
        values='Margin',
        aggfunc='sum',
        fill_value=0
    )

    # ✅ Check at least 2 quarters present
    if pivot.shape[1] < 2:
        return f"Only current quarter margin data is available for **{segment}** segment. Please add previous quarter data to compare changes."

    # ✅ Use last two quarters
    pivot = pivot.iloc[:, -2:]
    q1, q2 = pivot.columns

    pivot['Drop'] = pivot[q2] - pivot[q1]
    pivot['Abs Drop'] = pivot['Drop'].abs()

    # ✅ Sort by drop magnitude
    sorted_df = pivot.sort_values('Abs Drop', ascending=False).reset_index()

    # ✅ Display table
    st.markdown(f"### 💡 Margin Change Analysis for '{segment}' Segment ({q1} → {q2})")
    display_df = sorted_df[['Client', q1, q2, 'Drop']].rename(
        columns={q1: f"Margin {q1}", q2: f"Margin {q2}"}
    )
    st.dataframe(display_df)

    # ✅ Plot pie chart of absolute drop
    pie_df = sorted_df[sorted_df['Drop'] < 0].copy()
    if not pie_df.empty:
        plt.figure(figsize=(6, 6))
        plt.pie(pie_df['Abs Drop'], labels=pie_df['Client'], autopct='%1.1f%%', startangle=140)
        plt.title('🔻 Contribution to Total Margin Drop')
        st.pyplot(plt.gcf())

    return ""
