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

        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

display_header()

# -----------------------------
# Welcome text (preserved)
# -----------------------------
st.markdown(
    """
    <div style='text-align:center; font-size:18px; margin-bottom: 10px;'>
    Welcome to <b>AIde</b> — an AI-powered tool for analyzing business trends using your P&L and utilization data.
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Chat input + clear (preserved)
# -----------------------------
chat_col, clear_col = st.columns([4, 1])
with chat_col:
    user_question = st.text_input(
        label="👉 Start by typing your business question:",
        placeholder="e.g. List accounts with margin % less than 30% in the last quarter",
        value=st.session_state.autofill_text,
    )
with clear_col:
    if st.button("🧹 Clear Response"):
        clear_input()

# =========================================================
# AI FALLBACK (router + opportunistic kpi_engine use)
# =========================================================

# Optional KPI modules (import-guarded; code won’t break if missing)
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

    # explicit "MMM YYYY"
    m = re.findall(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+20\d{2}\b", q, flags=re.IGNORECASE)
    if m:
        m = [x.title() for x in m]
        if len(m) == 1:
            out["month_from"] = out["month_to"] = m[0]
        else:
            out["month_from"], out["month_to"] = m[0], m[1]
    return out

def _generic_margin_summary(df: pd.DataFrame, user_q: str):
    st.subheader("AI Fallback — General Summary")
    _ = _parse_time_filters(user_q)

    if _safe_has_cols(df, ["Type", "Amount in INR"]):
        if "Month" in df.columns:
            g = df.groupby(["Month", "Type"], dropna=False)["Amount in INR"].sum().reset_index()
            st.markdown("**Monthly Revenue/Cost**")
            st.dataframe(g)

        pivot = df.pivot_table(values="Amount in INR", index=None, columns="Type", aggfunc="sum", fill_value=0)
        if isinstance(pivot, pd.DataFrame):
            rev = float(pivot["Revenue"].iloc[0]) if "Revenue" in pivot.columns else 0.0
            cost = float(pivot["Cost"].iloc[0]) if "Cost" in pivot.columns else 0.0
        else:
            # Series case
            rev = float(pivot.get("Revenue", 0.0))
            cost = float(pivot.get("Cost", 0.0))

        margin_amt = rev - cost
        margin_pct = (margin_amt / cost * 100) if cost else None

        st.markdown("**Quick Totals**")
        st.write(
            {
                "Revenue (total)": round(rev, 2),
                "Cost (total)": round(cost, 2),
                "Margin (Amount)": round(margin_amt, 2),
                "Margin % ( (Rev - Cost)/Cost )": round(margin_pct, 2) if margin_pct is not None else "N/A",
            }
        )

        for key in ["Company_code", "FinalCustomerName", "Account", "Customer"]:
            if key in df.columns:
                by_acct = df.groupby([key, "Type"], dropna=False)["Amount in INR"].sum().reset_index()
                st.markdown(f"**By {key}**")
                st.dataframe(by_acct.head(50))
                break
    else:
        st.warning("The dataset is missing required columns ('Type', 'Amount in INR') for a safe fallback summary.")

def _use_kpi_tools_if_available(user_q: str, df: pd.DataFrame):
    """
    Best-effort use of existing kpi_engine modules if they expose usable logic.
    Keeps everything safe and read-only on currently loaded P&L.
    """
    ql = user_q.lower()

    # Margin-style view
    if "margin" in ql and _optional_modules.get("kpi_engine.margin"):
        st.subheader("AI Fallback — Margin Analysis (kpi_engine.margin)")
        try:
            if _safe_has_cols(df, ["Type", "Amount in INR", "Month"]):
                monthly = df.pivot_table(
                    values="Amount in INR", index="Month", columns="Type", aggfunc="sum", fill_value=0
                ).reset_index()
                if "Revenue" in monthly.columns and "Cost" in monthly.columns:
                    monthly["Margin Amount"] = monthly["Revenue"] - monthly["Cost"]
                    monthly["Margin %"] = monthly.apply(
                        lambda r: (r["Margin Amount"] / r["Cost"] * 100) if r["Cost"] else None, axis=1
                    )
                st.dataframe(monthly)
                return True
        except Exception as e:
            st.warning(f"Margin view failed: {e}")

    # Revenue / Cost breakdown
    if ("revenue" in ql and _optional_modules.get("kpi_engine.revenue")) or \
       ("cost" in ql and _optional_modules.get("kpi_engine.cost")):
        st.subheader("AI Fallback — Revenue/Cost Breakdown")
        try:
            if _safe_has_cols(df, ["Type", "Amount in INR", "Month"]):
                g = df.groupby(["Month", "Type"], dropna=False)["Amount in INR"].sum().reset_index()
                st.dataframe(g)
                return True
        except Exception as e:
            st.warning(f"Rev/Cost view failed: {e}")

    # Offshore / Onsite splits if a location-like column exists
    if ("offshore" in ql or "onsite" in ql) and "Month" in df.columns:
        loc_col = None
        for c in ["Location", "WorkLocation", "Onsite_Offshore", "Onshore_Offshore"]:
            if c in df.columns:
                loc_col = c
                break
        if loc_col and _safe_has_cols(df, ["Type", "Amount in INR", loc_col]):
            st.subheader(f"AI Fallback — {loc_col} Split")
            split = df.groupby([loc_col, "Type"], dropna=False)["Amount in INR"].sum().reset_index()
            st.dataframe(split)
            return True

    # Realized Rate / Headcount / Resources / UT — require UT/HR data
    if any(k in ql for k in ["realized rate", "headcount", "resources", "fte", "utilization", "ut"]):
        st.subheader("AI Fallback — Additional KPI")
        st.info("This analysis needs UT/HR datasets (e.g., NetAvailableHours, Utilization%). Please load/connect UT data to enable.")
        return True

    return False

def ai_fallback(user_q: str, df: pd.DataFrame):
    """
    Main fallback entry:
    - Try to use kpi_engine-style logic when possible
    - Else produce a safe, generic P&L summary
    """
    used = _use_kpi_tools_if_available(user_q, df)
    if not used:
        _generic_margin_summary(df, user_q)
    st.success("✅ AI-generated fallback completed.")

# =========================================================
# MAIN ROUTER (prebuilt path preserved + AI fallback)
# =========================================================
if user_question and not st.session_state.clear_chat:
    try:
        best_qid, matched_prompt = find_best_matching_qid(user_question)

        # Pre-configured Q1–Q10 path
        try:
            question_module = importlib.import_module(f"questions.question_{best_qid.lower()}")
            run_func = getattr(question_module, "run", None)
            if run_func is None:
                raise AttributeError(f"'run' function not found in module for {best_qid}")

            run_params = inspect.signature(run_func).parameters
            if len(run_params) >= 2:
                result = run_func(df_pnl, user_question)
            else:
                result = run_func(df_pnl)

            st.success("✅ Analysis complete.")
            if isinstance(result, pd.DataFrame):
                st.dataframe(result)
            elif isinstance(result, str):
                st.markdown(result)
            elif result is not None:
                st.write(result)

        except (ModuleNotFoundError, AttributeError) as e:
            # If prebuilt module missing or invalid, use AI fallback
            st.info(f"Switching to AI fallback for your question (reason: {e})")
            ai_fallback(user_question, df_pnl)

    except Exception as e:
        # Any unexpected router error -> fallback
        st.info("Switching to AI fallback due to an error in routing.")
        st.caption(f"Router error: {e}")
        ai_fallback(user_question, df_pnl)

# -----------------------------
# Prompt bank (preserved)
# -----------------------------
st.markdown("---")
st.markdown("💡 **Try asking:**")
col1, col2 = st.columns(2)
for i, prompt in enumerate(PROMPT_BANK):
    with (col1 if i % 2 == 0 else col2):
        st.button(prompt, on_click=handle_click, args=(prompt,))
