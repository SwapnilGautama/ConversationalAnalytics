# ✅ FINAL Q9: Revenue per Person Trends by Account (fully working)
import streamlit as st
import pandas as pd
import re
from kpi_engine.revenue_aggregated import revenue_aggregated
from kpi_engine.headcount_aggregated import headcount_aggregated

def run(df_pnl, df_ut, user_question=None):
    st.title("Revenue per Person Analysis by Account")

    # ✅ Standardize column names
    df_pnl.columns = df_pnl.columns.str.strip()
    df_ut.columns = df_ut.columns.str.strip()

    # ✅ Dynamic Revenue Column
    revenue_col = next((col for col in df_pnl.columns if col.lower().replace(" ", "") in ['amountinusd', 'amount']), None)
    if not revenue_col:
        st.error("❌ Column not found: Amount in USD")
        return

    # ✅ Extract Segment if present
    segment_match = re.search(r"\b(?:in|for)?\s*(Transportation|Med Tech|Media & Technology|Plant Engineering|Industrial Products)\b",
                              user_question or "", re.IGNORECASE)
    segment_filter = segment_match.group(1) if segment_match else None

    # ✅ Load Revenue and Headcount Aggregated
    revenue_df = calculate_revenue(df_pnl, segment_filter)
    headcount_df = calculate_headcount(df_ut, segment_filter)

    # ✅ Merge on FinalCustomerName and Month
    merged_df = pd.merge(revenue_df, headcount_df, on=['FinalCustomerName', 'Month'], how='inner')
    merged_df['Revenue per Person'] = merged_df['Revenue'] / merged_df['Headcount']
    merged_df = merged_df.round(2)

    st.subheader("📊 Revenue per Person by Account and Month")
    st.dataframe(merged_df, hide_index=True)

    # ✅ Trend Line Chart
    st.subheader("📈 Trend: Revenue per Person")
    pivot = merged_df.pivot_table(index='Month', columns='FinalCustomerName', values='Revenue per Person')
    st.line_chart(pivot)

