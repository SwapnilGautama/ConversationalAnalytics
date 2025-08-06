# app.py

import streamlit as st
from utils.semantic_matcher import find_best_matching_qid, PROMPT_BANK
import importlib
from kpi_engine import margin
import os
import pandas as pd
import inspect
from PIL import Image
from io import BytesIO
import base64

PROMPT_BANK = [
    "List accounts with margin % less than 30% in the last quarter",
    "Which cost caused margin drop last month in Transportation?",
    "How much C&B varied from last quarter to this quarter?",
    "C&B cost as percentage of revenue trend",
    "What is FTE trend over months?",
    "How is utilization % trending?",
    "realized rate",
    "revenue per person",
    "fresher ut trend"
]

if "autofill_text" not in st.session_state:
    st.session_state.autofill_text = ""

if "clear_chat" not in st.session_state:
    st.session_state.clear_chat = False

def handle_click(prompt):
    st.session_state.autofill_text = prompt
    st.session_state.clear_chat = False

def clear_input():
    st.session_state.autofill_text = ""
    st.session_state.clear_chat = True

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

st.set_page_config(page_title="LTTS BI Assistant", layout="wide")

# ✅ Unified header with centered title + right-aligned logo
def display_header():
    logo_path = "sample_data/Logo.png"
    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
        buffered = BytesIO()
        logo.save(buffered, format="PNG")
        encoded_image = base64.b64encode(buffered.getvalue()).decode()

        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: -20px; margin-bottom: 10px;">
            <div style="flex: 1;"></div>
            <div style="flex: 2; text-align: center;">
                <h1 style='font-family: "Segoe UI", sans-serif; font-size: 38px; color: #002D62; margin: 0;'>
                    Conversational Analytics Assistant
                </h1>
            </div>
            <div style="flex: 1; text-align: right;">
                <img src="data:image/png;base64,{encoded_image}" width="140" />
            </div>
        </div>
        """, unsafe_allow_html=True)

# 🔁 Call the updated header
display_header()

# ✅ Welcome Text
st.markdown("""
<div style='text-align:center; font-size:18px; margin-bottom: 10px;'>
Welcome to <b>AIde</b> — an AI-powered tool for analyzing business trends using your P&L and utilization data.
</div>
""", unsafe_allow_html=True)

# 👉 Chat Input + Clear Button (Right Aligned)
chat_col, clear_col = st.columns([4, 1])
with chat_col:
    user_question = st.text_input(
        label="👉 Start by typing your business question:",
        placeholder="e.g. List accounts with margin % less than 30% in the last quarter",
        value=st.session_state.autofill_text
    )
with clear_col:
    if st.button("🧹 Clear Response"):
        clear_input()

# 🧠 Execute selected analysis script
if user_question and not st.session_state.clear_chat:
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

# 🔁 Prompt Bank
st.markdown("---")
st.markdown("💡 **Try asking:**")
col1, col2 = st.columns(2)
for i, prompt in enumerate(PROMPT_BANK):
    with col1 if i % 2 == 0 else col2:
        st.button(prompt, on_click=handle_click, args=(prompt,))
