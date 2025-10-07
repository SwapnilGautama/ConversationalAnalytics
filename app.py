# app.py — Halo LTTS (free-flowing LLM router + safe fallbacks)
# - Adds Azure OpenAI intent router (free-form conversation)
# - Preserves all existing behavior and prompt-bank UX
# - Expands margin synonyms to treat "profit%" like "margin%"
# - Adds robust fallbacks if LLM is unavailable

import streamlit as st
st.set_page_config(page_title="Halo", layout="wide")

from utils.semantic_matcher import find_best_matching_qid  # returns (qid, prompt, score)
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

# ========= NEW: Azure OpenAI (optional) =========
AOAI_AVAILABLE = False
try:
    # Prefer the new SDK class shipped with openai>=1.0
    from openai import AzureOpenAI
    AOAI_AVAILABLE = True
except Exception:
    # Not fatal—router will degrade to non-LLM path
    AOAI_AVAILABLE = False


def _aoai_client():
    """
    Returns configured Azure OpenAI client or None.
    Uses env vars:
        AZURE_OPENAI_ENDPOINT
        AZURE_OPENAI_API_KEY
        AZURE_OPENAI_DEPLOYMENT
        AZURE_OPENAI_API_VERSION (optional; default 2024-02-15-preview)
    """
    if not AOAI_AVAILABLE:
        return None

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    if not endpoint or not key:
        return None

    try:
        client = AzureOpenAI(
            api_key=key,
            api_version=api_version,
            azure_endpoint=endpoint,
        )
        return client
    except Exception:
        return None


def _aoai_chat(messages, deployment=None, temperature=0.0, max_tokens=700):
    """
    Small wrapper that calls Azure OpenAI ChatCompletions if configured.
    Returns (text, error_message_or_None).
    """
    client = _aoai_client()
    deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not client or not deployment:
        return None, "Azure OpenAI not configured."

    try:
        # Chat Completions style (compatible with 4o/4o-mini deployments)
        resp = client.chat.completions.create(
            model=deployment,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
        )
        text = resp.choices[0].message.content if resp and resp.choices else None
        return text, None
    except Exception as e:
        return None, f"AOAI error: {e}"


# ---------- tiny helper (fixes NameError) ----------
def _safe_has_cols(frame: pd.DataFrame, cols) -> bool:
    """Return True if all required columns exist in the DataFrame."""
    return isinstance(frame, pd.DataFrame) and all(c in frame.columns for c in cols)


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
# Session state (preserved + chat memory)
# -----------------------------
if "autofill_text" not in st.session_state:
    st.session_state.autofill_text = ""
if "clear_chat" not in st.session_state:
    st.session_state.clear_chat = False
if "chat_history" not in st.session_state:
    # keep a light memory for intent routing / LLM answers
    st.session_state.chat_history = []  # [{role: "user"/"assistant", "content": "..."}]


def handle_click(prompt):
    st.session_state.autofill_text = prompt
    st.session_state.clear_chat = False


def clear_input():
    st.session_state.autofill_text = ""
    st.session_state.clear_chat = True
    st.session_state.chat_history = []


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
    # Ensure Month is datetime for filtering
    if "Month" in df.columns:
        try:
            df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
        except Exception:
            pass
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
            df["Year"] = df["Date_a_dt"].dt.year
            df["MonthNum"] = df["Date_a_dt"].dt.month
            df["MonthName"] = df["Date_a_dt"].dt.strftime("%b")
        else:
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
# Header (updated to include Halo logo on the left)
# -----------------------------
def _encode_image(path: str, width: int = 140) -> str | None:
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f'<img src="data:image/png;base64,{b64}" width="{width}" />'


