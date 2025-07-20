# questions/question_q1.py

import pandas as pd
from kpi_engine.margin import compute_margin
from dateutil.relativedelta import relativedelta

def run_question(df):
    df_margin = compute_margin(df)

    if "Month" not in df_margin or "Client" not in df_margin or "Margin %" not in df_margin:
        return {
            "error": "Required fields missing. Ensure Margin % calculation is correctly applied."
        }

    # Get the latest quarter
    latest_month = df_margin["Month"].max()
    quarter_start = latest_month - relativedelta(months=2)
    quarter_data = df_margin[df_margin["Month"] >= quarter_start]

    # Group by Client and calculate average margin
    grouped = (
        quarter_data.groupby("Client")["Margin %"]
        .mean()
        .reset_index()
        .rename(columns={"Margin %": "Avg Margin %"})
    )

    # Remove rows with NaN or invalid values
    grouped = grouped.dropna(subset=["Avg Margin %"])
    grouped["Avg Margin %"] = grouped["Avg Margin %"].round(2)

    # Filter where margin is less than 30%
    low_margin_clients = grouped[grouped["Avg Margin %"] < 30].copy()

    # 🔹 Text summary
    total_clients = grouped["Client"].nunique()
    low_margin_count = low_margin_clients["Client"].nunique()
    proportion = (low_margin_count / total_clients * 100) if total_clients else 0

    summary = (
        f"🔍 In the last quarter, {low_margin_count} accounts had an average margin below 30% "
        f"— which is {proportion:.1f}% of all {total_clients} accounts."
    )

    return {
        "summary": summary,
        "table": low_margin_clients.sort_values("Avg Margin %"),
    }
