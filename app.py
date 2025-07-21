# app.py

import streamlit as st
from utils.semantic_matcher import find_best_matching_qid, PROMPT_BANK
import importlib
from kpi_engine import margin
import os
import pandas as pd

# ✅ Load data from sample_data folder
@st.cache_data
def load_data():
    filepath = os.path.join("sample_data", "LnTPnL.xlsx")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found at path: {filepath}")

    df = margin.load_pnl_data(filepath)
    df = margin.preprocess_pnl_data(df)

    if df.empty:
        raise ValueError("Loaded P&L data is empty after preprocessing.")

    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# ✅ Import correct prompt bank used for semantic matching
from utils.semantic_matcher import PROMPT_BANK

# Streamlit UI
st.set_page_config(page_title="LTTS BI Assistant", layout="wide")
st.title("📊 LTTS BI Assistant")

st.markdown("""
Welcome to the **LTTS BI Assistant** — an AI-powered tool for analyzing business trends using your P&L and utilization data.

✅ You can ask questions such as:
- *Which accounts had CM% < 30 in the last quarter?*
- *What caused the margin drop in Transportation?*
- *Show UT% trends for the last 2 quarters*

👉 **Start by typing your business question below**:
""")

# Input box
user_question = st.text_input("Ask your business question:")

# Main logic
if user_question:
    try:
        best_qid, matched_prompt = find_best_matching_qid(user_question)
        st.info(f"🔍 Running analysis for: **{matched_prompt}**")

        # ✅ Lowercase the QID for correct import
        question_module = importlib.import_module(f"questions.question_{best_qid.lower()}")

        # ✅ Pass user_question into run() if it accepts it
        if "user_query" in question_module.run.__code__.co_varnames or "query" in question_module.run.__code__.co_varnames:
            result = question_module.run(user_question, df)
        else:
            result = question_module.run(df)

        st.success("✅ Analysis complete.")
        if isinstance(result, pd.DataFrame):
            st.dataframe(result)
        elif isinstance(result, str):
            st.markdown(result)
        else:
            st.write(result)

    except ModuleNotFoundError as e:
        st.error(f"❌ Could not load analysis script for {best_qid}: {e}")
    except Exception as e:
        st.error(f"❌ Error running analysis: {e}")
