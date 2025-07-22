import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

def analyze_margin_change_by_segment(pnl_df, segment_name):
    # Step 1: Clean date and filter for segment
    df = pnl_df.copy()
    df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
    df = df[df["Segment"] == segment_name].copy()
    df.dropna(subset=["Month"], inplace=True)

    if df.empty:
        return {
            "summary": f"Only current quarter margin data is available for **{segment_name}** segment. Please add previous quarter data to compare changes.",
            "table": [],
            "chart": None
        }

    # Step 2: Create Revenue and Cost columns
    df["Revenue"] = df.apply(lambda row: row["Amount in INR"] if "Revenue" in str(row["Group1"]) else 0, axis=1)
    df["Cost"] = df.apply(lambda row: row["Amount in INR"] if "Cost" in str(row["Group1"]) else 0, axis=1)
    df["Margin"] = df["Revenue"] - df["Cost"]

    # Step 3: Assign Quarter
    df["Quarter"] = df["Month"].dt.to_period("Q")

    # Step 4: Aggregate by Client and Quarter
    agg_df = df.groupby(["Company_Code", "Quarter"]).agg({"Revenue": "sum", "Cost": "sum", "Margin": "sum"}).reset_index()
    agg_df.sort_values(by=["Company_Code", "Quarter"], inplace=True)

    # Step 5: Pivot to get current and previous quarter side-by-side
    pivot_df = agg_df.pivot(index="Company_Code", columns="Quarter", values="Margin")
    pivot_df.columns = [str(col) for col in pivot_df.columns]
    pivot_df = pivot_df.reset_index()

    if pivot_df.shape[1] < 3:
        return {
            "summary": f"Only current quarter margin data is available for **{segment_name}** segment. Please add previous quarter data to compare changes.",
            "table": [],
            "chart": None
        }

    # Step 6: Identify current and previous quarters
    quarters = sorted(df["Quarter"].unique())
    curr_q, prev_q = str(quarters[-1]), str(quarters[-2])

    # Step 7: Calculate Margin %
    def calc_margin_change(row):
        curr_margin = row.get(curr_q, 0)
        prev_margin = row.get(prev_q, 0)
        if pd.isna(curr_margin) or pd.isna(prev_margin) or prev_margin == 0:
            return float('inf') if prev_margin == 0 and curr_margin > 0 else float('nan')
        return ((curr_margin - prev_margin) / abs(prev_margin)) * 100

    pivot_df["Avg Margin %"] = pivot_df.apply(calc_margin_change, axis=1)

    # Step 8: Format table
    table = []
    for _, row in pivot_df.iterrows():
        table.append({
            "Client": row["Company_Code"],
            "Avg Margin %": row["Avg Margin %"]
        })

    # Step 9: Create chart
    fig, ax = plt.subplots(figsize=(6, 3))
    clients = pivot_df["Company_Code"]
    margins = pivot_df["Avg Margin %"].fillna(0)
    ax.bar(clients, margins, color='skyblue')
    ax.axhline(0, color='gray', linestyle='--')
    ax.set_title("Client-wise Margin % Change")
    ax.set_xlabel("Client")
    ax.set_ylabel("Margin %")
    plt.xticks(rotation=45, ha='right')

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()

    # Step 10: Final summary
    avg_margin_change = pivot_df["Avg Margin %"].mean(skipna=True)
    if pd.isna(avg_margin_change):
        summary = f"Only current quarter margin data is available for **{segment_name}** segment. Please add previous quarter data to compare changes."
    else:
        direction = "increased" if avg_margin_change > 0 else "decreased"
        summary = f"🔍 In the **{segment_name}** Segment, average margin {direction} by **{avg_margin_change:.2f}%** in the last quarter compared to the previous quarter."

    return {
        "summary": summary,
        "table": table,
        "chart": chart_base64
    }
def run(pnl_df, user_query):
    # Extract segment name from the query
    segment_keywords = ["transportation", "plant", "hi-tech", "consumer", "medical", "industrial", "auto", "auto parts", "plant engineering"]
    matched_segment = None
    for keyword in segment_keywords:
        if keyword.lower() in user_query.lower():
            matched_segment = keyword.title()
            break
    if not matched_segment:
        matched_segment = "Transportation"  # default fallback

    return analyze_margin_change_by_segment(pnl_df, matched_segment)