def display_header():
    # LEFT: Halo logo (add your file here)
    halo_logo_path = os.path.join("sample_data", "halo_logo.png")   # <- add your Halo logo here
    halo_img_tag = _encode_image(halo_logo_path, width=140) or ""

    # RIGHT: Scalability Engineers logo (existing)
    se_logo_path = os.path.join("sample_data", "Logo.png")
    se_img_tag = _encode_image(se_logo_path, width=230) or ""

    # Center title text
    title_html = """
        <h1 style='font-family: "Segoe UI", sans-serif; font-size: 40px; color: #002D62; margin: 0;'>
            Conversational Analytics Assistant
        </h1>
    """

    st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-top:-20px; margin-bottom:10px;">
            <div style="flex:1; text-align:left;">{halo_img_tag}</div>
            <div style="flex:2; text-align:center;">{title_html}</div>
            <div style="flex:1; text-align:right;">{se_img_tag}</div>
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
    Welcome to <b>Halo</b> — an AI-powered tool for analyzing business trends using your P&L and utilization data.
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
            return "Amount in USD"
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
# Parsing helpers shared by UT & P&L
# =========================================================
SIM_THRESHOLD = 0.72
FREEFORM_TRIGGERS = ("ai:", "freeform:", "ad-hoc:")

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
    """Returns (month_num, year) if found; otherwise (None, None)."""
    ql = (q or "").lower()
    m = re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)\s+(\d{4})\b",
        ql,
    )
    if m:
        month_token, year = m.group(1), int(m.group(2))
        month_num = MONTH_ALIASES.get(month_token, None)
        return month_num, year
    for token, mnum in MONTH_ALIASES.items():
        if re.search(rf"\b{token}\b", ql):
            return mnum, None
    return None, None


def parse_account_token(q: str):
    """Light account parser: tokens like 'A1', 'A-1'."""
    m = re.search(r"\b([A-Za-z]\-?\d{1,3})\b", q or "")
    return m.group(1) if m else None


def _unique_nontrivial_values(series: pd.Series):
    vals = (
        series.dropna()
        .astype(str)
        .map(lambda x: x.strip())
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )
    return [v for v in vals if isinstance(v, str) and len(v.strip()) >= 3]


# =========================================================
# (UPDATED) Lightweight rule override for Q1 — "margin % below <N>"  (+profit synonyms)
# =========================================================
_Q1_PATTERNS = [
    r"\b(?:margin|gm|cm|profit|profitability)\s*%?\s*<\s*\d+\s*%?",
    r"\b(?:margin|gm|cm|profit|profitability)\s*(?:%|percent|percentage)?\s*(?:less than|below|under)\s*\d+\s*%?",
    r"\b(?:less than|below|under)\s*\d+\s*%?\s*(?:margin|gm|cm|profit|profitability)\b",
]


def _is_q1_margin_below_intent(q: str | None) -> bool:
    if not q:
        return False
    ql = q.lower()
    return any(re.search(p, ql) for p in _Q1_PATTERNS)


# =========================================================
# (NEW) Lightweight rule override for Q3 — "C&B quarter-over-quarter change"
# =========================================================
_Q3_PATTERNS = [
    r"\bc\s*&\s*b\b.*\b(var(?:y|ied)|change|delta|diff(?:erence)?)\b.*\bquarter\b",
    r"\bc\s*and\s*b\b.*\b(var(?:y|ied)|change|delta|diff(?:erence)?)\b.*\bquarter\b",
    r"\bc&b\b.*\bqoq\b",
    r"\bqoq\b.*\bc&b\b",
    r"\bcompare\b.*\bc&b\b.*\bquarter\b",
]


def _is_q3_cb_variance_intent(q: str | None) -> bool:
    if not q:
        return False
    ql = q.lower()
    return any(re.search(p, ql) for p in _Q3_PATTERNS)


# =========================================================
# UT headcount fallback (multi-dimension + Date_a) — working
# =========================================================
DIMENSION_CANDIDATES_UT = {
    "account_like": ["FinalCustomerName", "Account", "Customer", "Company_code"],
    "segment_like": ["Segment", "Vertical"],
    "org_like": ["BU", "DU"]
}


