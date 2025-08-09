# app.py

import streamlit as st
st.set_page_config(page_title="LTTS BI Assistant", layout="wide")

from utils.semantic_matcher import find_best_matching_qid  # keep existing matcher
import importlib
from kpi_engine import margin
import os
import pandas as pd
import inspect
from PIL import Image
from io import BytesIO
import base64
import re
from datetime import datetime

# -----------------------------
# Prompt bank (preserving UX)
# -----------------------------
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

# -----------------------------
# Session state (preserved)
# -----------------------------
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

# -----------------------------
# Data loaders (preserved)
# -----------------------------
@st.cache_data
def load_pnl():
    filepath = os.path.join("sample_data", "LnTPnL.xlsx")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found at path: {filepath}")
    df = margin.load_pnl_data(filepath)
    df = margin.preprocess_pnl_data(df)
    if df.empty:
        raise ValueError("Loaded P&L data is empty after preprocessing.")
    return df

try:
    df_pnl = load_pnl()
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# -----------------------------
# Header (preserved)
# -----------------------------
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
                <h1 style='font-family: "Segoe UI", sans-serif; font-size: 40px; color: #002D62; margin: 0;'>
                    Conversational Analytics Assistant
                </h1>
            </div>
            <div style="flex: 1; text-align: right;">
                <img src="data:image/png;base64,{encoded_image}" width="140" />
            </div>
        </div>
        """, unsafe_allow_html=True)

display_header()

# -----------------------------
# Welcome text (preserved)
# -----------------------------
st.markdown("""
<div style='text-align:center; font-size:18px; margin-bottom: 10px;'>
Welcome to <b>AIde</b> — an AI-powered tool for analyzing business trends using your P&L and utilization data.
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Chat input + clear (preserved)
# -----------------------------
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

# =========================================================
# NEW: AI FALLBACK (router + opportunistic kpi_engine use)
# =========================================================

# Import optional KPI modules safely (FIX: no broken strings)
_optional_modules = {}
for mod in [
    "kpi_engine.revenue",
    "kpi_engine.revenue_aggregated",
    "kpi_engine.indirect_revenue",
    "kpi_engine.offshore_revenue",
    "kpi_engine.onsite_revenue",
    "kpi_engine.cost",
    "kpi_engine.margin",
    "kpi_engine.realized_rate",
    "kpi_engine.headcount",
    "kpi_engine.headcount_aggregated",
    "kpi_engine.resources",
    "kpi_engine.bench",
    "kpi_engine.billed_rate",
    "kpi_engine.net_available_hours_aggregated",
]:
    try:
        _optional_modules[mod] = importlib.import_module(mod)
    except Exception:
        _optional_modules[mod] = None

def _safe_has_cols(frame: pd.DataFrame, cols):
    return isinstance(frame, pd.DataFrame) and all(c in frame.columns for c in cols)

def _parse_time_filters(q: str):
    """
    Try to infer simple time filters from free text.
    Returns: dict with potential keys: month_from, month_to, year
    """
    ql = q.lower()
    out = {}
    now = datetime.now()

    if "this year" in ql:
        out["year"] = now.year
    if "last month" in ql:
        prev_month = (now.replace(day=1) - pd.DateOffset(days=1)).to_pydatetime()
        out["month_from"] = prev_month.strftime("%b %Y")
        out["month_to"] = now.strftime("%b %Y")

    # explicit "MMM YYYY" mentions
    m = re.findall(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+20\d{2}\b", q, flags=re.IGNORECASE)
    if m:
        m = [x.title() for x in m]
        if len(m) == 1:
            out["month_from"] = out["month_to"] = m[0]
        else:
            out["month_from"], out["month_to"] = m[0], m[1]
    return out

def _call_if_exists(mod, fn_names, *args, **kwargs):
    """
    Try a list of likely function names inside a module
    and call the first one that exists. Returns (succeeded, result_or_error).
    """
    if mod is None:
        return False, "Module not available"
    for name in fn_names:
        try:
            fn = getattr(mod, name, None)
            if callable(fn):
                sig = inspect.signature(fn)
                # try to be lenient: pass only the params that exist
                call_kwargs = {}
                for p in sig.parameters.values():
                    if p.name in kwargs:
                        call_kwargs[p.name] = kwargs[p.name]
                res = fn(*args, **call_kwargs)
                return True, res
        except Exception as e:
            return False, f"{name} failed: {e}"
    return False, "No known function fo
