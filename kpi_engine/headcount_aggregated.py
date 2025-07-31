import pandas as pd

def headcount_aggregated(df_ut: pd.DataFrame) -> pd.DataFrame:
    df = df_ut.copy()

    # Convert Date_a to datetime
    df["Date_a"] = pd.to_datetime(df["Date_a"], dayfirst=True, errors='coerce')
    df.dropna(subset=["Date_a"], inplace=True)

    df["Month_Num"] = df["Date_a"].dt.month
    df["Year"] = df["Date_a"].dt.year

    # Group and count distinct PSNo
    df_hc = df.groupby(
        ["FinalCustomerName", "Segment", "Year", "Month_Num"], as_index=False
    )["PSNo"].nunique()

    df_hc.rename(columns={"PSNo": "Distinct_Headcount"}, inplace=True)

    return df_hc
