import pandas as pd
import streamlit as st
import os

from kpi_engine.utils import load_ut_data  # ⬅️ this should already exist

def run(pnl_df):
    st.markdown("## Q6. Realized Rate Analysis")

    # Load ut_df if not passed
    if isinstance(pnl_df, str):
        pnl_df = pd.read_excel(pnl_df)
    try:
        ut_df = load_ut_data()  # assume it takes no args and loads default file
    except Exception as e:
        st.error(f"Failed to load UT data: {e}")
        return

    # Proceed only if both are valid DataFrames
    if not isinstance(pnl_df, pd.DataFrame) or not isinstance(ut_df, pd.DataFrame):
        st.error("❌ One or more datasets could not be loaded as DataFrames.")
        return