def extract_dimension_filters_ut(user_q: str, df_ut: pd.DataFrame):
    if df_ut is None or df_ut.empty:
        return {}
    ql = (user_q or "").lower()
    filters = {}
    acct_token = parse_account_token(user_q)
    if acct_token:
        for col in DIMENSION_CANDIDATES_UT["account_like"]:
            if col in df_ut.columns:
                filters.setdefault(col, []).append(acct_token)
                break
    for group, cols in DIMENSION_CANDIDATES_UT.items():
        for col in cols:
            if col not in df_ut.columns:
                continue
            matches = []
            for val in _unique_nontrivial_values(df_ut[col]):
                if val.lower() in ql:
                    matches.append(val)
            if matches:
                filters.setdefault(col, []).extend(matches)
    return filters


def apply_ut_filters(df_ut: pd.DataFrame, filters: dict, month_num: int | None, year: int | None):
    if df_ut is None or df_ut.empty:
        return pd.DataFrame(), year
    work = df_ut.copy()
    if "Date_a_dt" in work.columns and pd.api.types.is_datetime64_any_dtype(work["Date_a_dt"]):
        if month_num:
            if year is None:
                yrs = work[work["Date_a_dt"].dt.month == month_num]["Date_a_dt"].dt.year
                if len(yrs):
                    year = int(yrs.max())
        if month_num and year:
            work = work[(work["Date_a_dt"].dt.month == month_num) & (work["Date_a_dt"].dt.year == year)]
        elif month_num:
            work = work[work["Date_a_dt"].dt.month == month_num]
    else:
        if month_num and "MonthNum" in work.columns:
            work = work[work["MonthNum"] == month_num]
        if year and "Year" in work.columns:
            work = work[work["Year"] == year]
    for col, values in (filters or {}).items():
        if col not in work.columns or not values:
            continue
        mask = pd.Series(False, index=work.index)
        for v in values:
            mask = mask | work[col].astype(str).str.contains(str(v), case=False, na=False)
        work = work[mask]
    return work, year


def headcount_view(user_q: str, df_ut: pd.DataFrame):
    if df_ut is None or df_ut.empty:
        st.subheader("AI Fallback — Additional KPI")
        st.info("This analysis needs UT/HR datasets (e.g., NetAvailableHours, Utilization%). Please load/connect UT data to enable.")
        return True
    month_num, year = parse_month_year_from_text(user_q)
    dim_filters = extract_dimension_filters_ut(user_q, df_ut)
    person_cols = [c for c in ["PSNo", "Agent", "EmployeeID", "EmpID"] if c in df_ut.columns]
    if not person_cols:
        st.subheader("AI Fallback — Headcount")
        st.info("UT dataset found, but no person identifier column (e.g., PSNo/Agent) was detected.")
        return True
    person_col = person_cols[0]
    filt, resolved_year = apply_ut_filters(df_ut, dim_filters, month_num, year)
    if filt.empty:
        st.subheader("AI Fallback — Headcount")
        month_label = "month not specified" if month_num is None else datetime(2000, month_num, 1).strftime("%b")
        year_label = "" if (resolved_year is None and year is None) else f" {resolved_year or year}"
        st.info(f"No UT records found for the requested filters in {month_label}{year_label}.")
        return True
    ql = (user_question or "").lower()
    dfw = filt.copy()
    if "Status" in dfw.columns and ("billable" in ql or "non-billable" in ql):
        if "billable" in ql:
            dfw = dfw[dfw["Status"].astype(str).str.contains("billable", case=False, na=False)]
        elif "non-billable" in ql:
            dfw = dfw[dfw["Status"].astype(str).str.contains("non", case=False, na=False)]
    hc = dfw[person_col].nunique()
    st.subheader("AI Fallback — Headcount")
    pieces = []
    if month_num:
        mdisp = datetime(2000, month_num, 1).strftime("%b")
        if resolved_year or year:
            mdisp = f"{mdisp} {resolved_year or year}"
        pieces.append(f"**Month:** {mdisp}")
    else:
        pieces.append("**Month:** (not specified)")
    if dim_filters:
        applied = []
        for col, vals in dim_filters.items():
            applied.append(f"{col} contains [{', '.join(map(str, vals))}]")
        pieces.append("**Filters:** " + "; ".join(applied))
    else:
        pieces.append("**Filters:** (none)")
    st.markdown(" &nbsp;&nbsp; ".join(pieces))
    st.dataframe(pd.DataFrame([{"Headcount": hc}]))
    for grp_col in ["BU", "DU", "Segment", "Vertical"]:
        if grp_col in dfw.columns:
            br = dfw.groupby(grp_col, dropna=False)[person_col].nunique().reset_index().rename(columns={person_col:"Headcount"})
            st.markdown(f"**Headcount by {grp_col}**")
            st.dataframe(br.sort_values("Headcount", ascending=False))
    return True


