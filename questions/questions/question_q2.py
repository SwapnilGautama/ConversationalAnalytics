import pandas as pd

def identify_margin_drop_costs(pnl_df: pd.DataFrame) -> dict:
    """
    Identify which cost in the 'Transportation' segment contributed most to margin drop
    comparing Jun'25 vs May'25.
    """
    # Filter for Transportation + Cost rows
    df_filtered = pnl_df[
        (pnl_df["Segment"] == "Transportation") &
        (pnl_df["Type"] == "Cost") &
        (pnl_df["Month"].isin(["May-25", "Jun-25"]))
    ]

    # Group and pivot
    grouped = df_filtered.groupby(["Group Description", "Month"])["Amount in USD"].sum().unstack(fill_value=0)

    grouped["Change"] = grouped["Jun-25"] - grouped["May-25"]
    grouped = grouped.sort_values(by="Change", ascending=False)

    # Prepare summary
    top_increase = grouped.head(3).reset_index()
    summary = f"In the Transportation segment, the cost groups with the highest increases in Jun'25 vs May'25 are:"
    
    top_groups = []
    for _, row in top_increase.iterrows():
        top_groups.append(f"- {row['Group Description']}: ${row['Change']:,.0f} increase")

    return {
        "summary": summary + "\n" + "\n".join(top_groups),
        "table": grouped.reset_index(),
        "chart": {
            "x": grouped.index.tolist(),
            "y": grouped["Change"].tolist(),
            "title": "Cost Increase by Group (Jun'25 vs May'25)",
            "xlabel": "Group Description",
            "ylabel": "Change in USD"
        }
    }
