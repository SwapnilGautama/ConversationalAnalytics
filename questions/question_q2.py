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
        return f"❗ Not enough data for MoM comparison in segment: {segment_input}", None

    prev_month, curr_month = latest_months
    df = df[df["Month"].dt.to_period("M").isin([prev_month, curr_month])]

    # Aggregate data
    agg_cols = ["Amount in INR"]
    group_cols = ["Company_Code", "Type", "MonthStr"]
    df_agg = df.groupby(group_cols)[agg_cols].sum().reset_index()

    # Pivot revenue and cost
    revenue_df = df_agg[df_agg["Type"] == "Revenue"].pivot(index="Company_Code", columns="MonthStr", values="Amount in INR").fillna(0)
    cost_df = df_agg[df_agg["Type"] == "Cost"].pivot(index="Company_Code", columns="MonthStr", values="Amount in INR").fillna(0)

    rev_cols = list(revenue_df.columns)
    cost_cols = list(cost_df.columns)

    # Calculate deltas
    revenue_df["Revenue_Change"] = revenue_df[rev_cols[1]].values - revenue_df[rev_cols[0]].values
    cost_df["Cost_Change"] = cost_df[cost_cols[1]].values - cost_df[cost_cols[0]].values

    # Merge
    merged = revenue_df[["Revenue_Change"]].merge(cost_df[["Cost_Change"]], left_index=True, right_index=True)
    merged["Margin_Change"] = merged["Revenue_Change"] - merged["Cost_Change"]
    merged = merged.sort_values(by="Margin_Change")

    # Group-level breakdown
    cost_groups = ["Group 1", "Group 2", "Group 3", "Group 4"]
    insights = {}
    for group in cost_groups:
        group_df = df[df["Type"] == "Cost"].groupby(["MonthStr", group])["Amount in INR"].sum().unstack().fillna(0)
        if len(group_df) >= 2:
            group_df["Change"] = group_df.iloc[-1] - group_df.iloc[-2]
            top_increase = group_df["Change"].sort_values(ascending=False).head(1)
            if not top_increase.empty:
                insights[group] = top_increase.index[0]

    # Text summary
    total_rev = df[df["Type"] == "Revenue"].groupby("MonthStr")["Amount in INR"].sum()
    total_cost = df[df["Type"] == "Cost"].groupby("MonthStr")["Amount in INR"].sum()

    summary = f"""
### 🔍 Summary
- **Revenue movement**: {rev_cols[0]} = ₹{total_rev[rev_cols[0]]:,.0f}, {rev_cols[1]} = ₹{total_rev[rev_cols[1]]:,.0f}
- **Cost movement**: {cost_cols[0]} = ₹{total_cost[cost_cols[0]]:,.0f}, {cost_cols[1]} = ₹{total_cost[cost_cols[1]]:,.0f}

### 💡 Group cost contributors to increase:
"""
    for group, cause in insights.items():
        summary += f"- {group}: {cause}\n"

    # Plot
    plt.figure(figsize=(10, 5))
    sns.barplot(data=merged.reset_index(), x="Company_Code", y="Margin_Change", palette="coolwarm")
    plt.title("Margin Change by Client")
    plt.xticks(rotation=45)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()

    return summary, img_base64


# ✅ Wrapper function for chatbot
def run(segment_input):
    return analyze_margin_drop(segment_input)
