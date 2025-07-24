# app.py

import streamlit as st
from utils.semantic_matcher import find_best_matching_qid, PROMPT_BANK
import importlib
from kpi_engine import margin
import os
import pandas as pd
import inspect

# ✅ Add your custom PROMPT BANK here
PROMPT_BANK = [
    "_List accounts with margin % less than 30% in the last quarter_",
    "_Which cost caused margin drop last month in Transportation?_",
    "_How much C&B varied from last quarter to this quarter?_",
    "_What is M-o-M trend of C&B cost % w.r.t total revenue?_",
    "_What is FTE trend over months?_"
]

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

# Streamlit page config
st.set_page_config(page_title="LTTS BI Assistant", layout="wide")
st.title("📊 LTTS BI Assistant")

# Description
st.markdown("""
Welcome to the **Conversational Analytics Assistant** — an AI-powered tool for analyzing business trends using your P&L and utilization data.
""")

# 👉 Input box with autocomplete suggestions
user_question = st.text_input(
    label="👉 Start by typing your business question:",
    placeholder="e.g. List accounts with margin % less than 30% in the last quarter",
)

# Render result if input exists
if user_question:
    try:
        best_qid, matched_prompt = find_best_matching_qid(user_question)
        st.info(f"🔍 Running analysis for: **{matched_prompt}**")

        # ✅ Import question logic
        question_module = importlib.import_module(f"questions.question_{best_qid.lower()}")
        run_func = question_module.run
        run_params = inspect.signature(run_func).parameters

        # ✅ Run with or without question param
        if len(run_params) == 2:
            result = run_func(df, user_question)
        else:
            result = run_func(df)

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

# Always display the prompt bank (bottom)
st.markdown("---")
st.markdown("💡 **Try asking:**")
for prompt in PROMPT_BANK:
    st.markdown(f"- {prompt}")