# =========================================================
# Financial multi-dimension filtering for P&L (Segment/Account + Month)
# =========================================================
DIMENSION_CANDIDATES_PNL = {
    "account_like": ["FinalCustomerName", "Account", "Customer", "Company_code"],
    "segment_like": ["Segment", "Vertical", "BU", "DU"]
}


def extract_dimension_filters_pnl(user_q: str, df_pnl: pd.DataFrame):
    if df_pnl is None or df_pnl.empty:
        return {}
    ql = (user_q or "").lower()
    filters = {}

    # explicit account token (A1)
    acct_token = parse_account_token(user_q)
    if acct_token:
        for col in DIMENSION_CANDIDATES_PNL["account_like"]:
            if col in df_pnl.columns:
                filters.setdefault(col, []).append(acct_token)
                break

    # substring matches for known values
    for group, cols in DIMENSION_CANDIDATES_PNL.items():
        for col in cols:
            if col not in df_pnl.columns:
                continue
            matches = []
            for val in _unique_nontrivial_values(df_pnl[col]):
                if val.lower() in ql:
                    matches.append(val)
            if matches:
                filters.setdefault(col, []).extend(matches)

    return filters


def apply_pnl_filters(df: pd.DataFrame, filters: dict, month_num: int | None, year: int | None):
    if df is None or df.empty:
        return pd.DataFrame(), year
    work = df.copy()

    # Month/year via 'Month' datetime column
    if "Month" in work.columns and pd.api.types.is_datetime64_any_dtype(work["Month"]):
        if month_num:
            if year is None:
                yrs = work[work["Month"].dt.month == month_num]["Month"].dt.year
                if len(yrs):
                    year = int(yrs.max())
        if month_num and year:
            work = work[(work["Month"].dt.month == month_num) & (work["Month"].dt.year == year)]
        elif month_num:
            work = work[work["Month"].dt.month == month_num]

    # Dimension filters: AND across columns, OR within the same column
    for col, values in (filters or {}).items():
        if col not in work.columns or not values:
            continue
        mask = pd.Series(False, index=work.index)
        for v in values:
            mask = mask | work[col].astype(str).str.contains(str(v), case=False, na=False)
        work = work[mask]

    return work, year


