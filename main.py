# app.py
from typing import Any, Dict
from fastapi import FastAPI
from utils.semantic_matcher import find_best_matching_qid
import importlib
import inspect
import os
import pandas as pd
from kpi_engine import margin

app = FastAPI()
SIM_THRESHOLD = 0.72
FREEFORM_TRIGGERS = ("ai:", "freeform:", "ad-hoc:")

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

try:
    df_pnl = load_pnl()
except Exception as e:
    print(e)

@app.post("/ques")
async def analyze(question: str) -> Dict[str, Any]:
    """
    Analyze a user question:
    1. Find best matching QID from prompt bank.
    2. Dynamically import corresponding question module and run its 'run' function.
    3. Return results as JSON.
    """
    # Find best QID
    res = find_best_matching_qid(question)
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

    # Check for AI fallback / low score
    force_ai = question.lower().strip().startswith(FREEFORM_TRIGGERS)
    low_score = (score is not None and score < SIM_THRESHOLD)

    response: Dict[str, Any] = {
        "best_qid": best_qid,
        "matched_prompt": matched_prompt,
        "score": score,
        "force_ai": force_ai,
        "low_score": low_score,
        "result": None,
        "error": None
    }

    try:
        # Dynamically import question module
        question_module = importlib.import_module(f"questions.question_{best_qid.lower()}")
        run_func = getattr(question_module, "run", None)

        if run_func is None:
            raise AttributeError(f"'run' function not found in module for {best_qid}")

        # Check function signature to pass parameters
        run_params = inspect.signature(run_func).parameters
        if len(run_params) >= 2:
            result = run_func(df_pnl, question)  
        else:
            result = run_func(df_pnl)

        # Prepare JSON-serializable result
        if isinstance(result, pd.DataFrame):
            response["result"] = result.to_dict(orient="records")
        else:
            response["result"] = result

    except Exception as e:
        response["error"] = str(e)

    return response
