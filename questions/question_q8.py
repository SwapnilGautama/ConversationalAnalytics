import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def load_data():
    return pd.read_excel("sample_data/LNTDataSample.xlsx")

def run(df=None, user_question=None):
    st.title("Utilization % Trends")

    df = load_data()

    df["MonthName"] = df["Month"].apply(lambda x: pd.to_datetime(f"{x}", format="%m").strftime("%b"))

    df_filtered = df[df["Status"] == "Billable"]

    df_filtered["Date_a"] = pd.to_datetime(df_filtered["Date_a"])
    df_filtered["MonthYear"] = df_filtered["Date_a"].dt.to_period("M").astype(str)

    def pivot_table(df, index, values):
        return pd.pivot_table(
            df,
            index=index,
            columns="MonthName",
            values=values,
            aggfunc="sum",
            fill_value=0
        ).reindex(columns=["Apr", "May", "Jun"], fill_value=0)

    tabs = st.tabs(["BU-DU", "Segment"])

    # BU-DU Tab
    with tabs[0]:
        st.subheader("Utilization % by BU and DU")
        df_grouped = df_filtered.groupby(["BusinessUnit", "Delivery_Unit", "MonthName"]).agg({
            "NetAvailableHours": "sum",
            "TotalBillableHours": "sum"
        }).reset_index()

        df_grouped["Utilization %"] = (df_grouped["TotalBillableHours"] / df_grouped["NetAvailableHours"]) * 100

        ut_table = df_grouped.pivot_table(
            index=["BusinessUnit", "Delivery_Unit"],
            columns="MonthName",
            values="Utilization %",
            aggfunc="mean"
        ).reindex(columns=["Apr", "May", "Jun"], fill_value=0)

        st.dataframe(ut_table.style.format("{:.2f}"))

        st.markdown("##### 🔹 NetBillableHours")
        st.dataframe(
            pivot_table(df_filtered, ["BusinessUnit", "Delivery_Unit"], "TotalBillableHours").style.format("{:,.0f}")
        )

        st.markdown("##### 🔹 NetAvailableHours")
        st.dataframe(
            pivot_table(df_filtered, ["BusinessUnit", "Delivery_Unit"], "NetAvailableHours").style.format("{:,.0f}")
        )

    # Segment Tab
    with tabs[1]:
        st.subheader("Utilization % by Segment")
        df_seg = df_filtered.groupby(["Segment", "MonthName"]).agg({
            "NetAvailableHours": "sum",
            "TotalBillableHours": "sum"
        }).reset_index()
        df_seg["Utilization %"] = (df_seg["TotalBillableHours"] / df_seg["NetAvailableHours"]) * 100

        ut_seg_table = df_seg.pivot_table(
            index="Segment",
            columns="MonthName",
            values="Utilization %",
            aggfunc="mean"
        ).reindex(columns=["Apr", "May", "Jun"], fill_value=0)

        st.dataframe(ut_seg_table.style.format("{:.2f}"))

        st.markdown("##### 🔹 NetBillableHours")
        st.dataframe(
            pivot_table(df_filtered, ["Segment"], "TotalBillableHours").style.format("{:,.0f}")
        )

        st.markdown("##### 🔹 NetAvailableHours")
        st.dataframe(
            pivot_table(df_filtered, ["Segment"], "NetAvailableHours").style.format("{:,.0f}")
        )
