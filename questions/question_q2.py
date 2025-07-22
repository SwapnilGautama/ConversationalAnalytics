import pandas as pd
from utils.helpers import extract_relevant_quarters, extract_latest_quarters, format_in_inr_cr
from utils.visuals import generate_bar_chart
from utils.nlp import capitalize_each_word

def analyze_margin_change_by_segment(pnl_df, segment="Transportation"):
    # ✅ Clean and standardize column names
    pnl_df.columns = pnl_df.columns.str.strip()

    # ✅ Rename expected columns
    pnl_df.rename(columns={
        "Amount in INR": "Amount",
        "Company code": "Company_Code",
        "Month": "Date"
    }, inplace=True)

    # ✅ Filter for relevant groupings
    pnl_df = pnl_df[pnl_df["Group2"].isin(["Revenue - Fixed", "Revenue - Projects", "Costs - Direct Expenses - Onsite", "Costs - Direct Expenses - Offshore"])]
    
    if "Segment" not in pnl_df.columns or "Date" not in pnl_df.columns:
        return {"summary": f"❌ Required columns are missing in data."}

    # ✅ Narrow to segment
    segment_df = pnl_df[pnl_df["Segment"].str.strip().str.lower() == segment.strip().lower()]
    if segment_df.empty:
        return {"summary": f"❌ No data found for segment: {segment}"}

    # ✅ Extract latest 2 quarters
    segment_df["Date"] = pd.to_datetime(segment_df["Date"], errors='coerce')
    segment_df = segment_df.dropna(subset=["Date"])
    latest_qtrs = extract_latest_quarters(segment_df["Date"])
    if len(latest_qtrs) < 2:
        return {"summary": f"⚠️ Only current quarter margin data is available for **{segment}** segment. Please add previous quarter data to compare changes."}

    q1, q2 = latest_qtrs
    q1_df = extract_relevant_quarters(segment_df, [q1])
    q2_df = extract_relevant_quarters(segment_df, [q2])

    def calc_margin(df):
        pivot = df.pivot_table(index="Company_Code", columns="Group2", values="Amount", aggfunc="sum").fillna(0)
        revenue = pivot.get("Revenue - Fixed", 0) + pivot.get("Revenue - Projects", 0)
        cost = pivot.get("Costs - Direct Expenses - Onsite", 0) + pivot.get("Costs - Direct Expenses - Offshore", 0)
        margin = revenue - cost
        margin_pct = (margin / revenue * 100) if revenue.sum() != 0 else 0
        return pd.DataFrame({"Revenue": revenue, "Cost": cost, "Margin": margin, "Margin %": margin_pct})

    q1_metrics = calc_margin(q1_df)
    q2_metrics = calc_margin(q2_df)

    combined = q2_metrics.join(q1_metrics, lsuffix="_q2", rsuffix="_q1", how="outer").fillna(0)
    combined["Δ Margin %"] = combined["Margin %_q2"] - combined["Margin %_q1"]
    combined_sorted = combined.sort_values("Δ Margin %")

    # ✅ Summary
    worst_accounts = combined_sorted.head(3)
    summary_lines = [
        f"📉 Margin dropped in **{segment}** segment from **{q1}** to **{q2}**.",
        f"🔻 Top contributors to the drop:",
    ]
    for acc, row in worst_accounts.iterrows():
        summary_lines.append(
            f"- `{acc}`: Margin % dropped from {row['Margin %_q1']:.1f}% to {row['Margin %_q2']:.1f}% (Δ {row['Δ Margin %']:.1f}%)"
        )

    # ✅ Chart
    chart = generate_bar_chart(
        worst_accounts.reset_index(),
        x_col="Company_Code",
        y_col="Δ Margin %",
        title=f"Top Accounts Causing Margin Drop in {capitalize_each_word(segment)}"
    )

    return {
        "summary": "\n".join(summary_lines),
        "charts": [chart],
        "tables": [{"title": "Margin Comparison", "df": combined_sorted.reset_index()}]
    }

def run(pnl_df, ut_df, user_question):
    return analyze_margin_change_by_segment(pnl_df)
