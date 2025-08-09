# app.py

import streamlit as st
st.set_page_config(page_title="LTTS BI Assistant", layout="wide")

from utils.semantic_matcher import find_best_matching_qid  # existing matcher (qid, prompt, score)
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
# Data loaders (P&L preserved) + OPTIONAL UT loader
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

@st.cache_data
def load_ut_optional():
    """
    Try to load UT/HR dataset if present.
    Expected file: sample_data/LNTData.xlsx
    Returns a cleaned DataFrame or None if not found.
    """
    ut_path = os.path.join("sample_data", "LNTData.xlsx")
    if not os.path.exists(ut_path):
        return None
    try:
        df = pd.read_excel(ut_path)
        df.columns = [str(c).strip() for c in df.columns]

        # Parse Date_a to datetime for reliable month/year filtering
        if "Date_a" in df.columns:
            df["Date_a_dt"] = pd.to_datetime(df["Date_a"], errors="coerce")
            # Convenience columns (not required but helpful)
            df["Year"] = df["Date_a_dt"].dt.year
            df["MonthNum"] = df["Date_a_dt"].dt.month
            df["MonthName"] = df["Date_a_dt"].dt.strftime("%b")
        else:
            # fallback if only Month numeric exists
            if "Month" in df.columns and pd.api.types.is_numeric_dtype(df["Month"]):
                month_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
                df["MonthName"] = df["Month"].map(month_map)
                df["MonthNum"] = df["Month"]

        return df
    except Exception:
        return None

try:
    df_pnl = load_pnl()
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

df_ut = load_ut_optional()  # may be None (non-breaking)

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
# Helper: Dynamic Amount field selector + unit helpers (financials)
# =========================================================
REVCOST_MARGIN_KEYWORDS = (
    "revenue", "cost", "margin", "c&b", "c & b", "c and b", "profit", "loss",
    "cogs", "gross margin", "gm%", "gm %", "cm%", "cm %"
)

def choose_amount_column(user_q: str, df: pd.DataFrame) -> str:
    """
    If the question is about revenue/cost/margin, prefer 'Amount in USD'.
    If it's missing, fall back to 'Amount in INR' with a notice.
    Non-financial questions: prefer INR if present else USD.
    """
    ql = (user_q or "").lower()
    wants_usd = any(k in ql for k in REVCOST_MARGIN_KEYWORDS)

    has_usd = "Amount in USD" in df.columns
    has_inr = "Amount in INR" in df.columns

    if wants_usd:
        if has_usd:
            return "Amount in USD"
        elif has_inr:
            st.caption("Note: 'Amount in USD' not found — using 'Amount in INR' for this financial question.")
            return "Amount in INR"
        else:
            return "Amount in USD"  # handled downstream if missing
    else:
        if has_inr:
            return "Amount in INR"
        elif has_usd:
            return "Amount in USD"
        else:
            return "Amount in INR"

def is_usd_col(amount_col: str) -> bool:
    return amount_col.strip().lower() == "amount in usd"

def unit_label(amount_col: str) -> str:
    return "USD mn" if is_usd_col(amount_col) else "INR mn (USD unavailable)"

def to_million(value) -> float:
    try:
        return round(float(value) / 1_000_000.0, 1)
    except Exception:
        return value

def series_to_million(s: pd.Series) -> pd.Series:
    try:
        return (s.astype(float) / 1_000_000.0).round(1)
    except Exception:
        return s

# =========================================================
# AI FALLBACK (router + opportunistic kpi_engine use) + Headcount intent
# =========================================================
SIM_THRESHOLD = 0.72
FREEFORM_TRIGGERS = ("ai:", "freeform:", "ad-hoc:")

# Optional KPI modules (import-guarded)
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
    """Infer simple time filters from free text (used in financial fallback only)."""
    ql = (q or "").lower()
    out = {}
    now = datetime.now()

    if "this year" in ql:
        out["year"] = now.year
    if "last month" in ql:
        prev_month = (now.replace(day=1) - pd.DateOffset(days=1)).to_pydatetime()
        out["month_from"] = prev_month.strftime("%b %Y")
        out["month_to"] = now.strftime("%b %Y")

    m = re.findall(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+20\d{2}\b", q or "", flags=re.IGNORECASE)
    if m:
        m = [x.title() for x in m]
        if len(m) == 1:
            out["month_from"] = out["month_to"] = m[0]
        else:
            out["month_from"], out["month_to"] = m[0], m[1]
    return out

# ---------- NEW: month & year parsing for Date_a-based UT filtering ----------
MONTH_ALIASES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12
}

