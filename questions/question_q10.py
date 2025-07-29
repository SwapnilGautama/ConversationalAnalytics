import pandas as pd
import streamlit as st
import calendar

def run(query):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    try:
        df = pd.read_excel("sample_data/LNTData.xlsx")

        required_fields = ['FresherAgeingCategory', 'Segment', 'Month', 'Year',
                           'TotalBillableHours', 'NetAvailableHours']

        column_map = {
            'DU': 'Delivery_Unit',
            'BU': 'Business_Unit'
        }

        # Rename columns based on q8.py logic
        for standard_col, actual_col in column_map.items():
            if actual_col in df.columns:
                df.rename(columns={actual_col: standard_col}, inplace=True)
                required_fields.append(standard_col)

        # Check all required columns exist
        missing_cols = [col for col in required_fields if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            return

        # Map Year to numeric year
        df['Year'] = df['Year'].astype(str).str.extract(r'(\d{4})').astype(int)

        # Calculate Utilization %
        df["Utilization %"] = (df["TotalBillableHours"] / df["NetAvailableHours"]) * 100
        df = df.replace([float('inf'), float('-inf')], pd.NA).dropna(subset=['Utilization %'])

        # Month mapping (1 → Jan, 2 → Feb, ...)
        df['MonthShort'] = df['Month'].apply(lambda x: calendar.month_abbr[int(x)])
        df['MonthOrder'] = df['Month']

        # Filter only rows with FresherAgeingCategory
        df = df[df['FresherAgeingCategory'].notna()]

        # --- KEY INSIGHTS ---
        st.subheader("📌 Key Insights")

        latest_month = df.sort_values(["Year", "MonthOrder"]).dropna(subset=["Utilization %"]).iloc[-1]
        latest_year = latest_month["Year"]
        latest_month_num = latest_month["MonthOrder"]
        latest_month_name = calendar.month_name[int(latest_month_num)]

        summary = df[(df["Year"] == latest_year) & (df["MonthOrder"] == latest_month_num)]
        category_summary = summary.groupby("FresherAgeingCategory")["Utilization %"].mean().sort_values(ascending=False)

        top_increase = category_summary.dropna().head(3)
        top_decrease = category_summary.dropna().sort_values().head(3)

        
        # --- TABLE ONLY ---
        st.subheader("📋 UT% Table")

        pivot_df = df.pivot_table(index=['Year', 'MonthOrder', 'MonthShort'],
                                  columns='FresherAgeingCategory',
                                  values='Utilization %',
                                  aggfunc='mean').reset_index()

        pivot_df = pivot_df.sort_values(["Year", "MonthOrder"])
        pivot_df.drop(columns="Year", inplace=True)

        # Format and display table as whole number percentages
        numeric_cols = pivot_df.select_dtypes(include='number').columns
        styled_df = pivot_df.drop(columns='MonthOrder').style.format(
            {col: lambda x: f"{int(round(x))}%" if pd.notnull(x) else "" for col in numeric_cols}
        ).set_properties(**{
            'border': '1px solid lightgrey',
            'border-collapse': 'collapse'
        })
        st.dataframe(styled_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error running analysis: {e}")