# ------------------ Financial fallbacks (with filtering) ------------------
def _generic_margin_summary(df: pd.DataFrame, user_q: str):
    st.subheader("AI Fallback — General Summary")

    amount_col = choose_amount_column(user_q, df)
    if not _safe_has_cols(df, ["Type", amount_col]):
        st.warning(f"The dataset is missing required columns ('Type', '{amount_col}') for a safe fallback summary.")
        return

    month_num, year = parse_month_year_from_text(user_q)
    dim_filters = extract_dimension_filters_pnl(user_q, df)
    dff, resolved_year = apply_pnl_filters(df, dim_filters, month_num, year)

    if dff.empty:
        st.info("No P&L rows found for the requested filters/time. Showing overall totals instead.")
        dff = df

    unit = unit_label(amount_col)

    if "Month" in dff.columns:
        g = dff.groupby(["Month", "Type"], dropna=False)[amount_col].sum().reset_index()
        g[amount_col] = series_to_million(g[amount_col])
        st.markdown(f"**Monthly Revenue/Cost** (values in {unit})")
        st.dataframe(g)

    pivot = dff.pivot_table(values=amount_col, index=None, columns="Type", aggfunc="sum", fill_value=0)
    if isinstance(pivot, pd.DataFrame):
        rev = float(pivot["Revenue"].iloc[0]) if "Revenue" in pivot.columns else 0.0
        cost = float(pivot["Cost"].iloc[0]) if "Cost" in pivot.columns else 0.0
    else:
        rev = float(pivot.get("Revenue", 0.0))
        cost = float(pivot.get("Cost", 0.0))

    margin_amt = rev - cost
    # BOTH %s for clarity
    margin_pct_cost = (margin_amt / cost * 100) if cost else None
    profit_pct_rev  = (margin_amt / rev  * 100) if rev else None

    pieces = []
    if month_num:
        mdisp = datetime(2000, month_num, 1).strftime("%b")
        if resolved_year or year:
            mdisp = f"{mdisp} {resolved_year or year}"
        pieces.append(f"**Month filter:** {mdisp}")
    if dim_filters:
        applied = []
        for col, vals in dim_filters.items():
            applied.append(f"{col} contains [{', '.join(map(str, vals))}]")
        pieces.append("**Filters:** " + "; ".join(applied))
    if pieces:
        st.caption(" | ".join(pieces))

    st.markdown("**Quick Totals**")
    st.write(
        {
            f"Revenue (total, {unit})": to_million(rev),
            f"Cost (total, {unit})": to_million(cost),
            "Margin (Amount, same unit)": to_million(margin_amt),
            "Margin % ( (Rev - Cost)/Cost )": round(margin_pct_cost, 1) if margin_pct_cost is not None else "N/A",
            "Profit % ( (Rev - Cost)/Revenue )": round(profit_pct_rev, 1) if profit_pct_rev is not None else "N/A",
        }
    )

    for key in ["Company_code", "FinalCustomerName", "Account", "Customer"]:
        if key in dff.columns:
            by_acct = dff.groupby([key, "Type"], dropna=False)[amount_col].sum().reset_index()
            by_acct[amount_col] = series_to_million(by_acct[amount_col])
            st.markdown(f"**By {key}** (values in {unit})")
            st.dataframe(by_acct.head(50))
            break


# ========= NEW: relative period helper used by margin engine =========
def resolve_relative_period(q: str, df: pd.DataFrame):
    """
    Returns a boolean mask for df if 'last month' or 'last quarter' is detected.
    Falls back to None if not found or Month missing.
    """
    if "Month" not in df.columns or not pd.api.types.is_datetime64_any_dtype(df["Month"]):
        return None
    ql = (q or "").lower()
    last_date = pd.to_datetime(df["Month"], errors="coerce").max()
    if pd.isna(last_date):
        return None
    if "last month" in ql:
        ym = (last_date.year, last_date.month)
        return (df["Month"].dt.year == ym[0]) & (df["Month"].dt.month == ym[1])
    if "last quarter" in ql or "previous quarter" in ql:
        qtr = (last_date.month - 1)//3 + 1
        prev_q = qtr - 1 or 4
        prev_y = last_date.year - (1 if qtr == 1 else 0)
        return (df["Month"].dt.to_period("Q") == pd.Period(f"{prev_y}Q{prev_q}"))
    return None


# ========= NEW: generic margin/profit% engine (freeform) =========
MARGIN_SYNONYMS = (
    "margin", "gm", "cm", "profit", "profitability",
    "profit%", "profit %", "profit percent", "profit percentage",
    "margin%", "margin %", "gm%", "cm%"
)


def has_margin_intent(q: str | None) -> bool:
    ql = (q or "").lower()
    return any(tok in ql for tok in MARGIN_SYNONYMS)


def extract_threshold(q: str):
    ql = (q or "").lower()
    m = re.search(r"(<=|>=|<|>)\s*(\d{1,3}(?:\.\d+)?)\s*%?", ql)
    if m:
        return m.group(1), float(m.group(2))
    word_ops = [
        (r"\b(less than|below|under)\b", "<"),
        (r"\b(more than|above|greater than|over)\b", ">")
    ]
    for pat, sym in word_ops:
        m2 = re.search(pat + r"\s*(\d{1,3}(?:\.\d+)?)\s*%?", ql)
        if m2:
            return sym, float(m2.group(1))
    return None, None


