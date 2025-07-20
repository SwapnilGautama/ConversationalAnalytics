# app.py

import streamlit as st
import openai
import importlib
from utils.semantic_matcher import get_best_matching_question
from config.prompt_bank import PROMPT_BANK

# Set OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="LTTS BI Assistant", layout="wide")

# Header / Landing message
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

# User input
user_question = st.text_input("Ask your business question:", key="user_input")

# Session state for conversation history
if "history" not in st.session_state:
    st.session_state.history = []

# Response placeholder
response_container = st.container()

# Main app logic
if user_question:
    best_qid = get_best_matching_question(user_question, PROMPT_BANK)

    if best_qid:
        st.success(f"🔍 Running analysis for: **{PROMPT_BANK[best_qid]}**")

        try:
            # Dynamically import the appropriate module
            question_module = importlib.import_module(f"questions.question_{best_qid.lower()}")
            result = question_module.run(
                st.session_state.get("pnl_df"), 
                st.session_state.get("ut_df")
            )

            with response_container:
                st.write(result.get("summary"))
                if "table" in result:
                    st.dataframe(result["table"])
                if "chart" in result:
                    st.pyplot(result["chart"])

                st.session_state.history.append((user_question, result.get("summary")))
        except Exception as e:
            st.error(f"❌ Error running analysis: {e}")
    else:
        st.warning("⚠️ Couldn’t match your question. Try rephrasing or be more specific.")

# Suggestions
if user_question:
    st.markdown("---")
    st.info("**Try asking next:**\n- MoM headcount trend\n- Realized rate drop > $5\n- DU-wise fresher UT%")

# History
with st.expander("🔁 Show previous questions"):
    for i, (q, a) in enumerate(st.session_state.history[::-1]):
        st.markdown(f"**Q{i+1}:** {q}")
        st.markdown(f"_A:_ {a}")
