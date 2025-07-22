import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime

def analyze_margin_drop(segment_input):
    # Load data
    file_path = "sample_data/LnTPnL.xlsx"
    df = pd.read_excel(file_path)

    # Clean and transform
    df["Month"] = pd.to_datetime(df["Month"])
    df["MonthStr"] = df["Month"].dt.strftime("%b-%Y")
    df = df[df["Segment"] == segment_input]

    # Get latest 2 months
    latest_months = sorted(df["Month"].dt.to_period("M").unique())[-2:]
    if len(latest_months) < 2:
        return f"❗ Not enough data for MoM comparison in segment: {segment_input}"

    prev_month, curr_month = latest_months
    df = df[df["Month"].dt.to_period("M").isin([prev_month, curr_month])]

    # Aggregate data
    agg = df.groupby(["Company_Code", "Type", "MonthStr"])[["Amount in INR"]].sum().reset_index()
    pivot = agg.pivot_table(index="Company_Code", columns=["Type", "MonthStr"], values="Amount in INR", fill_value=0)
    pivot.columns = [f"{t}_{m}" for t, m in pivot.columns]
    pivot = pivot.reset_index()

    # Compute Revenue, Cost, Margin, Margin %
    try:
        rev_cols = [c for c in pivot.columns if "Revenue" in c]
        cost_cols = [c for c in pivot.columns if "Cost" in c]
        pivot["RevDiff"] = pivot[rev_cols[1]] - pivot[rev_cols[0]]
        pivot["CostDiff"] = pivot[cost_cols[1]] - pivot[cost_cols[0]]
        pivot["MarginPrev"] = pivot[rev_cols[0]] - pivot[cost_cols[0]]
        pivot["MarginCurr"] = pivot[rev_cols[1]] - pivot[cost_cols[1]]
        pivot["MarginDrop"] = pivot["MarginPrev"] - pivot["MarginCurr"]
        pivot["Margin%Prev"] = pivot["MarginPrev"] / pivot[cost_cols[0]].replace(0, 1)
        pivot["Margin%Curr"] = pivot["MarginCurr"] / pivot[cost_cols[1]].replace(0, 1)
    except Exception as e:
        return f"❗ Error during margin computation: {e}"

    # Identify clients with margin drop due to cost increase
    margin_issues = pivot[(pivot["MarginDrop"] > 0) & (pivot["RevDiff"].abs() < pivot["CostDiff"].abs())]

    if margin_issues.empty:
        return f"✅ No significant margin drops detected in segment {segment_input} for cost increase analysis."

    # Breakdown cost increase by groups
    df_cost = df[(df["Type"] == "Cost") & (df["Month"].dt.to_period("M") == curr_month)]
    group_costs = df_cost.groupby("Group1")["Amount in INR"].sum().sort_values(ascending=False)

    # Summary
    rev_movement = df[df["Type"] == "Revenue"].groupby("MonthStr")["Amount in INR"].sum()
    cost_movement = df[df["Type"] == "Cost"].groupby("MonthStr")["Amount in INR"].sum()
    summary = f"""
🔹 **Segment: {segment_input}**  
🔹 Revenue changed from ₹{rev_movement.iloc[0]:,.0f} to ₹{rev_movement.iloc[1]:,.0f}  
🔹 Cost changed from ₹{cost_movement.iloc[0]:,.0f} to ₹{cost_movement.iloc[1]:,.0f}  

📌 Top Cost Groups by Contribution:
"""
    for g, val in group_costs.head(5).items():
        summary += f"\n- {g}: ₹{val:,.0f}"

    # Table Plot
    table_data = margin_issues[["Company_Code", "Margin%Prev", "Margin%Curr", "MarginDrop"]].sort_values("MarginDrop", ascending=False)
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.axis("off")
    tbl = ax1.table(cellText=table_data.values, colLabels=table_data.columns, loc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)

    buf1 = io.BytesIO()
    plt.savefig(buf1, format="png", bbox_inches="tight")
    plt.close(fig1)
    table_encoded = base64.b64encode(buf1.getvalue()).decode("utf-8")

    # Pie Plot
    fig2, ax2 = plt.subplots()
    top_clients = table_data.set_index("Company_Code")["MarginDrop"]
    ax2.pie(top_clients, labels=top_clients.index, autopct='%1.1f%%', startangle=140)
    ax2.set_title("Margin Drop Contribution by Client")

    buf2 = io.BytesIO()
    plt.savefig(buf2, format="png", bbox_inches="tight")
    plt.close(fig2)
    pie_encoded = base64.b64encode(buf2.getvalue()).decode("utf-8")

    return {
        "summary": summary,
        "table_base64": table_encoded,
        "pie_base64": pie_encoded
    }

# Example (replace with actual user input dynamically)
result = analyze_margin_drop("Plant Engineering")
result["summary"] if isinstance(result, dict) else result
