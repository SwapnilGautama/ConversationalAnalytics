# ✅ FILE: questions/question_q1.py

import pandas as pd
import streamlit as st
from kpi_engine.cm_margin import compute_cm_margin  # Prebuilt KPI

def run_question(pnl_df: pd.DataFrame, ut_df: pd.DataFrame):
    st.subheader("Accounts with CM% < 30 in the Last Quarter")

    try:
        # ✅ Get CM% from KPI engine
        cm_df = compute_cm_margin(pnl_df)

        # ✅ Check expected columns
        required_columns = ["Quarter", "CM%", "Company Code"]
        for col in required_columns:
            if col not in cm_df.columns:
                st.error(f"Missing column in KPI output: {col}")
                return

        # ✅ Use most recent quarter
        latest_qtr = cm_df["Quarter"].max()
        st.write(f"🔎 Showing results for: **{latest_qtr}**")

        # ✅ Filter for CM% < 30
        filtered_df = cm_df[(cm_df["Quarter"] == latest_qtr) & (cm_df["CM%"] < 30)]

        if filtered_df.empty:
            st.success(f"No accounts had CM% < 30 in {latest_qtr}.")
            return

        # ✅ Show result
        st.write("📉 Accounts with low margin:")
        st.dataframe(filtered_df[["Company Code", "Quarter", "CM%"]])

    except Exception as e:
        st.error(f"❌ Error running Q1 logic: {e}")