def extract_topn(q: str):
    ql = (q or "").lower()
    m = re.search(r"\b(top|bottom)\s*(\d{1,3})\b", ql)
    if m:
        return m.group(1), int(m.group(2))
    return None, None


def generic_margin_engine(user_q: str, df: pd.DataFrame):
    """
    Flexible, dataframe-only engine that:
      * applies account/segment + month filters,
      * understands 'last month/quarter',
      * computes Revenue, Cost, Margin amount,
      * computes BOTH margin% (Rev-Cost)/Cost and profit% (Rev-Cost)/Revenue,
      * supports threshold queries (e.g., margin < 30%), and
      * supports Top/Bottom N by margin/profit%.
    """
    if df is None or df.empty:
        st.info("No P&L data loaded.")
        return True

    amount_col = choose_amount_column(user_q, df)
    unit = unit_label(amount_col)

    month_num, year = parse_month_year_from_text(user_q)
    dim_filters = extract_dimension_filters_pnl(user_q, df)
    dff, resolved_year = apply_pnl_filters(df, dim_filters, month_num, year)

    rel_mask = resolve_relative_period(user_q, df)
    if rel_mask is not None:
        dff = dff[rel_mask] if not dff.empty else df[rel_mask]

    if dff.empty:
        dff = df  # fallback to global view

    group_cols_pref = ["FinalCustomerName", "Account", "Customer", "Company_code", "Segment", "Vertical", "BU", "DU"]
    grp = next((c for c in group_cols_pref if c in dff.columns), None)

    if _safe_has_cols(dff, ["Type", amount_col]):
        if grp:
            g = dff.groupby([grp, "Type"], dropna=False)[amount_col].sum().reset_index()
            pivot = g.pivot_table(values=amount_col, index=grp, columns="Type", aggfunc="sum", fill_value=0).reset_index()
        else:
            pivot = dff.pivot_table(values=amount_col, index=None, columns="Type", aggfunc="sum", fill_value=0)
            pivot = pivot.to_frame().T
            pivot.insert(0, "All", "Total")
            grp = "All"
    else:
        st.warning(f"Missing required columns to compute margin ('Type', '{amount_col}').")
        return True

    for col in ["Revenue", "Cost"]:
        if col not in pivot.columns:
            pivot[col] = 0.0
    pivot["MarginAmount"] = pivot["Revenue"] - pivot["Cost"]
    pivot["MarginPct_cost"] = pivot.apply(lambda r: (r["MarginAmount"]/r["Cost"]*100) if r["Cost"] else None, axis=1)
    pivot["ProfitPct_rev"] = pivot.apply(lambda r: (r["MarginAmount"]/r["Revenue"]*100) if r["Revenue"] else None, axis=1)

    op, thr = extract_threshold(user_q)
    order, topn = extract_topn(user_q)

    use_rev_pct = "profit" in (user_q or "").lower()
    pct_col = "ProfitPct_rev" if use_rev_pct else "MarginPct_cost"

    if thr is not None:
        if op in ("<", "<="):
            pivot = pivot[pivot[pct_col] <= thr] if op == "<=" else pivot[pivot[pct_col] < thr]
        elif op in (">", ">="):
            pivot = pivot[pivot[pct_col] >= thr] if op == ">=" else pivot[pivot[pct_col] > thr]

    if order and topn:
        asc = (order == "bottom")
        pivot = pivot.sort_values(pct_col, ascending=asc).head(topn)

    for c in ["Revenue", "Cost", "MarginAmount"]:
        pivot[c] = series_to_million(pivot[c])

    parts = [f"Values shown in {unit}.", f"Ranking by **{'Profit% (Rev)' if use_rev_pct else 'Margin% (Cost)'}**."]
    if month_num:
        mdisp = datetime(2000, month_num, 1).strftime("%b")
        if resolved_year or year:
            mdisp = f"{mdisp} {resolved_year or year}"
        parts.append(f"Month filter: {mdisp}")
    if dim_filters:
        applied = []
        for col, vals in dim_filters.items():
            applied.append(f"{col} contains [{', '.join(map(str, vals))}]")
        parts.append("Filters: " + "; ".join(applied))
    st.caption(" | ".join(parts))

    st.subheader("AI Fallback — Margin/Profit% View")
    cols_order = [grp, "Revenue", "Cost", "MarginAmount", "MarginPct_cost", "ProfitPct_rev"]
    show = [c for c in cols_order if c in pivot.columns]
    st.dataframe(pivot[show].rename(columns={
        "MarginAmount":"Margin (Amount)",
        "MarginPct_cost":"Margin % ( (Rev-Cost)/Cost )",
        "ProfitPct_rev":"Profit % ( (Rev-Cost)/Revenue )"
    }))
    return True


