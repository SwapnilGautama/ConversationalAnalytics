
import pandas as pd
import streamlit as st

def run(prompt=None):
    st.title("📊 MoM Revenue vs C&B % of Revenue")

    # Load data
    df = pd.read_excel("sample_data/LnTPnL.xlsx")
    df['Period'] = pd.to_datetime(df['Period'], errors='coerce')
    df['Period'] = df['Period'].dt.to_period('M').astype(str)
    df = df[df['Group4'] == 'C&B']

    # Prompt and frequency selection
    trend_type = st.radio("Choose trend frequency", ["MoM", "QoQ", "YoY"], horizontal=True)

    # Summarize
    summary = df.groupby("Period").agg(
        CnB_Amount=("Amount in INR", lambda x: x[df['Type'] == "Cost"].sum()/1e7),
        Revenue=("Amount in INR", lambda x: x[df['Type'] == "Revenue"].sum()/1e7)
    ).reset_index()
    summary["C&B % of Revenue"] = (summary["CnB_Amount"] / summary["Revenue"]) * 100
    summary["MoM C&B Change (%)"] = summary["CnB_Amount"].pct_change().multiply(100).round(2)
    summary["MoM Revenue Change (%)"] = summary["Revenue"].pct_change().multiply(100).round(2)
    summary["Rev-C&B Movement Diff"] = summary["MoM Revenue Change (%)"] - summary["MoM C&B Change (%)"]

    # Total row
    total_row = pd.DataFrame([{
        "Period": "Total",
        "CnB_Amount": summary["CnB_Amount"].sum(),
        "Revenue": summary["Revenue"].sum(),
        "C&B % of Revenue": (summary["CnB_Amount"].sum() / summary["Revenue"].sum()) * 100,
        "MoM C&B Change (%)": summary["MoM C&B Change (%)"].sum(skipna=True),
        "MoM Revenue Change (%)": summary["MoM Revenue Change (%)"].sum(skipna=True),
        "Rev-C&B Movement Diff": summary["Rev-C&B Movement Diff"].sum(skipna=True)
    }])
    summary = pd.concat([summary, total_row], ignore_index=True)

    st.markdown("### Summary Table")

    # Safe style formatting
    def color_diff(val):
        if isinstance(val, float):
            return "color: green" if val >= 0 else "color: red"
        return ""

    styled = summary.style.format({
        "CnB_Amount": "{:.2f}",
        "Revenue": "{:.2f}",
        "C&B % of Revenue": "{:.2f}",
        "MoM C&B Change (%)": "{:.2f}",
        "MoM Revenue Change (%)": "{:.2f}",
        "Rev-C&B Movement Diff": "{:.2f}"
    }).applymap(color_diff, subset=["Rev-C&B Movement Diff"])       .set_properties(subset=pd.IndexSlice[[len(summary)-1], :], **{"font-weight": "bold"})       .set_table_styles([
        {"selector": "th.col0", "props": [("background-color", "#FDEBD0")]},
        {"selector": "th.col1", "props": [("background-color", "#D6EAF8")]},
        {"selector": "th.col2", "props": [("background-color", "#FADBD8")]},
        {"selector": "th.col3", "props": [("background-color", "#D5F5E3")]},
        {"selector": "th.col4", "props": [("background-color", "#F9E79F")]},
        {"selector": "th.col5", "props": [("background-color", "#E8DAEF")]},
        {"selector": "th.col6", "props": [("background-color", "#F5CBA7")]}
    ])

    st.dataframe(styled, use_container_width=True)
