# app.py

import streamlit as st
from semantic_matcher import get_best_matching_question
import importlib
import os
from kpi_engine import margin

# Load and cache data
@st.cache_data
def load_data():
    filepath = "LnTPnL.xlsx"
    df = margin.load_pnl_data(filepath)
    df = margin.preprocess_pnl_data(df)
    return df

df = load_data()

# UI
st.title("AI-Powered Business Insights Chatbot")

st.markdown("""
Welcome to the Business Insights Assistant!  
**This app uses the P&L data from the `LnTPnL.xlsx` file.**  
You can ask questions related to:
- Margins
- Cost breakdown
- Revenue trends
- Utilization
- Headcount and more

Example questions:
- "Which clients had a margin less than 30% last quarter?"
- "Which costs increased in the transportation account?"
""")

user_query = st.text_input("Ask your question:")

if user_query:
    matched_question_id = get_best_matching_question(user_query)

    if matched_question_id:
        st.markdown(f"**Matched Question:** {matched_question_id}")

        try:
            module_path = f"questions.question_{matched_question_id}"
            question_module = importlib.import_module(module_path)
            result = question_module.run(df)
            st.success("Here is the result:")
            st.write(result)
        except Exception as e:
            st.error(f"Failed to load or run question module: {e}")
    else:
        st.error("Could not understand your question.")
