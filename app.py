import streamlit as st
import openai
import difflib
from backend import get_answer  # your existing backend function

st.set_page_config(layout="wide")
st.title("📊 AI Business Insights Assistant")

# ✅ Prompt questions
prompt_questions = [
    "What is the current margin % for each client?",
    "Which cost triggered the margin drop last month in Transportation?",
    "How does C&B cost compare across quarters by segment?",
    "What is the M-o-M trend of C&B cost % with respect to total revenue?",
    "What is the client-wise revenue and cost summary for the last quarter?",
    "Highlight clients where realized rate has dropped sharply.",
    "Which segment has the most volatile margin %?",
    "Show the YoY revenue trend by client.",
    "Where has indirect cost grown disproportionately?",
    "Compare billed vs realized rate across clients."
]

# ✅ User input with live suggestions
user_input = st.text_input("Ask your business question:")

# ✅ Suggest closest match from prompt questions
if user_input:
    suggestions = difflib.get_close_matches(user_input, prompt_questions, n=3, cutoff=0.3)
    if suggestions:
        st.markdown("#### 💡 Suggestions:")
        for q in suggestions:
            if st.button(f"👉 {q}"):
                user_input = q
                st.experimental_rerun()

# ✅ Run only when input exists
if user_input:
    with st.spinner("Generating insights..."):
        response = get_answer(user_input)
    st.markdown("### 🧠 Insights")
    st.write(response["text"])

    if "table" in response:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📋 Table")
            st.dataframe(response["table"])
        with col2:
            if "chart" in response:
                st.markdown("### 📊 Chart")
                st.pyplot(response["chart"])

# ✅ Show prompt questions at the bottom
st.markdown("### 🤖 Sample Questions")
for q in prompt_questions:
    st.markdown(f"- *{q}*")
