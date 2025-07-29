vimport pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns
import calendar

# Set pastel theme
sns.set_palette("pastel")
plt.rcParams["axes.edgecolor"] = "lightgrey"

def run():
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

        required_fields += list(column_map.keys())
        missing = [col for col in required_fields if col not in df.columns]

        if missing:
            st.error(f"Missing required columns: {', '.join(missing)}")
            return

        # Convert Year like "2024-25" → 2024
        df['Year'] = df['Year'].astype(str).str[:4].astype(int)

        # Calculate Utilization %
        df = df[df['NetAvailableHours'] != 0]  # avoid division by zero
        df['Utilization %'] = df['TotalBillableHours'] / df['NetAvailableHours'] * 100

        # Map numeric months to short names
        df['Month'] = df['Month'].astype(int)
        df['MonthName'] = df['Month'].apply(lambda x: calendar.month_abbr[x])

        # Group and pivot
        agg = df.groupby(['MonthName', 'FresherAgeingCategory'])['Utilization %'].mean().reset_index()
        pivot = agg.pivot(index='MonthName', columns='FresherAgeingCategory', values='Utilization %')
        pivot = pivot[calendar.month_abbr[1:13]] if set(pivot.index) >= set(calendar.month_abbr[1:13]) else pivot
        pivot = pivot.round(2)

        # Insights (summary)
        st.markdown("### 🔍 Insights")
        trend_summary = pivot.mean().sort_values(ascending=False).to_frame(name='Avg UT%')
        st.dataframe(trend_summary.style.format("{:.2f}"))

        # Layout
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### 📋 UT% by Month and Bucket")
            st.dataframe(pivot.style.format("{:.2f}").set_table_styles([
                {'selector': 'th', 'props': [('border', '1px solid lightgrey')]},
                {'selector': 'td', 'props': [('border', '1px solid lightgrey')]}
            ]))

        with col2:
            st.markdown("### 📈 UT% Trend Line Chart")
            plt.figure(figsize=(8, 4))
            for cat in pivot.columns:
                plt.plot(pivot.index, pivot[cat], label=cat)
            plt.xlabel("Month")
            plt.ylabel("Utilization %")
            plt.title("Fresher UT% Trends")
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.legend()
            st.pyplot(plt)

        st.success("✅ Analysis complete.")

    except Exception as e:
        st.error(f"Error running analysis: {e}")
