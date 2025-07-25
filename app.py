# app.py

import streamlit as st
from utils.semantic_matcher import find_best_matching_qid, PROMPT_BANK
import importlib
from kpi_engine import margin
import os
import pandas as pd
import inspect
import base64

# ✅ Add your custom PROMPT BANK here
PROMPT_BANK = [
    "List accounts with margin % less than 30% in the last quarter",
    "Which cost caused margin drop last month in Transportation?",
    "How much C&B varied from last quarter to this quarter?",
    "What is M-o-M trend of C&B cost % w.r.t total revenue?",
    "What is FTE trend over months?"
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

# ✅ Centered Scalability Engineers logo
def display_logo():
    logo_path = "sample_data/logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f"<div style='text-align: center'><img src='data:image/png;base64,{logo_base64}' width='300'/></div>",
            unsafe_allow_html=True
        )

display_logo()

# ✅ Title with pastel Google-style multi-colored font
st.markdown("""
<h1 style="font-family: 'Segoe UI', sans-serif; font-size: 40px;">
  <span style="color:#AECBFA;">C</span>
  <span style="color:#F28B82;">o</span>
  <span style="color:#FBF476;">n</span>
  <span style="color:#CCFF90;">v</span>
  <span style="color:#AECBFA;">e</span>
  <span style="color:#F28B82;">r</span>
  <span style="color:#FBF476;">s</span>
  <span style="color:#CCFF90;">a</span>
  <span style="color:#AECBFA;">t</span>
  <span style="color:#F28B82;">i</span>
  <span style="color:#FBF476;">o</span>
  <span style="color:#CCFF90;">n</span>
  <span style="color:#AECBFA;">a</span>
  <span style="color:#F28B82;">l</span>
  &nbsp;
  <span style="color:#FBF476;">A</span>
  <span style="color:#CCFF90;">n</span>
  <span style="color:#AECBFA;">a</span>
  <span style="color:#F28B82;">l</span>
  <span style="color:#FBF476;">y</span>
  <span style="color:#CCFF90;">t</span>
  <span style="color:#AECBFA;">i</span>
  <span style="color:#F28B82;">c</span>
  <span style="color:#FBF476;">s</span>
  &nbsp;
  <span style="color:#CCFF90;">A</span>
  <span style="color:#AECBFA;">s</span>
  <span style="color:#F28B82;">s</span>
  <span style="color:#FBF476;">i</span>
  <span style="color:#CCFF90;">s</span>
  <span style="color:#AECBFA;">t</span>
  <span style="color:#F28B82;">a</span>
  <span style="color:#FBF476;">n</span>
  <span style="color:#CCFF90;">t</span>
</h1>
""", unsafe_allow_html=True)

# Description
st.markdown("""
Welcome to the **LTTS BI Assistant** — an AI-powered tool for analyzing business trends using your P&L and utilization data.
""")

# 🔁 Auto-fill logic for prompt clicks
if "autofill_text" not in st.session_state:
    st.session_state.autofill_text = ""

def handle_click(prompt):
    st.session_state.autofill_text = prompt

# 👉 Input box with autocomplete suggestions
user_question = st.text_input(
    label="👉 Start by typing your business question:",
    placeholder="e.g. List accounts with margin % less than 30% in the last quarter",
    value=st.session_state.autofill_text
)

# Render result if input exists
if user_question:
    try:
        best_qid, matched_prompt = find_best_matching_qid(user_question)

        question_module = importlib.import_module(f"questions.question_{best_qid.lower()}")
        run_func = question_module.run
        run_params = inspect.signature(run_func).parameters

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
    st.button(prompt, on_click=handle_click, args=(prompt,))