def parse_month_year_from_text(q: str):
    """
    Returns (month_num, year) if found; otherwise (None, None).
    Accepts 'Jun 2025', 'June 2025', etc. Year must be 4 digits to avoid ambiguity.
    """
    ql = (q or "").lower()
    # Try patterns like "June 2025" or "Jun 2025"
    m = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)\s+(\d{4})\b", ql)
    if m:
        month_token, year = m.group(1), int(m.group(2))
        month_num = MONTH_ALIASES.get(month_token, None)
        return month_num, year

    # If only month name is present (no explicit year)
    for token, mnum in MONTH_ALIASES.items():
        if re.search(rf"\b{token}\b", ql):
            return mnum, None

    return None, None

def parse_account_from_text(q: str):
    """
    Light account parser: captures tokens like 'A1', 'A-1', 'Account A1'.
    """
    m = re.search(r"\b([A-Za-z]\-?\d{1,3})\b", q or "")
    return m.group(1) if m else None

def ut_filter_by_account_and_period(df_ut: pd.DataFrame, acct_token: str, month_num: int | None, year: int | None):
    """
    Filters UT using Date_a_dt (preferred). If year is None but month is provided,
    picks the latest year available for that month.
    """
    if df_ut is None or df_ut.empty:
        return pd.DataFrame()

    work = df_ut.copy()

    # Account filter: try multiple columns
    acct_cols = [c for c in ["FinalCustomerName", "Company_code", "Account", "Customer"] if c in work.columns]
    if acct_token and acct_cols:
        found = pd.Series(False, index=work.index)
        for c in acct_cols:
            found = found | work[c].astype(str).str.contains(acct_token, case=False, na=False)
        work = work[found]

    # Period filter via Date_a_dt
    if "Date_a_dt" in work.columns and pd.api.types.is_datetime64_any_dtype(work["Date_a_dt"]):
        if month_num:
            if year is None:
                # choose latest available year for that month
                yrs = work[work["Date_a_dt"].dt.month == month_num]["Date_a_dt"].dt.year
                if len(yrs):
                    year = int(yrs.max())
        if month_num and year:
            work = work[(work["Date_a_dt"].dt.month == month_num) & (work["Date_a_dt"].dt.year == year)]
        elif month_num:
            work = work[work["Date_a_dt"].dt.month == month_num]
    else:
        # Fallback if Date_a not available: use Month/Year if present
        if month_num and "MonthNum" in work.columns:
            work = work[work["MonthNum"] == month_num]
        if year and "Year" in work.columns:
            work = work[work["Year"] == year]

    return work, year  # return resolved year (may have been inferred)

