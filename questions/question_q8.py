import streamlit as st
import pandas as pd
import numpy as np

def load_data():
    df = pd.read_excel("sample_data/LNTData.xlsx", sheet_name="LNTData")
    return df

def calculate_ut(df):
    df = df.copy()
    df['NetAvailableHours'] = pd.to_numeric(df['NetAvailableHours'], errors='coerce')
    df['TotalBillableHours'] = pd.to_numeric(df['TotalBillableHours'], errors='coerce')
    df = df[df['Status'] == 'Billable']
    df['UT%'] = (df['TotalBillableHours'] / df['NetAvailableHours']) * 100
    df = df.dropna(subset=['UT%', 'NetAvailableHours', 'TotalBillableHours'])
    df['Month'] = df['Month'].apply(lambda x: int(x) if not pd.isna(x) else x)
    month_order = [1,2,3,4,5,6,7,8,9,10,11,12]
    df['MonthName'] = pd.to_datetime(df['Month'], format='%m').dt.strftime('%b')
    df['MonthName'] = pd.Categorical(df['MonthName'], categories=[pd.to_datetime(m, format='%m').strftime('%b') for m in month_order], ordered=True)
    return df

def pivot_table(df, index_col, value_col):
    return pd.pivot_table(df, index=index_col, columns='MonthName', values=value_col, aggfunc='mean').round(2)

def agg_table(df, index_col, value_col):
    return pd.pivot_table(df, index=index_col, columns='MonthName', values=value_col, aggfunc='sum').round(0)

def run(df=None, user_question=None):
    st.title("Revenue per Person by Account")
    df = load_data() if df is None else df
    df = calculate_ut(df)

    tabs = st.tabs(["Summary", "BU", "DU", "Segment"])

    for i, groupby in enumerate(["FinalCustomerName", "BusinessUnit", "Delivery_Unit", "Segment"]):
        with tabs[i]:
            st.subheader(f"Utilization % by {groupby}")
            ut_table = pivot_table(df, groupby, 'UT%')
            st.dataframe(ut_table.style.set_caption(f"Avg UT% by {groupby} and Month"))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"### Total Net Available Hours by {groupby}")
                avail = agg_table(df, groupby, 'NetAvailableHours')
                st.dataframe(avail.style.set_caption("NetAvailableHours"))

            with col2:
                st.markdown(f"### Total Billable Hours by {groupby}")
                bill = agg_table(df, groupby, 'TotalBillableHours')
                st.dataframe(bill.style.set_caption("TotalBillableHours"))