# ------------------ Smarter KPI tool chooser (pandas-first) ------------------
def _use_kpi_tools_if_available(user_q: str, df: pd.DataFrame, route_hint: str | None = None):
    """
    Best-effort use of pandas-only views.
    Includes headcount intent via UT (using Date_a) if loaded.
    Adds multi-dimension + Month filtering for P&L-based financial metrics.
    Optional route_hint can force a particular view.
    """
    ql = (user_q or "").lower()

    # ---- Headcount intent ----
    if route_hint == "HEADCOUNT" or any(w in ql for w in ["headcount", "fte", "resources"]) or re.search(r"\bhc\b", ql):
        return headcount_view(user_question, df_ut)

    amount_col = choose_amount_column(user_q, df)
    unit = unit_label(amount_col)
    month_num, year = parse_month_year_from_text(user_q)
    dim_filters = extract_dimension_filters_pnl(user_q, df)
    dff, resolved_year = apply_pnl_filters(df, dim_filters, month_num, year)
    if dff.empty:
        dff = df
        tried_filter_note = True
    else:
        tried_filter_note = False

    # ---- Margin / Profit% view ----
    if route_hint == "MARGIN" or has_margin_intent(user_q) or "margin" in ql or "profit" in ql:
        return generic_margin_engine(user_q, df)

    # ---- Revenue/Cost breakdown ----
    if route_hint == "REV_COST" or ("revenue" in ql) or ("cost" in ql):
        st.subheader("AI Fallback — Revenue/Cost Breakdown")
        try:
            if _safe_has_cols(dff, ["Type", amount_col]) and "Month" in dff.columns:
                g = dff.groupby(["Month", "Type"], dropna=False)[amount_col].sum().reset_index()
                g[amount_col] = series_to_million(g[amount_col])
                parts = [f"Values shown in {unit}."]
                if month_num:
                    mdisp = datetime(2000, month_num, 1).strftime("%b")
                    if resolved_year or year:
                        mdisp = f"{mdisp} {resolved_year or year}"
                    parts.append(f"Month filter: {mdisp}")
                if dim_filters:
                    applied = []
                    for col, vals in dim_filters.items():
                        applied.append(f"{col} contains [{', '.join(map(str, vals))}]")
                    parts.append("Filters: " + "; ".join(applied))
                if tried_filter_note:
                    parts.append("(No rows matched filters — showing overall results.)")
                st.caption(" | ".join(parts))
                st.dataframe(g)
                return True
        except Exception as e:
            st.warning(f"Rev/Cost view failed: {e}")

    # ---- Offshore / Onsite splits ----
    if route_hint == "ON_OFF" or (("offshore" in ql or "onsite" in ql) and "Month" in df.columns):
        loc_col = None
        for c in ["Location", "WorkLocation", "Onsite_Offshore", "Onshore_Offshore"]:
            if c in df.columns:
                loc_col = c
                break
        if loc_col and _safe_has_cols(dff, ["Type", amount_col, loc_col]):
            try:
                g = dff.groupby([loc_col, "Type"], dropna=False)[amount_col].sum().reset_index()
                g[amount_col] = series_to_million(g[amount_col])
                parts = [f"Values shown in {unit}."]
                if month_num:
                    mdisp = datetime(2000, month_num, 1).strftime("%b")
                    if resolved_year or year:
                        mdisp = f"{mdisp} {resolved_year or year}"
                    parts.append(f"Month filter: {mdisp}")
                if dim_filters:
                    applied = []
                    for col, vals in dim_filters.items():
                        applied.append(f"{col} contains [{', '.join(map(str, vals))}]")
                    parts.append("Filters: " + "; ".join(applied))
                if tried_filter_note:
                    parts.append("(No rows matched filters — showing overall results.)")
                st.caption(" | ".join(parts))
                st.dataframe(g.sort_values([loc_col, "Type"]))
                return True
            except Exception as e:
                st.warning(f"Onsite/Offshore view failed: {e}")

    # If nothing matched, try a generic margin summary or return False to let other paths handle.
    try:
        _generic_margin_summary(df, user_q)
        return True
    except Exception as e:
        st.warning(f"Generic summary failed: {e}")
        return False


