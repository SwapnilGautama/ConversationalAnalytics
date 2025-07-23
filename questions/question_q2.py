import pandas as pd
import matplotlib.pyplot as plt
import io

def run(**kwargs):
    # Extract user input segment
    segment = kwargs.get("segment", "Transportation")

    # Load the LnTPnL data
    file_path = "sample_data/LnTPnL.xlsx"
    df = pd.read_excel(file_path)

    # Standardize columns
    df.columns = df.columns.str.strip()

    # Filter by Segment and remove nulls
    df = df[df["Segment"] == segment]
    df = df[df["Month"].notnull()]
    df = df[df["Company_Code"].notnull()]
    df["Month"] = pd.to_datetime(df["Month"], format="%b %Y")

    # Separate Revenue and Cost
    rev_df = df[df["Type"] == "Revenue"]
    cost_df = df[df["Type"] == "Cost"]

    # Aggregate revenue and cost at segment level per month
    monthly_rev = rev_df.groupby("Month")["Amount in INR"].sum().sort_index()
    monthly_cost = cost_df.groupby("Month")["Amount in INR"].sum().sort_index()

    # Compute margin %
    margin_pct = ((monthly_rev - monthly_cost) / monthly_cost * 100).round(2)

    # Get current and previous month
    if len(margin_pct) < 2:
        return "Not enough monthly data to compute margin trend."
    prev_month, curr_month = margin_pct.index[-2], margin_pct.index[-1]

    # Text summary 1 – Margin movement
    prev_margin, curr_margin = margin_pct.iloc[-2], margin_pct.iloc[-1]
    margin_trend = f"1. Margin for {segment} changed from {prev_margin:.2f}% in {prev_month.strftime('%b')} to {curr_margin:.2f}% in {curr_month.strftime('%b')}."

    # Text summary 2 – Segment health (client-level margin drop)
    client_margin = (
        df.groupby(["Company_Code", "Month", "Type"])["Amount in INR"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    client_margin["Margin%"] = ((client_margin["Revenue"] - client_margin["Cost"]) / client_margin["Cost"]) * 100
    pivot = client_margin.pivot(index="Company_Code", columns="Month", values="Margin%")
    pivot = pivot.dropna()
    if len(pivot.columns) < 2:
        segment_health = "2. Not enough client-level data to assess segment health."
    else:
        prev_m, curr_m = pivot.columns[-2], pivot.columns[-1]
        declining_clients = (pivot[curr_m] < pivot[prev_m]).sum()
        total_clients = pivot.shape[0]
        segment_health = f"2. {declining_clients} of {total_clients} clients ({(declining_clients/total_clients)*100:.0f}%) in {segment} saw a drop in margin from {prev_m.strftime('%b')} to {curr_m.strftime('%b')}."

    # Text summary 3 – Cost movement
    cost_change_pct = ((monthly_cost.iloc[-1] - monthly_cost.iloc[-2]) / monthly_cost.iloc[-2]) * 100
    cost_trend = f"3. Total cost in {segment} increased by {cost_change_pct:.2f}% from {prev_month.strftime('%b')} to {curr_month.strftime('%b')}."

    summary = "\n".join([margin_trend, segment_health, cost_trend])

    # Group4 Cost Type Analysis
    group4 = cost_df[cost_df["Group4"].notnull()]
    group4_months = group4[group4["Month"].isin([prev_month, curr_month])]
    pivot_group4 = (
        group4_months.groupby(["Group4", "Month"])["Amount in INR"]
        .sum()
        .unstack()
        .fillna(0)
        .round()
    )
    pivot_group4["% Change"] = ((pivot_group4[curr_month] - pivot_group4[prev_month]) / pivot_group4[prev_month].replace(0, 1)) * 100
    pivot_group4 = pivot_group4.sort_values(by="% Change", ascending=False)
    top_costs = pivot_group4.head(8).copy()
    top_costs = top_costs.rename(
        columns={
            prev_month: f"{prev_month.strftime('%b')} Cost (Cr)",
            curr_month: f"{curr_month.strftime('%b')} Cost (Cr)",
        }
    )
    for col in top_costs.columns[:2]:
        top_costs[col] = (top_costs[col] / 1e7).round(2)

    # Convert to HTML
    table_html = top_costs.reset_index().to_html(index=False)

    return summary + "\n\n### Top Group4 Cost Increases\n\n" + table_html
