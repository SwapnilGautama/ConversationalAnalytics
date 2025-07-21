import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

from kpi_engine.margin import compute_margin_by_quarter
from utils.helpers import render_table, extract_quarters, return_latest_quarters

def run(pnl_df: pd.DataFrame, ut_df: pd.DataFrame = None, **kwargs) -> dict:
    # Filter for Transportation segment
    transportation_df = pnl_df[pnl_df["segment"].str.lower() == "transportation"]

    if transportation_df.empty:
        return {
            "summary": "🚨 No P&L data available for the Transportation segment.",
            "table": None
        }

    # Extract quarter column
    transportation_df["Quarter"] = extract_quarters(transportation_df["Date"])

    # Calculate margins by quarter
    margin_df = compute_margin_by_quarter(transportation_df)

    # Sort and get last 2 quarters
    sorted_quarters = return_latest_quarters(margin_df["Quarter"].unique())
    if len(sorted_quarters) < 2:
        return {"summary": "🕒 Not enough quarters available for margin trend comparison.", "table": None}

    q1, q2 = sorted_quarters[-2], sorted_quarters[-1]
    margin_q1 = margin_df[margin_df["Quarter"] == q1]["Margin %"].mean()
    margin_q2 = margin_df[margin_df["Quarter"] == q2]["Margin %"].mean()
    margin_drop = margin_q2 - margin_q1

    # Analyze major cost contributors to the margin drop
    cost_breakdown = transportation_df[transportation_df["Quarter"].isin([q1, q2])]
    grouped_costs = cost_breakdown.groupby(["Cost Element", "Quarter"])["Amount in INR"].sum().unstack().fillna(0)
    grouped_costs["Change"] = grouped_costs[q2] - grouped_costs[q1]
    grouped_costs["Change %"] = (grouped_costs["Change"] / grouped_costs[q1].replace(0, 1)) * 100
    top_contributors = grouped_costs.sort_values("Change", ascending=False).head(5).reset_index()

    # Summary
    summary = (
        f"🛣️ The margin for the **Transportation** segment dropped from **{margin_q1:.2f}%** in {q1} "
        f"to **{margin_q2:.2f}%** in {q2}, a change of **{margin_drop:.2f} percentage points**.\n\n"
        f"Top cost elements contributing to this drop:"
    )

    # Table rendering
    table_md = render_table(
        top_contributors[["Cost Element", q1, q2, "Change", "Change %"]].rename(
            columns={
                q1: f"Cost in {q1}",
                q2: f"Cost in {q2}",
                "Change": "₹ Change",
                "Change %": "% Change"
            }
        )
    )

    # Optional: Add bar chart as visual
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(top_contributors["Cost Element"], top_contributors["Change"], color="orange")
    ax.set_xlabel("Change in Cost (INR)")
    ax.set_title("Top 5 Cost Elements Causing Margin Drop (Transportation)")
    plt.tight_layout()

    # Convert plot to base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    img_html = f"<img src='data:image/png;base64,{img_base64}'/>"

    return {
        "summary": summary,
        "table": table_md,
        "visual": img_html
    }
