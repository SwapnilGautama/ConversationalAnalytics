import pandas as pd

def compare_cb_variation_quarters(pnl_df: pd.DataFrame) -> dict:
    """
    Compare C&B Cost between FY25Q4 (Jan–Mar) and FY26Q1 (Apr–Jun)
    """
    # Define months by quarter
    q4_months = ["Jan-25", "Feb-25", "Mar-25"]
    q1_months = ["Apr-25", "May-25", "Jun-25"]

    # Filter relevant rows
    cb_df = pnl_df[
        (pnl_df["Group Description"] == "C&B Cost") &
        (pnl_df["Month"].isin(q4_months + q1_months))
    ]

    # Aggregate
    totals = cb_df.groupby("Month")["Amount in USD"].sum()
    q4_total = totals[q4_months].sum()
    q1_total = totals[q1_months].sum()

    delta = q1_total - q4_total
    pct_change = (delta / q4_total * 100) if q4_total else None

    summary = (
        f"C&B cost was ${q4_total:,.0f} in FY25Q4 and ${q1_total:,.0f} in FY26Q1.\n"
        f"The change is ${delta:,.0f} ({pct_change:.2f}% {'increase' if delta > 0 else 'decrease'})."
    )

    return {
        "summary": summary,
        "table": pd.DataFrame({
            "Quarter": ["FY25Q4", "FY26Q1"],
            "C&B Cost": [q4_total, q1_total]
        }),
        "chart": {
            "x": ["FY25Q4", "FY26Q1"],
            "y": [q4_total, q1_total],
            "title": "C&B Cost Comparison by Quarter",
            "xlabel": "Quarter",
            "ylabel": "Cost (USD)"
        }
    }
