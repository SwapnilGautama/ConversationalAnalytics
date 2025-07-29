import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns
import calendar

# Set pastel theme
sns.set_palette("pastel")
plt.rcParams["axes.edgecolor"] = "lightgrey"

def run(query):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    try:
        df = pd.read_excel("sample_data/LNTData.xlsx")

        # Rename BU and DU as per q8.py
        column_map = {
            'DU': 'Delivery_Unit',
            'BU': 'Business_Unit'
        }
        for std_col, actual_col in column_map.items():
            if actual_col in df.columns:
                df.rename(columns={actual_col: std_col}, inplace=True)

        # Ensure required fields exist
        required_cols = ['FresherAgeingCategory', 'Segment', 'BU', 'DU', 'Month', 'Year', 'TotalBillableHours', 'NetAvailableHours']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            return

        # Derive Utilization %
        df['Utilization %'] = (df['TotalBillableHours'] / df['NetAvailableHours']) * 100
        df['Utilization %'] = df['Utilization %'].round(2)

        # Map month numbers to short names
        df['MonthName'] = df['Month'].apply(lambda x: calendar.month_abbr[int(x)] if pd.notnull(x) else x)

        # Clean Year
        df['Year'] = df['Year'].astype(str).str[:4].astype(int)

        # Group and Pivot
        agg_df = df.groupby(['FresherAgeingCategory', 'Segment', 'BU', 'DU', 'Year', 'MonthName'])['Utilization %'].mean().reset_index()

        # Prepare pivot for table
        pivot_df = agg_df.pivot_table(
            index=['Year', 'MonthName'],
            columns='FresherAgeingCategory',
            values='Utilization %',
            aggfunc='mean'
        ).reset_index()

        # Sort months correctly
        month_order = list(calendar.month_abbr)[1:]
        pivot_df['MonthOrder'] = pd.Categorical(pivot_df['MonthName'], categories=month_order, ordered=True)
        pivot_df = pivot_df.sort_values(['Year', 'MonthOrder'])

        # Display insights
        st.subheader("📌 Key Insights")
        recent_month = pivot_df['MonthName'].iloc[-1]
        insight = f"Fresher UT% trends show variations across aging buckets. For example, in {recent_month}, "
        top_cols = pivot_df.columns[2:-1]
        sample_trends = [f"{col}: {pivot_df[col].iloc[-1]:.1f}%" for col in top_cols]
        insight += ", ".join(sample_trends) + "."
        st.markdown(insight)

        # Display visuals
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📋 UT% Table")
            table_display = pivot_df.drop(columns='MonthOrder')
            st.dataframe(table_display.style.format("{:.1f}").set_properties(**{
                'border': '1px solid lightgrey',
                'border-collapse': 'collapse'
            }), use_container_width=True)

        with col2:
            st.subheader("📈 UT% Trend Chart")
            fig, ax = plt.subplots(figsize=(6, 4))
            for col in top_cols:
                ax.plot(pivot_df['MonthName'], pivot_df[col], label=col, linewidth=2)
            ax.set_ylabel("Utilization %")
            ax.set_xlabel("Month")
            ax.set_title("Fresher UT% Trend by Category")
            ax.legend(title="Fresher Category", bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, linestyle='--', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)

    except Exception as e:
        st.error(f"⚠️ Error running analysis: {str(e)}")
