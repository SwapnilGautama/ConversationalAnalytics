import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns
import calendar
import difflib

# Set pastel theme
sns.set_palette("pastel")
plt.rcParams["axes.edgecolor"] = "lightgrey"

def run(query):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    try:
        df = pd.read_excel("sample_data/LNTData.xlsx")

        # Show available columns (for debug or dynamic detection)
        actual_cols = df.columns.tolist()

        # Fuzzy find BU and DU using close matches
        bu_col = difflib.get_close_matches('Business_Unit', actual_cols, n=1, cutoff=0.6)
        du_col = difflib.get_close_matches('Delivery_Unit', actual_cols, n=1, cutoff=0.6)

        # Rename dynamically
        if bu_col:
            df.rename(columns={bu_col[0]: 'BU'}, inplace=True)
        if du_col:
            df.rename(columns={du_col[0]: 'DU'}, inplace=True)

        # Check required fields after renaming
        required_cols = ['FresherAgeingCategory', 'Segment', 'BU', 'DU', 'Month', 'Year', 'TotalBillableHours', 'NetAvailableHours']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            return

        # Derive Utilization %
        df['Utilization %'] = (df['TotalBillableHours'] / df['NetAvailableHours']) * 100
        df['Utilization %'] = df['Utilization %'].round(2)

        # Convert Month to short names
        df['MonthName'] = df['Month'].apply(lambda x: calendar.month_abbr[int(x)] if pd.notnull(x) else x)

        # Clean Year
        df['Year'] = df['Year'].astype(str).str[:4].astype(int)

        # Group and Pivot
        agg_df = df.groupby(['FresherAgeingCategory', 'Segment', 'BU', 'DU', 'Year', 'MonthName'])['Utilization %'].mean().reset_index()

        pivot_df = agg_df.pivot_table(
            index=['Year', 'MonthName'],
            columns='FresherAgeingCategory',
            values='Utilization %',
            aggfunc='mean'
        ).reset_index()

        # Sort by proper month order
        month_order = list(calendar.month_abbr)[1:]
        pivot_df['MonthOrder'] = pd.Categorical(pivot_df['MonthName'], categories=month_order, ordered=True)
        pivot_df = pivot_df.sort_values(['Year', 'MonthOrder'])

        # Display summary
        st.subheader("📌 Key Insights")
        if not pivot_df.empty:
            latest_month = pivot_df.iloc[-1]
            insights = [f"{col}: {latest_month[col]:.1f}%" for col in pivot_df.columns if col not in ['Year', 'MonthName', 'MonthOrder']]
            insight_text = f"In {latest_month['MonthName']} {latest_month['Year']}, UT% by category: " + ", ".join(insights)
            st.markdown(insight_text)
        else:
            st.warning("No data to generate insights.")

        # Layout visuals
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📋 UT% Table")
            st.dataframe(
                pivot_df.drop(columns='MonthOrder').style.format("{:.1f}").set_properties(**{
                    'border': '1px solid lightgrey',
                    'border-collapse': 'collapse'
                }),
                use_container_width=True
            )

        with col2:
            st.subheader("📈 UT% Trend Chart")
            fig, ax = plt.subplots(figsize=(6, 4))
            for col in pivot_df.columns[2:-1]:  # skip Year, MonthName, MonthOrder
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
