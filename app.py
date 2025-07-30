# app.py

import streamlit as st
from utils.semantic_matcher import find_best_matching_qid, PROMPT_BANK
import importlib
from kpi_engine import margin, utilization  # 👈 Added utilization to load ut_df
import os
import pandas as pd
import inspect
import base64

PROMPT_BANK = [
    "List accounts with margin % less than 30% in the last quarter",
    "Which cost caused margin drop last month in Transportation?",
    "How much C&B varied from last quarter to this quarter?",
    "C&B cost as percentage of revenue trend",
    "What is FTE trend over months?",
    "How is utilization % trending?",
    "realized rate",
    "fresher ut trend"
]

if "autofill_text" not in st.session_state:
    st.session_state.autofill_text = ""

def handle_click(prompt):
    st.session_state.autofill_text = prompt

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

@st.cache_data
def load_ut_data():
    filepath = os.path.join("sample_data", "LNTData.xlsx")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"UT file not found at path: {filepath}")
    df = utilization.load_ut_data(filepath)
    df = utilization.preprocess_ut_data(df)
    return df

try:
    pnl_df = load_data()
    ut_df = load_ut_data()
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

st.set_page_config(page_title="LTTS BI Assistant", layout="wide")

# ✅ Logo Rendering (Centered)
def display_logo():
    logo_path = "sample_data/logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f"<div style='text-align: center; margin-top: -40px;'><img src='data:image/png;base64,{logo_base64}' width='220'/></div>",
            unsafe_allow_html=True
        )

display_logo()

# ✅ Updated Title – LTTS Blue Branding
st.markdown("""
<h1 style='text-align:center; font-family: "Segoe UI", sans-serif; font-size: 40px; color: #002D62; margin-top: -40px;'>
Conversational Analytics Assistant
</h1>
""", unsafe_allow_html=True)

# Description
st.markdown("""
<div style='text-align:center; font-size:18px; margin-bottom: 25px;'>
Welcome to the <b>LTTS BI Assistant</b> — an AI-powered tool for analyzing business trends using your P&L and utilization data.
</div>
""", unsafe_allow_html=True)

# 👉 Chat Input
user_question = st.text_input(
    label="👉 Start by typing your business question:",
    placeholder="e.g. List accounts with margin % less than 30% in the last quarter",
    value=st.session_state.autofill_text
)

# 🧠 Execute selected analysis script
if user_question:
    try:
        best_qid, matched_prompt = find_best_matching_qid(user_question)
        question_module = importlib.import_module(f"questions.question_{best_qid.lower()}")
        run_func = question_module.run
        run_params = inspect.signature(run_func).parameters

        if len(run_params) == 2:
            result = run_func(pnl_df, user_question)
        elif len(run_params) == 3:
            result = run_func(pnl_df, ut_df, user_question)
        else:
            result = run_func(pnl_df)

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

# 🔁 Prompt Bank
st.markdown("---")
st.markdown("💡 **Try asking:**")
col1, col2 = st.columns(2)
for i, prompt in enumerate(PROMPT_BANK):
    with col1 if i % 2 == 0 else col2:
        st.button(prompt, on_click=handle_click, args=(prompt,))
