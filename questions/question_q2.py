import pandas as pd

def run(query, df):
    # Extract segment from query (assumes last word)
    segment = query.strip().split()[-1]

    # Clean columns
    df.columns = df.columns.str.strip()
    
    # Filter and standardize
    df = df[df["Segment"].str.lower() == segment.lower()]
    df = df[df["Month"].notnull() & df["Company_Code"].notnull()]
    df["Month"] = pd.to_datetime(df["Month"], format="%b %Y")

    # Split Revenue and Cost
    rev_df = df[df["Type"] == "Revenue"]
    cost_df = df[df["Type"] == "Cost"]

    # Monthly totals
    monthly_rev = rev_df.groupby("Month")["Amount in INR"].sum().sort_index()
    monthly_cost = cost_df.groupby("Month")["Amount in INR"].sum().sort_index()

    if len(monthly_cost) < 2 or len(monthly_rev) < 2:
        return f"Not enough monthly data to compute margin trend for segment '{segment}'."

    # Margin % per month
    margin_pct = ((monthly_rev - monthly_cost) / monthly_cost * 100).round(2)
    prev_month, curr_month = margin_pct.index[-2], margin_pct.index[-1]
    prev_margin, curr_margin = margin_pct.iloc[-2], margin_pct.iloc[-1]

    # Summary 1 – Margin movement
    margin_summary = (
        f"1. Margin for **{segment}** reduced from **{prev_margin:.2f}% in {prev_month.strftime('%b')}** "
        f"to **{curr_margin:.2f}% in {curr_month.strftime('%b')}**."
    )

    # Summary 2 – Segment health (client margin drop)
    client_margin = (
        df.groupby(["Company_Code", "Month", "Type"])["Amount in INR"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    client_margin["Margin%"] = ((client_margin["Revenue"] - client_margin["Cost"]) / client_margin["Cost"]) * 100
    pivot = client_margin.pivot(index="Company_Code", columns="Month", values="Margin%").dropna()
    if len(pivot.columns) < 2:
        health_summary = "2. Not enough client-level data to assess segment health."
    else:
        declining_clients = (pivot[curr_month] < pivot[prev_month]).sum()
        total_clients = pivot.shape[0]
        health_summary = (
            f"2. {declining_clients} of {total_clients} clients (**{(declining_clients/total_clients)*100:.0f}%**) "
            f"in **{segment}** saw a drop in margin from **{prev_month.strftime('%b')}** to **{curr_month.strftime('%b')}**."
        )

    # Summary 3 – Cost increase
    cost_change_pct = ((monthly_cost[curr_month] - monthly_cost[prev_month]) / monthly_cost[prev_month]) * 100
    cost_summary = (
        f"3. Total cost in **{segment}** increased by **{cost_change_pct:.2f}%** from "
        f"**{prev_month.strftime('%b')}** to **{curr_month.strftime('%b')}**."
    )

    summary = "\n".join([margin_summary, health_summary, cost_summary])

    # Group4 Top Cost Types
    group4_df = cost_df[cost_df["Group4"].notnull()]
    group4_df = group4_df[group4_df["Month"].isin([prev_month, curr_month])]

    top_group4 = (
        group4_df.groupby(["Group4", "Month"])["Amount in INR"]
        .sum()
        .unstack(fill_value=0)
        .round()
    )

    # Avoid divide by zero
    top_group4["% Change"] = ((top_group4[curr_month] - top_group4[prev_month]) / 
                              top_group4[prev_month].replace(0, 1)) * 100

    # Sort by % increase
    top_group4 = top_group4.sort_values(by="% Change", ascending=False).head(8)

    # Convert to crores
    top_group4[f"{prev_month.strftime('%b')} Cost (Cr)"] = (top_group4[prev_month] / 1e7).round(2)
    top_group4[f"{curr_month.strftime('%b')} Cost (Cr)"] = (top_group4[curr_month] / 1e7).round(2)

    top_cost_table = top_group4[[
        f"{prev_month.strftime('%b')} Cost (Cr)",
        f"{curr_month.strftime('%b')} Cost (Cr)",
        "% Change"
    ]].reset_index().rename(columns={"Group4": "Cost Type"})

    # HTML table
    table_html = top_cost_table.to_html(index=False)

    return summary + "\n\n### 🔍 Top Group4 Cost Increases\n\n" + table_html
