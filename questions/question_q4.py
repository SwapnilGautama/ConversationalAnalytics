import streamlit as st
import pandas as pd
import numpy as np
import re

def run(prompt):
    st.markdown("<h2 style='color:#4F8BF9'>📊 Revenue Trend Analysis</h2>", unsafe_allow_html=True)

    # Extract segment
    segment_match = re.search(r"\b(?:in|for)?\s*(Transportation|Media & Technology|Plant Engineering|Industrial Products|Med Tech)\b", prompt, re.IGNORECASE)
    segment_filter = segment_match.group(1) if segment_match else None

    df = pd.read_excel("sample_data/LnTPnL.xlsx", sheet_name="LnTPnL")
    df.columns = df.columns.str.strip()
    df['Year'] = df['Year'].astype(str)
    df['Month'] = df['Month'].astype(str).str.zfill(2)
    df['Period'] = df['Year'] + '-' + df['Month']

    if segment_filter and 'Segment' in df.columns:
        df = df[df['Segment'].str.lower() == segment_filter.lower()]

    df_rev = df[df['Type'].str.lower() == 'revenue'].copy()

    amount_col = 'Amount in INR'
    df_rev[amount_col] = pd.to_numeric(df_rev[amount_col], errors='coerce')

    df_summary = df_rev.groupby('Period')[amount_col].sum() / 1e6
    df_summary = df_summary.to_frame(name='Total Revenue (Million INR)')

    # Add C&B % of Revenue
    df_cb = df[df['Group4'] == 'C&B'].copy()
    df_cb['Amount in INR'] = pd.to_numeric(df_cb['Amount in INR'], errors='coerce')
    df_cb_grouped = df_cb.groupby('Period')['Amount in INR'].sum() / 1e6
    df_summary['C&B Cost (Million INR)'] = df_cb_grouped
    df_summary['C&B % of Revenue'] = (df_summary['C&B Cost (Million INR)'] / df_summary['Total Revenue (Million INR)']) * 100

    # Add Revenue Growth, C&B Growth
    df_summary['Revenue Growth %'] = df_summary['Total Revenue (Million INR)'].pct_change() * 100
    df_summary['C&B % Growth'] = df_summary['C&B % of Revenue'].pct_change() * 100
    df_summary['Growth Spread (Rev - C&B%)'] = df_summary['Revenue Growth %'] - df_summary['C&B % Growth']

    # Format
    def format_summary(df):
        df_rounded = df.round(2)
        total = df_rounded.sum(numeric_only=True)
        total['Growth Spread (Rev - C&B%)'] = df['Growth Spread (Rev - C&B%)'].mean()
        total_row = pd.DataFrame(total).T
        total_row.index = ['Total']
        styled = pd.concat([df_rounded, total_row])

        def style_func(val, col):
            if col == 'Growth Spread (Rev - C&B%)':
                return 'color: green; font-weight: bold' if val > 0 else 'color: red; font-weight: bold'
            return ''

        return styled.style\
            .applymap(lambda v: 'font-weight: bold', subset=pd.IndexSlice[['Total'], :])\
            .applymap(lambda v: style_func(v, 'Growth Spread (Rev - C&B%)'), subset=['Growth Spread (Rev - C&B%)'])\
            .set_table_styles(
                [
                    {'selector': 'thead tr:nth-child(1)', 'props': [('background-color', '#f4e1ff')]},
                    {'selector': 'thead tr:nth-child(2)', 'props': [('background-color', '#e0f7fa')]},
                    {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#f9f9f9')]},
                    {'selector': 'tbody tr:nth-child(odd)', 'props': [('background-color', '#ffffff')]}
                ],
                overwrite=False
            )

    st.markdown("### 📈 Summary Table")
    st.dataframe(format_summary(df_summary.reset_index()), use_container_width=True)

    # BU-wise Revenue
    st.markdown("### 🧾 Revenue Breakdown by BU and DU")
    df_rev['Period'] = df_rev['Period']
    pivot_bu = pd.pivot_table(df_rev, index='Period', columns='BU', values=amount_col, aggfunc='sum').fillna(0) / 1e6
    pivot_du = pd.pivot_table(df_rev, index='Period', columns='DU', values=amount_col, aggfunc='sum').fillna(0) / 1e6

    def style_table(pivot_df, pastel="#fcefdc"):
        df = pivot_df.copy()
        total_row = df.sum(numeric_only=True)
        total_row.name = 'Total'
        df = df.append(total_row)
        styled = df.round(1).style\
            .applymap(lambda v: 'font-weight: bold', subset=pd.IndexSlice[['Total'], :])\
            .set_table_styles(
                [
                    {'selector': 'thead tr', 'props': [('background-color', pastel)]},
                    {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#f9f9f9')]},
                    {'selector': 'tbody tr:nth-child(odd)', 'props': [('background-color', '#ffffff')]}
                ],
                overwrite=False
            )
        return styled

    st.markdown("#### Revenue by BU (Million INR)")
    st.dataframe(style_table(pivot_bu, pastel="#e6f4ea"), use_container_width=True)

    st.markdown("#### Revenue by DU (Million INR)")
    st.dataframe(style_table(pivot_du, pastel="#ffe7e7"), use_container_width=True)
