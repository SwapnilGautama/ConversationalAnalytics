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

        for standard_col, actual_col in column_map.items():
            if actual_col in df.columns:
                df.rename(columns={actual_col: standard_col}, inplace=True)
                required_fields.append(standard_col)

        missing_cols = [col for col in required_fields if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            return

        df['Year'] = df['Year'].astype(str).str.extract(r'(\d{4})').astype(int)
        df["Utilization %"] = (df["TotalBillableHours"] / df["NetAvailableHours"]) * 100
        df = df.replace([float('inf'), float('-inf')], pd.NA).dropna(subset=['Utilization %'])

        df['MonthShort'] = df['Month'].apply(lambda x: calendar.month_abbr[int(x)])
        df['MonthOrder'] = df['Month']

        df = df[df['FresherAgeingCategory'].notna()]

        # --- Insights ---
        latest_month = df.sort_values(["Year", "MonthOrder"]).dropna(subset=["Utilization %"]).iloc[-1]
        latest_year = latest_month["Year"]
        latest_month_num = latest_month["MonthOrder"]
        latest_month_name = calendar.month_name[int(latest_month_num)]

        summary = df[(df["Year"] == latest_year) & (df["MonthOrder"] == latest_month_num)]
        category_summary = summary.groupby("FresherAgeingCategory")["Utilization %"].mean().sort_values(ascending=False)

        top_increase = category_summary.dropna().head(3)
        top_decrease = category_summary.dropna().sort_values().head(3)

        # --- UT% Table ---
        pivot_ut = df.pivot_table(index=['Year', 'MonthOrder', 'MonthShort'],
                                  columns='FresherAgeingCategory',
                                  values='Utilization %',
                                  aggfunc='mean').reset_index()

        pivot_ut = pivot_ut.sort_values(["Year", "MonthOrder"])
        pivot_ut.drop(columns="Year", inplace=True)

        numeric_cols_ut = pivot_ut.select_dtypes(include='number').columns
        styled_ut = pivot_ut.drop(columns='MonthOrder').style.format(
            {col: lambda x: f"{int(round(x))}%" if pd.notnull(x) else "" for col in numeric_cols_ut}
        ).set_properties(**{
            'border': '1px solid lightgrey',
            'border-collapse': 'collapse'
        })

        st.dataframe(styled_ut, use_container_width=True)

        # --- TotalBillableHours and NetAvailableHours Tables (Side by Side) ---
        col1, col2 = st.columns(2)

        # TotalBillableHours Table
        with col1:
            st.markdown("🔹 **TotalBillableHours**")
            billable_pivot = df.pivot_table(index=['Year', 'MonthOrder', 'MonthShort'],
                                            columns='FresherAgeingCategory',
                                            values='TotalBillableHours',
                                            aggfunc='sum').reset_index()
            billable_pivot = billable_pivot.sort_values(['Year', 'MonthOrder'])
            billable_pivot.drop(columns='Year', inplace=True)
            styled_billable = billable_pivot.drop(columns='MonthOrder').style.format('{:,.0f}').set_properties(
                **{'border': '1px solid lightgrey', 'border-collapse': 'collapse'})
            st.dataframe(styled_billable, use_container_width=True)

        # NetAvailableHours Table
        with col2:
            st.markdown("🔹 **NetAvailableHours**")
            available_pivot = df.pivot_table(index=['Year', 'MonthOrder', 'MonthShort'],
                                             columns='FresherAgeingCategory',
                                             values='NetAvailableHours',
                                             aggfunc='sum').reset_index()
            available_pivot = available_pivot.sort_values(['Year', 'MonthOrder'])
            available_pivot.drop(columns='Year', inplace=True)
            styled_available = available_pivot.drop(columns='MonthOrder').style.format('{:,.0f}').set_properties(
                **{'border': '1px solid lightgrey', 'border-collapse': 'collapse'})
            st.dataframe(styled_available, use_container_width=True)

    except Exception as e:
        st.error(f"Error running analysis: {e}")