def headcount_view(user_q: str, df_ut: pd.DataFrame):
    """
    Headcount = distinct PSNo (or Agent) for the requested account/month using Date_a.
    """
    if df_ut is None or df_ut.empty:
        st.subheader("AI Fallback — Additional KPI")
        st.info("This analysis needs UT/HR datasets (e.g., NetAvailableHours, Utilization%). Please load/connect UT data to enable.")
        return True

    month_num, year = parse_month_year_from_text(user_q)
    acct_token = parse_account_from_text(user_q)

    # Person identifier column
    person_cols = [c for c in ["PSNo", "Agent", "EmployeeID", "EmpID"] if c in df_ut.columns]
    if not person_cols:
        st.subheader("AI Fallback — Headcount")
        st.info("UT dataset found, but no person identifier column (e.g., PSNo/Agent) was detected.")
        return True
    person_col = person_cols[0]

    filt, resolved_year = ut_filter_by_account_and_period(df_ut, acct_token, month_num, year)
    if filt.empty:
        st.subheader("AI Fallback — Headcount")
        month_label = "month not specified" if month_num is None else datetime(2000, month_num, 1).strftime("%b")
        year_label = "" if (resolved_year is None and year is None) else f" {resolved_year or year}"
        if acct_token:
            st.info(f"No UT records found for account like '{acct_token}' in {month_label}{year_label}.")
        else:
            st.info("Please include an account token (e.g., 'A1') and month/year (e.g., 'June 2025').")
        return True

    # Optional billable filter
    ql = (user_question or "").lower()
    dfw = filt.copy()
    if "Status" in dfw.columns and ("billable" in ql or "non-billable" in ql):
        if "billable" in ql:
            dfw = dfw[dfw["Status"].astype(str).str.contains("billable", case=False, na=False)]
        elif "non-billable" in ql:
            dfw = dfw[dfw["Status"].astype(str).str.contains("non", case=False, na=False)]

    hc = dfw[person_col].nunique()

    st.subheader("AI Fallback — Headcount")
    acct_display = acct_token or "(all accounts in filter)"
    if month_num:
        month_display = datetime(2000, month_num, 1).strftime("%b")
        if resolved_year or year:
            month_display = f"{month_display} {resolved_year or year}"
    else:
        month_display = "(month not specified)"
    st.markdown(f"**Account:** {acct_display} &nbsp;&nbsp; **Month:** {month_display}")
    st.dataframe(pd.DataFrame([{"Headcount": hc, "Account (contains)": acct_display, "Month": month_display}]))

    # Optional small breakdown by BU/DU if present
    for grp_col in ["BU", "DU"]:
        if grp_col in dfw.columns:
            br = dfw.groupby(grp_col, dropna=False)[person_col].nunique().reset_index().rename(columns={person_col:"Headcount"})
            st.markdown(f"**Headcount by {grp_col}**")
            st.dataframe(br.sort_values("Headcount", ascending=False))
    return True

# ------------------ Existing generic financial fallbacks ------------------
def _generic_margin_summary(df: pd.DataFrame, user_q: str):
    st.subheader("AI Fallback — General Summary")

    amount_col = choose_amount_column(user_q, df)
    if not _safe_has_cols(df, ["Type", amount_col]):
        st.warning(f"The dataset is missing required columns ('Type', '{amount_col}') for a safe fallback summary.")
        return

    unit = unit_label(amount_col)

    # Monthly totals if Month exists
    if "Month" in df.columns:
        g = df.groupby(["Month", "Type"], dropna=False)[amount_col].sum().reset_index()
        g[amount_col] = series_to_million(g[amount_col])
        st.markdown(f"**Monthly Revenue/Cost** (values in {unit})")
        st.dataframe(g)

    # Overall totals and margin
    pivot = df.pivot_table(values=amount_col, index=None, columns="Type", aggfunc="sum", fill_value=0)
    if isinstance(pivot, pd.DataFrame):
        rev = float(pivot["Revenue"].iloc[0]) if "Revenue" in pivot.columns else 0.0
        cost = float(pivot["Cost"].iloc[0]) if "Cost" in pivot.columns else 0.0
    else:
        rev = float(pivot.get("Revenue", 0.0))
        cost = float(pivot.get("Cost", 0.0))

    margin_amt = rev - cost
    margin_pct = (margin_amt / cost * 100) if cost else None

    st.markdown("**Quick Totals**")
    st.write(
        {
            f"Revenue (total, {unit})": to_million(rev),
            f"Cost (total, {unit})": to_million(cost),
            "Margin (Amount, same unit)": to_million(margin_amt),
            "Margin % ( (Rev - Cost)/Cost )": round(margin_pct, 1) if margin_pct is not None else "N/A",
        }
    )

    # By account-like column
    for key in ["Company_code", "FinalCustomerName", "Account", "Customer"]:
        if key in df.columns:
            by_acct = df.groupby([key, "Type"], dropna=False)[amount_col].sum().reset_index()
            by_acct[amount_col] = series_to_million(by_acct[amount_col])
            st.markdown(f"**By {key}** (values in {unit})")
            st.dataframe(by_acct.head(50))
            break

