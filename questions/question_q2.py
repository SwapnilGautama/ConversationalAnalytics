# ✅ FINAL version of question_q2.py (128 lines) with all fixes applied

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run(pnl_df: pd.DataFrame, segment_filter: str = None):
    st.info(f"🔎 Running Q2 analysis for segment: **{segment_filter}**")

    # Normalize column names
    pnl_df.columns = pnl_df.columns.str.strip()

    # Confirm required columns exist
    required_cols = {'Month', 'Company_Code', 'Segment', 'Type', 'Amount in INR', 'Group1', 'Group2', 'Group3', 'Group4'}
    if not required_cols.issubset(set(pnl_df.columns)):
        st.error(f"Missing required columns in LnTPnL.xlsx: {required_cols - set(pnl_df.columns)}")
        return None

    # Convert Month to datetime
    pnl_df["Month"] = pd.to_datetime(pnl_df["Month"], errors='coerce')
    pnl_df = pnl_df.dropna(subset=["Month"])

    # Filter latest 2 months
    recent_months = sorted(pnl_df["Month"].unique())[-2:]
    if len(recent_months) < 2:
        st.error("Not enough data to compare last two months.")
        return None

    current_month, previous_month = recent_months[-1], recent_months[-2]

    # Apply segment filter if provided
    if segment_filter:
        segment_filter = segment_filter.lower().strip()
        matched_segments = [seg for seg in pnl_df["Segment"].unique() if segment_filter in seg.lower()]
        if not matched_segments:
            st.warning(f"No segment found matching '{segment_filter}'. Showing data for all segments.")
        else:
            pnl_df = pnl_df[pnl_df["Segment"].isin(matched_segments)]

    # Split revenue and cost
    revenue_df = pnl_df[pnl_df["Type"] == "Revenue"]
    cost_df = pnl_df[pnl_df["Type"] == "Cost"]

    # Aggregate revenue by month and company
    revenue_summary = revenue_df.groupby(["Company_Code", "Month"])["Amount in INR"].sum().unstack().fillna(0)
    revenue_summary.columns = ['Revenue_previous', 'Revenue_current']
    revenue_summary["Revenue_Change"] = revenue_summary["Revenue_current"] - revenue_summary["Revenue_previous"]

    # Aggregate total cost by month and company
    total_cost_summary = cost_df.groupby(["Company_Code", "Month"])["Amount in INR"].sum().unstack().fillna(0)
    total_cost_summary.columns = ['Cost_previous', 'Cost_current']
    total_cost_summary["Cost_Change"] = total_cost_summary["Cost_current"] - total_cost_summary["Cost_previous"]

    # Aggregate cost groups (Group1–4)
    cost_groups = []
    for group_col in ['Group1', 'Group2', 'Group3', 'Group4']:
        group_cost = (
            cost_df.groupby(["Company_Code", group_col, "Month"])["Amount in INR"]
            .sum()
            .unstack(fill_value=0)
            .reset_index()
        )
        group_cost.columns.name = None
        group_cost["Group"] = group_col
        cost_groups.append(group_cost)

    # Combine all groups
    group_cost_df = pd.concat(cost_groups)
    group_cost_df = group_cost_df.rename(columns={previous_month: "Amount_previous", current_month: "Amount_current"})
    group_cost_df["Amount_Change"] = group_cost_df["Amount_current"] - group_cost_df["Amount_previous"]

    # Identify dominant cost driver per company
    top_cost_contributors = (
        group_cost_df.groupby("Company_Code")
        .apply(lambda x: x.loc[x["Amount_Change"].idxmax()])
        .reset_index(drop=True)
    )[["Company_Code", "Group", group_col, "Amount_Change"]]

    # Merge revenue + cost + driver
    merged = pd.concat([revenue_summary, total_cost_summary], axis=1)
    merged = merged.merge(top_cost_contributors, on="Company_Code", how="left")
    merged["Margin_current"] = merged["Revenue_current"] - merged["Cost_current"]
    merged["Margin_previous"] = merged["Revenue_previous"] - merged["Cost_previous"]
    merged["Margin_Change"] = merged["Margin_current"] - merged["Margin_previous"]

    # Margin % calculation
    merged["Margin_%"] = ((merged["Revenue_current"] - merged["Cost_current"]) / merged["Cost_current"]) * 100

    # Filter for margin drop cases with nearly constant or slightly dropped revenue
    drop_cases = merged[
        (merged["Margin_Change"] < 0) &
        (merged["Revenue_Change"] > -0.1 * merged["Revenue_previous"]) &
        (merged["Cost_Change"] > 0)
    ].sort_values("Margin_Change")

    if drop_cases.empty:
        st.warning("No margin drop cases identified with stable revenue and rising cost.")
        return

    # Display results
    st.subheader(f"🔻 Top {min(5, len(drop_cases))} Clients with Margin Drop Due to Cost Increase")
    st.dataframe(drop_cases.head(5)[[
        "Revenue_previous", "Revenue_current", "Revenue_Change",
        "Cost_previous", "Cost_current", "Cost_Change",
        "Margin_previous", "Margin_current", "Margin_Change", "Margin_%" ,
        group_col, "Group", "Amount_Change"
    ]].style.format("{:.2f}"))

    # Plot
    fig, ax = plt.subplots()
    drop_cases_sorted = drop_cases.sort_values("Margin_Change").head(5)
    ax.bar(drop_cases_sorted.index, drop_cases_sorted["Margin_Change"], color="red")
    ax.set_title(f"Margin Drop - Top Clients ({segment_filter or 'All Segments'})")
    ax.set_ylabel("Margin Change (INR)")
    st.pyplot(fig)
