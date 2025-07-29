import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

def run(segment=None, year=None):
    # Load data
    df = pd.read_excel("sample_data/LNTData.xlsx")

    # Ensure required fields exist
    required_fields = ['Month', 'Year', 'FresherAgeingCategory', 'Status', 'PSNo', 'NetAvailableHours', 'TotalBillableHours', 'Segment', 'DeliveryGroup', 'Delivery_Unit']
    missing_fields = [col for col in required_fields if col not in df.columns]
    if missing_fields:
        st.error(f"Missing required columns: {', '.join(missing_fields)}")
        return

    # Filters applied
    filters_applied = []

    if year:
        df = df[df['Year'] == year]
        filters_applied.append(f"Year = {year}")

    if segment and isinstance(segment, str):
        df = df[df['Segment'].astype(str).str.lower() == segment.lower()]
        filters_applied.append(f"Segment = {segment}")

    # Filter to only Billable
    df = df[df['Status'] == 'Billable']

    # Drop NA Fresher categories
    df = df.dropna(subset=['FresherAgeingCategory'])

    # Calculate UT%
    df['Utilization %'] = df['TotalBillableHours'] / df['NetAvailableHours'] * 100

    # Aggregate UT% by Month and Category
    trend = df.groupby(['Month', 'FresherAgeingCategory'])['Utilization %'].mean().reset_index()

    # Month mapping
    month_map = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    trend['MonthName'] = trend['Month'].map(month_map)

    # Pivot for table
    table = trend.pivot(index='MonthName', columns='FresherAgeingCategory', values='Utilization %')
    table = table.reindex(list(month_map.values()))  # Ensure correct order

    # Display applied filters
    if filters_applied:
        with st.container():
            st.markdown("🧭 **Filter Applied**")
            st.write(", ".join(filters_applied))

    # Title
    st.markdown("## 📊 Fresher UT% Monthly Trends by Bucket")

    # Summary
    latest_month = trend['Month'].max()
    latest_data = trend[trend['Month'] == latest_month]
    summary_lines = []
    for cat in latest_data['FresherAgeingCategory'].unique():
        val = latest_data[latest_data['FresherAgeingCategory'] == cat]['Utilization %'].mean()
        summary_lines.append(f"- **{cat}** had a UT% of **{val:.1f}%** in {month_map[latest_month]}")
    st.markdown("### 🔍 Insights")
    st.markdown("\n".join(summary_lines))

    # Side-by-side layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📋 UT% Table")
        st.dataframe(table.style.format("{:.1f}").set_table_styles([
            {"selector": "th", "props": [("border", "1px solid lightgrey")]},
            {"selector": "td", "props": [("border", "1px solid lightgrey")]}
        ]), use_container_width=True)

    with col2:
        st.markdown("#### 📈 UT% Trend Chart")
        plt.figure(figsize=(8, 4))
        sns.lineplot(data=trend, x='MonthName', y='Utilization %', hue='FresherAgeingCategory', marker='o')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', linewidth=0.5)
        plt.tight_layout()
        st.pyplot(plt.gcf())
        plt.clf()
