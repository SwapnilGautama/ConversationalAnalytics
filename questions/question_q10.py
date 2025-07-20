import pandas as pd

def answer_question_q10(ut_df: pd.DataFrame, entity_name: str) -> dict:
    """
    Computes UT% trend for the last 2 quarters for a DU/BU/account.

    Parameters:
    - ut_df (pd.DataFrame): Utilization dataset
    - entity_name (str): DU or BU or Account name (matches with one of: Delivery_Unit, Business_Unit, Final Customer Name)

    Returns:
    - dict: Contains summary, trend table, and chart data
    """
    # Standardize date format
    ut_df["Month"] = pd.to_datetime(ut_df["Month"])
    ut_df["MonthStr"] = ut_df["Month"].dt.strftime("%b-%Y")

    # Try matching by DU, then BU, then Account
    if entity_name in ut_df["Delivery_Unit"].unique():
        filtered = ut_df[ut_df["Delivery_Unit"] == entity_name].copy()
        entity_type = "Delivery Unit"
    elif entity_name in ut_df["Business_Unit"].unique():
        filtered = ut_df[ut_df["Business_Unit"] == entity_name].copy()
        entity_type = "Business Unit"
    elif entity_name.lower() in ut_df["Final Customer Name"].str.lower().unique():
        filtered = ut_df[ut_df["Final Customer Name"].str.lower() == entity_name.lower()].copy()
        entity_type = "Account"
    else:
        return {
            "answer": f"'{entity_name}' not found in Delivery Unit, Business Unit, or Account columns.",
            "table": pd.DataFrame(),
            "chart": None
        }

    # Keep only last 6 months (2 quarters)
    recent_months = sorted(filtered["Month"].unique())[-6:]
    filtered = filtered[filtered["Month"].isin(recent_months)]

    if filtered.empty:
        return {
            "answer": f"No recent UT% data available for {entity_type} '{entity_name}'.",
            "table": pd.DataFrame(),
            "chart": None
        }

    # Compute UT%
    grouped = (
        filtered.groupby("MonthStr")
        .agg({"Billed HC": "sum", "HC": "sum"})
        .reset_index()
    )
    grouped["UT%"] = ((grouped["Billed HC"] / grouped["HC"]) * 100).round(2)

    latest_month = grouped["MonthStr"].iloc[-1]
    latest_ut = grouped["UT%"].iloc[-1]

    summary = f"UT% for {entity_type} '{entity_name}' in {latest_month} was {latest_ut}%."

    return {
        "answer": summary,
        "table": grouped[["MonthStr", "Billed HC", "HC", "UT%"]],
        "chart": {
            "type": "line",
            "x": grouped["MonthStr"].tolist(),
            "y": grouped["UT%"].tolist(),
            "title": f"UT% Trend for {entity_name}"
        }
    }
