# utilization.py

import pandas as pd
import os
import streamlit as st

@st.cache_data
def load_ut_data():
    filepath = os.path.join("sample_data", "LNTDataSample.xlsx")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found at: {filepath}")
    df = pd.read_excel(filepath)
    
    # Clean and standardize column names
    df.columns = df.columns.str.strip()
    
    # Calculate UT%
    df["UT%"] = (df["TotalBillableHours"] / df["NetAvailableHours"]) * 100
    df["Month"] = pd.to_datetime(df["Month"])
    df["Quarter"] = df["Month"].dt.to_period("Q")
    df["Year"] = df["Month"].dt.year.astype(str)
    
    return df


# ✅ Monthly trend for UT%
def get_ut_mom_trend(df, level="DU"):
    trend = df.groupby([pd.Grouper(key="Month", freq="M"), level])["UT%"].mean().reset_index()
    trend["Month"] = trend["Month"].dt.strftime("%Y-%m")
    return trend.pivot(index="Month", columns=level, values="UT%").fillna(0)


# ✅ Quarterly trend for UT%
def get_ut_qoq_trend(df, level="DU"):
    trend = df.groupby(["Quarter", level])["UT%"].mean().reset_index()
    trend["Quarter"] = trend["Quarter"].astype(str)
    return trend.pivot(index="Quarter", columns=level, values="UT%").fillna(0)


# ✅ Yearly trend for UT%
def get_ut_yoy_trend(df, level="DU"):
    trend = df.groupby(["Year", level])["UT%"].mean().reset_index()
    return trend.pivot(index="Year", columns=level, values="UT%").fillna(0)


# ✅ Agent-level UT%
def get_agent_ut(df):
    return df.groupby("EmployeeID")["UT%"].mean().reset_index().rename(columns={"UT%": "Avg UT%"})

# ✅ Filter by segment, DU, BU, account
def filter_ut(df, segment=None, du=None, bu=None, account=None):
    if segment:
        df = df[df["Segment"] == segment]
    if du:
        df = df[df["DU"] == du]
    if bu:
        df = df[df["BU"] == bu]
    if account:
        df = df[df["Account"] == account]
    return df
