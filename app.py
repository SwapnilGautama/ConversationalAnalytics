import streamlit as st
import openai
import importlib
from utils.semantic_matcher import get_best_matching_question
from config.prompt_bank import PROMPT_BANK
from config.openai_config import OPENAI_API_KEY

# Set OpenAI API Key
openai.api_key = OPENAI_API_KEY

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

# Question input
user_question = st.text_input("Ask your business question:", key="user_input")

# Placeholder for output
response_container = st.container()

# Optional: History to maintain conversational tone (reset each session)
if "history" not in st.session_state:
    st.session_state.history = []

# Run analysis and display result
if user_question:
    # Match user question to best Q1–Q10 match
    best_qid = get_best_matching_question(user_question, PROMPT_BANK)

    if best_qid:
        st.success(f"🔍 Running analysis for: **{PROMPT_BANK[best_qid]}**")

        # Dynamically import and run the matched question module
        try:
            question_module = importlib.import_module(f"questions.question_{best_qid.lower()}")
            result = question_module.run(user_question)

            # Show the result
            with response_container:
                st.write(result.get("summary"))
                if "table" in result:
                    st.dataframe(result["table"])
                if "chart" in result:
                    st.pyplot(result["chart"])

                # Save to history
                st.session_state.history.append((user_question, result.get("summary")))
        except Exception as e:
            st.error(f"❌ Error running the analysis: {e}")
    else:
        st.warning("Sorry, I couldn’t match your question to a known analysis. Try rephrasing.")

# Post-answer suggestions
if user_question:
    st.markdown("---")
    st.info("**You can also try asking:**\n- What is the M-o-M headcount trend?\n- Revenue per person by account\n- DU-wise fresher UT trends")

# Optional: Show Q&A history
with st.expander("🔁 Show previous questions"):
    for i, (q, a) in enumerate(st.session_state.history[::-1]):
        st.markdown(f"**Q{i+1}:** {q}")
        st.markdown(f"_A:_ {a}")
