# ✅ Rebuilt headcount_aggregated.py using exact q7.py logic

import pandas as pd

def compute_headcount(df):
    df = df.copy()

    # Clean and standardize fields
    df['Segment'] = df.get('Segment', 'Unknown')
    df['BU'] = df.get('Exec DG', 'Unknown')
    df['DU'] = df.get('Exec DU', 'Unknown')
    df['PSNo'] = df.get('PSNo', 'Unknown')
    df['Month'] = pd.to_datetime(df['date_a'], errors='coerce').dt.to_period("M")

    # Drop duplicates at Month + PSNo level — ensures unique people per month
    df_unique = df.drop_duplicates(subset=["Month", "PSNo"])

    # Group and count unique PSNo
    grouped = (
        df_unique.groupby(["Segment", "BU", "DU", "Month"])["PSNo"]
        .nunique()
        .reset_index(name="Headcount")
    )

    # Pivot: show months as columns
    pivot = grouped.pivot_table(
        index=["Segment", "BU", "DU"],
        columns="Month",
        values="Headcount",
        fill_value=0
    )

    # Sort columns in chronological order
    pivot = pivot.sort_index(axis=1)

    # Reset index and clean up column names
    pivot = pivot.reset_index()
    pivot.columns.name = None

    return pivot
