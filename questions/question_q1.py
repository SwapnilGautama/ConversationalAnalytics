# ✅ FILE: questions/question_q1.py

import pandas as pd
from kpi_engine.margin import compute_margin_kpi  # ✅ corrected name

def run(pnl_df: pd.DataFrame, ut_df: pd.DataFrame):
    try:
        # Call correct KPI function
        cm_df = compute_margin_kpi(pnl_df)

        # Ensure expected columns exist
        required_columns = ["Quarter", "CM%", "Company Code"]
        for col in required_columns:
            if col not in cm_df.columns:
                return {
                    "summary": f"❌ Missing column in KPI output: {col}",
                    "table": pd.DataFrame(),
                }

        # Use most recent quarter
        latest_qtr = cm_df["Quarter"].max()

        # Filter for CM% < 30
        filtered_df = cm_df[(cm_df["Quarter"] == latest_qtr) & (cm_df["CM%"] < 30)]

        if filtered_df.empty:
            return {
                "summary": f"No accounts had CM% < 30 in {latest_qtr}.",
                "table": pd.DataFrame(),
            }

        summary = f"📉 These accounts had CM% < 30 in **{latest_qtr}**:"
        table = filtered_df[["Company Code", "Quarter", "CM%"]].reset_index(drop=True)

        return {
            "summary": summary,
            "table": table,
        }

    except Exception as e:
        return {
            "summary": f"❌ Error running Q1 logic: {str(e)}",
            "table": pd.DataFrame(),
        }