def _use_kpi_tools_if_available(user_q: str, df: pd.DataFrame):
    """
    Best-effort use of existing kpi_engine modules when possible.
    Includes headcount intent via UT (using Date_a) if loaded.
    """
    ql = (user_q or "").lower()

    # ---- Headcount intent (Date_a-based) ----
    if any(w in ql for w in ["headcount", "fte", "resources"]) or re.search(r"\bhc\b", ql):
        return headcount_view(user_question, df_ut)

    # ---- Financial fallbacks (USD mn where available) ----
    amount_col = choose_amount_column(user_q, df)
    unit = unit_label(amount_col)

    # Margin-style view
    if "margin" in ql and _optional_modules.get("kpi_engine.margin"):
        st.subheader("AI Fallback — Margin Analysis (kpi_engine.margin)")
        try:
            if _safe_has_cols(df, ["Type", amount_col, "Month"]):
                monthly = df.pivot_table(
                    values=amount_col, index="Month", columns="Type", aggfunc="sum", fill_value=0
                ).reset_index()
                for col in ["Revenue", "Cost"]:
                    if col in monthly.columns:
                        monthly[col] = series_to_million(monthly[col])
                if "Revenue" in monthly.columns and "Cost" in monthly.columns:
                    monthly["Margin Amount"] = (monthly["Revenue"] - monthly["Cost"]).round(1)
                    monthly["Margin %"] = monthly.apply(
                        lambda r: round((r["Margin Amount"] / r["Cost"] * 100), 1) if r["Cost"] else None, axis=1
                    )
                st.caption(f"Values shown in {unit}.")
                st.dataframe(monthly)
                return True
        except Exception as e:
            st.warning(f"Margin view failed: {e}")

    # Revenue / Cost breakdown
    if ("revenue" in ql and _optional_modules.get("kpi_engine.revenue")) or \
       ("cost" in ql and _optional_modules.get("kpi_engine.cost")):
        st.subheader("AI Fallback — Revenue/Cost Breakdown")
        try:
            if _safe_has_cols(df, ["Type", amount_col, "Month"]):
                g = df.groupby(["Month", "Type"], dropna=False)[amount_col].sum().reset_index()
                g[amount_col] = series_to_million(g[amount_col])
                st.caption(f"Values shown in {unit}.")
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
        if loc_col and _safe_has_cols(df, ["Type", amount_col, loc_col]):
            st.subheader(f"AI Fallback — {loc_col} Split")
            split = df.groupby([loc_col, "Type"], dropna=False)[amount_col].sum().reset_index()
            split[amount_col] = series_to_million(split[amount_col])
            st.caption(f"Values shown in {unit}.")
            st.dataframe(split)
            return True

    # Realized Rate / Utilization — require UT/HR data (kept informative)
    if any(k in ql for k in ["realized rate", "utilization", "ut"]):
        st.subheader("AI Fallback — Additional KPI")
        st.info("This analysis needs UT/HR datasets (e.g., NetAvailableHours, Utilization%). Please load/connect UT data to enable.")
        return True

    return False

def ai_fallback(user_q: str, df: pd.DataFrame):
    """Main fallback entry."""
    used = _use_kpi_tools_if_available(user_q, df)
    if not used:
        _generic_margin_summary(df, user_q)
    st.success("✅ AI-generated fallback completed.")

# =========================================================
# MAIN ROUTER (prebuilt path preserved + AI fallback)
# =========================================================
if user_question and not st.session_state.clear_chat:
    try:
        # Get best match — handle tuple or dict variants
        res = find_best_matching_qid(user_question)
        best_qid, matched_prompt, score = None, None, None
        if isinstance(res, tuple):
            if len(res) == 3:
                best_qid, matched_prompt, score = res
            elif len(res) == 2:
                best_qid, matched_prompt = res
            elif len(res) == 1:
                best_qid = res[0]
        elif isinstance(res, dict):
            best_qid = res.get("qid") or res.get("best_qid")
            matched_prompt = res.get("prompt") or res.get("matched_prompt")
            score = res.get("score")

        # Triggers to force AI path
        force_ai = user_question.lower().strip().startswith(FREEFORM_TRIGGERS)
        low_score = (score is not None and score < SIM_THRESHOLD)

        if force_ai or low_score or not best_qid:
            if force_ai:
                st.caption("AI mode: freeform override detected.")
            elif low_score:
                st.caption(f"AI mode: matcher score {score:.2f} < {SIM_THRESHOLD}.")
            else:
                st.caption("AI mode: no suitable prebuilt match found.")
            ai_fallback(user_question, df_pnl)
            st.stop()

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
            st.info(f"Switching to AI fallback for your question (reason: {e})")
            ai_fallback(user_question, df_pnl)

    except Exception as e:
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
