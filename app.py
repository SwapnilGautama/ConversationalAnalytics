# app.py

import streamlit as st
from utils.semantic_matcher import get_best_matching_question
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

# Prompt bank (Q1–Q10)
PROMPT_BANK = {
    "q1": "Which accounts had CM% < 30 in the last quarter?",
    "q2": "What caused the margin drop in Transportation?",
    "q3": "Show UT% trends for the last 2 quarters",
    "q4": "Which clients have the highest costs this year?",
    "q5": "Show YoY, QoQ and MoM revenue trends for a client",
    "q6": "Highlight accounts where realized rate dropped > $3 or $5",
    "q7": "What is the MoM headcount change for an account?",
    "q8": "Revenue per person trend by account",
    "q9": "Utilization % trend across accounts",
    "q10": "DU-wise fresher UT trends"
}

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
        best_qid = get_best_matching_question(user_question, PROMPT_BANK)
        st.info(f"🔍 Running analysis for: **{PROMPT_BANK[best_qid]}**")

        question_module = importlib.import_module(f"questions.question_{best_qid}")
        result = question_module.run(user_question, df)

        st.success("✅ Analysis complete.")

        # Display based on result type
        if isinstance(result, pd.DataFrame):
            st.dataframe(result)
        elif isinstance(result, str):
            st.markdown(result)
        elif isinstance(result, tuple):
            for item in result:
                if isinstance(item, pd.DataFrame):
                    st.dataframe(item)
                elif hasattr(item, "figure"):
                    st.pyplot(item.figure)
                elif isinstance(item, str):
                    st.markdown(item)
        else:
            st.write(result)

    except ModuleNotFoundError as e:
        st.error(f"❌ Could not load analysis script for {best_qid}: {e}")
    except Exception as e:
        st.error(f"❌ Error running analysis: {e}")
