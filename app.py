# app.py

import streamlit as st
from utils.semantic_matcher import get_best_matching_question
import importlib
from kpi_engine import margin
import os

# ✅ Load data from sample_data folder
@st.cache_data
def load_data():
    filepath = os.path.join("sample_data", "LnTPnL.xlsx")
    df = margin.load_pnl_data(filepath)
    df = margin.preprocess_pnl_data(df)
    return df

df = load_data()

# Prompt bank (from Q1 to Q10)
PROMPT_BANK = {
    "q1": "Which accounts had CM% < 30 in the last quarter?",
    "q2": "What caused the margin drop in Transportation?",
    "q3": "Show UT% trends for the last 2 quarters",
    "q4": "Which clients have the highest costs this year?",
    # ... (q5 to q10, optional)
}

# Streamlit UI
st.set_page_config(page_title="LTTS BI Assistant", layout="wide")
st.title("📊 LTTS BI Assistant")

st.markdown("""
Welcome to the LTTS BI Assistant! This tool helps you analyze performance trends using P&L and Utilization data.

✅ Use this assistant to:
- Understand revenue, cost, margin, headcount, and utilization trends
- Ask natural language questions like:
    - "Which accounts had CM% < 30 in the last quarter?"
    - "What caused the margin drop in Transportation?"
    - "Show UT% trends for the last 2 quarters"

👉 Type your question below to get started:
""")

# Input box
user_question = st.text_input("Ask your business question:")

# Main logic
if user_question:
    try:
        best_qid = get_best_matching_question(user_question, PROMPT_BANK)
        st.info(f"🔍 Running analysis for: **{PROMPT_BANK[best_qid]}**")

        question_module = importlib.import_module(f"questions.question_{best_qid}")
        result = question_module.run(df)

        st.success("✅ Analysis complete.")
        st.write(result)

    except Exception as e:
        st.error(f"❌ Error running analysis: {e}")
