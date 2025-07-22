import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from dateutil import parser

def question_q2(ln_tpnl_df: pd.DataFrame, segment_filter: str = "Transportation"):
    try:
        # Ensure correct datetime format
        ln_tpnl_df["Month"] = pd.to_datetime(ln_tpnl_df["Month"])
        
        # Filter segment (dynamic)
        df = ln_tpnl_df[ln_tpnl_df["Segment"].str.lower() == segment_filter.lower()]

        # Filter for last 2 months
        latest_month = df["Month"].max()
        previous_month = latest_month - pd.DateOffset(months=1)
        df_recent = df[df["Month"].isin([latest_month, previous_month])]

        # Separate revenue and cost
        df_revenue = df_recent[df_recent["Type"].str.lower() == "revenue"]
        df_cost = df_recent[df_recent["Type"].str.lower() == "cost"]

        # Sum revenue per company per month
        revenue_summary = df_revenue.groupby(["Company_Code", "Month"])["Amount in INR"].sum().unstack().fillna(0)
        revenue_summary.columns = ["Previous_Revenue", "Current_Revenue"] if previous_month < latest_month else ["Current_Revenue", "Previous_Revenue"]
        revenue_summary.reset_index(inplace=True)

        # Sum cost per company per month per Group (1 to 4)
        group_cols = ["Group1", "Group2", "Group3", "Group4"]
        cost_summary = (
            df_cost.groupby(["Company_Code", "Month"])[["Amount in INR"] + group_cols]
            .sum()
            .reset_index()
        )

        cost_pivot = cost_summary.pivot(index="Company_Code", columns="Month", values="Amount in INR").fillna(0)
        cost_pivot.columns = ["Previous_Cost", "Current_Cost"] if previous_month < latest_month else ["Current_Cost", "Previous_Cost"]
        cost_pivot.reset_index(inplace=True)

        # Merge revenue and cost
        merged = pd.merge(revenue_summary, cost_pivot, on="Company_Code", how="outer").fillna(0)

        # Calculate margin %
        merged["Previous_Margin%"] = ((merged["Previous_Revenue"] - merged["Previous_Cost"]) / merged["Previous_Cost"].replace(0, 1)) * 100
        merged["Current_Margin%"] = ((merged["Current_Revenue"] - merged["Current_Cost"]) / merged["Current_Cost"].replace(0, 1)) * 100
        merged["Margin%_Drop"] = merged["Current_Margin%"] - merged["Previous_Margin%"]

        # Find clients where margin dropped and revenue stable (<10% drop) but cost increased
        margin_drop_clients = merged[
            (merged["Margin%_Drop"] < 0) &
            ((merged["Current_Revenue"] >= 0.9 * merged["Previous_Revenue"]) | (merged["Previous_Revenue"] == 0)) &
            (merged["Current_Cost"] > merged["Previous_Cost"])
        ]["Company_Code"].tolist()

        df_cost_filtered = df_cost[
            (df_cost["Company_Code"].isin(margin_drop_clients)) &
            (df_cost["Month"].isin([latest_month, previous_month]))
        ]

        # Aggregate cost group change per client
        cost_group_changes = []
        for group in group_cols:
            group_cost = (
                df_cost_filtered.groupby(["Company_Code", "Month"])[group]
                .sum()
                .unstack()
                .fillna(0)
                .reset_index()
            )
            group_cost["Change"] = group_cost[latest_month] - group_cost[previous_month]
            group_cost["Cost Group"] = group
            cost_group_changes.append(group_cost[["Company_Code", "Cost Group", "Change"]])

        group_change_df = pd.concat(cost_group_changes).sort_values(by="Change", ascending=False)

        # Show summary
        st.subheader(f"🔍 Margin Drop Analysis - {segment_filter}")
        st.write("Filtered for clients with margin drop caused by cost increase, and stable revenue.")

        st.dataframe(merged[merged["Company_Code"].isin(margin_drop_clients)][[
            "Company_Code", "Previous_Revenue", "Current_Revenue",
            "Previous_Cost", "Current_Cost", "Previous_Margin%", "Current_Margin%", "Margin%_Drop"
        ]].sort_values(by="Margin%_Drop"))

        st.subheader("📊 Cost Increase by Group (Top Contributors)")
        st.dataframe(group_change_df[group_change_df["Change"] > 0])

        # Plotting
        top_contributors = group_change_df[group_change_df["Change"] > 0].groupby("Cost Group")["Change"].sum()
        plt.figure(figsize=(8, 4))
        top_contributors.plot(kind="bar", color="red", edgecolor="black")
        plt.title("Cost Increase by Cost Group")
        plt.ylabel("INR Change")
        plt.xlabel("Cost Group")
        plt.xticks(rotation=0)
        st.pyplot(plt)

    except Exception as e:
        st.error(f"Failed to generate Q2 analysis: {e}")
