import pandas as pd

def revenue_aggregated(df_pnl: pd.DataFrame) -> pd.DataFrame:
    # Filter for valid revenue Group1 categories
    valid_groups = ["ONSITE", "OFFSHORE", "INDIRECT REVENUE"]
    df_filtered = df_pnl[
        (df_pnl["Group1"].isin(valid_groups)) &
        (df_pnl["Type"].str.upper() == "REVENUE")
    ].copy()

    # Create Month and Year columns from the 'Month' field (string like 'Jun 2025')
    df_filtered["Month"] = pd.to_datetime(df_filtered["Month"], format="%b %Y")
    df_filtered["Month_Num"] = df_filtered["Month"].dt.month
    df_filtered["Year"] = df_filtered["Month"].dt.year

    # Group and sum revenue
    df_revenue = df_filtered.groupby(
        ["FinalCustomerName", "Segment", "Year", "Month_Num"], as_index=False
    )["Amount in USD"].sum()

    df_revenue.rename(columns={"Amount in USD": "Total_Revenue_USD"}, inplace=True)

    return df_revenue
