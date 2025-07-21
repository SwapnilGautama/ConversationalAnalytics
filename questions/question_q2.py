import pandas as pd
import datetime
import matplotlib.pyplot as plt
import io
import base64
from dateutil.relativedelta import relativedelta
from kpi_engine.margin import compute_margin


def extract_segment_from_query(query):
    query = query.lower()
    keywords = ["transportation", "manufacturing", "utilities", "healthcare", "defense", "aerospace"]  # Add more as needed
    for k in keywords:
        if k in query:
            return k.capitalize()
    return None


def run(df_pnl: pd.DataFrame, query: str) -> dict:
    segment = extract_segment_from_query(query)
    if not segment:
        return {"summary": "❌ Could not identify the segment from the query. Please specify a valid segment."}

    df_filtered = df_pnl[df_pnl["segment"].str.lower() == segment.lower()].copy()
    if df_filtered.empty:
        return {"summary": f"❌ No data found for segment: {segment}"}

    df_margin = calculate_margin(df_filtered)
    df_margin["Quarter"] = pd.to_datetime(df_margin["Month"])
    df_margin["Quarter"] = df_margin["Quarter"].dt.to_period("Q")

    latest_quarter = df_margin["Quarter"].max()
    prev_quarter = (latest_quarter - 1)

    current = df_margin[df_margin["Quarter"] == latest_quarter]
    previous = df_margin[df_margin["Quarter"] == prev_quarter]

    if current.empty or previous.empty:
        return {"summary": f"❌ Not enough quarterly data available for segment: {segment}"}

    current_avg = current["Margin %"].mean()
    previous_avg = previous["Margin %"].mean()
    diff = current_avg - previous_avg

    trend = "decreased" if diff < 0 else "increased"
    pct = abs(diff)
    summary = f"🔍 In the **{segment}** segment, average margin {trend} by **{pct:.2f}%** in the last quarter compared to the previous quarter."

    client_comparison = current.groupby("Client")["Margin %"].mean().sort_values()
    table = client_comparison.reset_index().rename(columns={"Margin %": "Avg Margin %"})

    # Chart
    fig, ax = plt.subplots(figsize=(6, 4))
    client_comparison.plot(kind="barh", ax=ax, color="coral")
    ax.set_xlabel("Avg Margin %")
    ax.set_ylabel("Client")
    ax.set_title(f"Client Margin% in {segment} Segment - Q{latest_quarter.quarter} {latest_quarter.start_time.year}")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()

    return {
        "summary": summary,
        "table": table.to_dict(orient="records"),
        "chart": chart_base64
    }
