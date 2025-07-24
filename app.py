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

# Description in dark grey
st.markdown("""
<p style='color:#333333'>
Welcome to the <strong>LTTS BI Assistant</strong> — an AI-powered tool fo
