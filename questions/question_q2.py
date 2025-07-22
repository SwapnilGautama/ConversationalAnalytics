import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

def extract_Segment_from_query(query):
    query_lower = query.lower()
    if "transport" in query_lower:
        return "Transportation"
    elif "plant" in query_lower:
        return "Plant Engineering"
    elif "media" in query_lower or "technology" in query_lower:
        return "Media & Technology"
    else:
        return None

def calculate_margin_diff(df, segment):
    df_segment = df[df["Segment"] == segment].copy()
    if df_segment.empty:
        return None, None

    # ✅ Safeguard: Check for required 'Date' column
    if "Month" not in df_segment.columns:
        return None, None

    df_segment["Quarter"] = pd.to_datetime(df_segment["Month"], errors="coerce").dt.to_period("Q")
    grouped = df_segment.groupby(["Quarter", "Client"]).agg({"Margin": "sum", "Revenue": "sum"}).reset_index()
    grouped["Margin %"] = (grouped["Margin"] / grouped["Revenue"]) * 100

    latest_two_quarters = sorted(grouped["Quarter"].dropna().unique())[-2:]
    if len(latest_two_quarters) < 2:
        return grouped, None

    current = grouped[grouped["Quarter"] == latest_two_quarters[1]]
    previous = grouped[grouped["Quarter"] == latest_two_quarters[0]]

    merged = pd.merge(current, previous, on="Client", suffixes=("_curr", "_prev"))
    merged["Avg Margin %"] = merged["Margin %_curr"] - merged["Margin %_prev"]
    merged = merged[["Client", "Avg Margin %"]].sort_values(by="Avg Margin %")

    return merged, grouped

def run(df_pnl: pd.DataFrame, query: str) -> dict:
    Segment = extract_Segment_from_query(query)

    if Segment is None or (isinstance(Segment, pd.Series) and Segment.empty):
        return {"summary": "❌ Could not identify the Segment from the query. Please specify a valid Segment."}

    table_data, full_margin_data = calculate_margin_diff(df_pnl, Segment)

    if table_data is None or table_data.empty:
        return {"summary": f"❌ Margin data is missing or incomplete for segment: {Segment}"}

    avg_margin_change = table_data["Avg Margin %"].mean()
    summary = f"🔍 In the **{Segment}** Segment, average margin changed by **{avg_margin_change:.2f}%** in the last quarter compared to the previous quarter."

    table = table_data.to_dict(orient="records")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(table_data["Client"], table_data["Avg Margin %"], color="orange")
    ax.set_title(f"{Segment} - Margin % Change by Client")
    ax.set_ylabel("Change in Margin %")
    ax.set_xlabel("Client")
    plt.xticks(rotation=45)

    img_buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img_buffer, format="png")
    plt.close(fig)
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.read()).decode("utf-8")

    return {
        "summary": summary,
        "table": table,
        "chart": img_base64
    }
