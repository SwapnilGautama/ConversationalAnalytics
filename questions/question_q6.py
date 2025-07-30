import pandas as pd

def calculate_realized_rate(df_pnl: pd.DataFrame, df_ut: pd.DataFrame) -> pd.DataFrame:
    # Ensure proper datetime format
    df_pnl["Month"] = pd.to_datetime(df_pnl["Month"], errors='coerce')
    df_ut["Month"] = pd.to_datetime(df_ut["Month"], errors='coerce')

    # Drop rows with missing join keys
    df_pnl.dropna(subset=["FinalCustomerName", "Month"], inplace=True)
    df_ut.dropna(subset=["FinalCustomerName", "Month"], inplace=True)

    # Apply revenue filters
    df_pnl_filtered = df_pnl[
        (df_pnl["Group1"].str.upper().isin(["ONSITE", "OFFSHORE", "INDIRECT REVENUE"])) &
        (df_pnl["Type"].str.lower() == "revenue")
    ]

    # Sum revenue
    revenue_df = (
        df_pnl_filtered
        .groupby(["FinalCustomerName", "Month"], as_index=False)
        .agg({"Amount in USD": "sum"})
        .rename(columns={"Amount in USD": "Revenue"})
    )

    # Sum available hours
    ut_df = (
        df_ut
        .groupby(["FinalCustomerName", "Month"], as_index=False)
        .agg({"NetAvailableHours": "sum"})
        .rename(columns={"NetAvailableHours": "AvailableHours"})
    )

    # Merge and calculate
    merged = pd.merge(revenue_df, ut_df, on=["FinalCustomerName", "Month"], how="inner")
    merged = merged[merged["AvailableHours"] != 0]
    merged["Realized_Rate"] = merged["Revenue"] / merged["AvailableHours"]

    return merged