# =========================================================
# LLM router (optional) + overall dispatcher
# =========================================================

def _llm_route_and_answer(user_q: str) -> bool:
    """Use Azure OpenAI (if configured) to answer freeform questions."""
    system = (
        "You are an analytics assistant for P&L and utilization data. "
        "Prefer precise, concise answers; when numbers are unknown, say so. "
        "Never fabricate columns; avoid assuming currency unless stated."
    )
    msgs = [{"role": "system", "content": system}]
    # Include a tiny chat memory for context
    for m in st.session_state.chat_history[-6:]:
        msgs.append(m)
    msgs.append({"role": "user", "content": user_q})
    text, err = _aoai_chat(msgs)
    if err or not text:
        return False
    st.subheader("AI Answer")
    st.write(text)
    # Append to memory
    st.session_state.chat_history.append({"role":"user","content":user_q})
    st.session_state.chat_history.append({"role":"assistant","content":text})
    return True


def _dispatch_to_qmodule(qid: str, df_pnl: pd.DataFrame, df_ut: pd.DataFrame, user_q: str) -> bool:
    """Try to import question module and run it. Expected function: run(df_pnl, df_ut, user_q)."""
    try:
        module_name = f"question_engine.question_q{qid}" if not qid.startswith('q') else f"question_engine.{qid}"
        mod = importlib.import_module(module_name)
        if hasattr(mod, "run"):
            st.subheader(f"Configured Analysis — {qid.upper()}")
            mod.run(df_pnl=df_pnl, df_ut=df_ut, user_question=user_q)
            return True
    except Exception as e:
        st.warning(f"Could not run configured analysis for {qid}: {e}")
    return False


# =========================================================
# UI — Prompt bank suggestions
# =========================================================
st.markdown("<hr style='margin: 6px 0 10px 0; opacity: 0.2;'/>", unsafe_allow_html=True)
st.markdown("**Try a question:**")


btn_cols = st.columns(len(PROMPT_BANK))
for i, prompt in enumerate(PROMPT_BANK):
    with btn_cols[i]:
        if st.button(prompt, key=f"pb_{i}"):
            handle_click(prompt)
            st.experimental_rerun()


# =========================================================
# Main handle: when user submits a question
# =========================================================
if user_question and not st.session_state.clear_chat:
    ql = user_question.lower().strip()

    # 1) Lightweight pandas-first tools (headcount, margin/profit%, rev/cost, onshore/offshore)
    handled = _use_kpi_tools_if_available(user_question, df_pnl)
    if not handled:
        # 2) Try configured questions via semantic matcher
        try:
            qid, prompt, score = find_best_matching_qid(ql)
        except Exception:
            qid, prompt, score = None, None, 0.0

        if qid and score >= SIM_THRESHOLD:
            handled = _dispatch_to_qmodule(qid, df_pnl, df_ut, user_question)

    # 3) If still not handled, use LLM router for freeform (if available) else final fallback
    if not handled:
        if any(ql.startswith(t) for t in FREEFORM_TRIGGERS) or ql.endswith("?") or "explain" in ql:
            handled = _llm_route_and_answer(user_question)

    if not handled:
        # 4) Final safety net — generic margin summary
        _generic_margin_summary(df_pnl, user_question)
