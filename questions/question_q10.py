import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import streamlit as st
import os

def run(question: str, chat_history=None):
    # 🟦 Extract year and segment
    year = None
    segment = None
    lower_q = question.lower()
    for y in ['2023', '2024', '2025']:
        if y in lower_q:
            year = int(y)
            break
    segments = ['Transportation', 'Med Tech', 'Plant Engineering', 'Media & Technology', 'Industrial Products']
    for s in segments:
        if s.lower() in lower_q:
            segment = s
            break

    # 📂 Load data
    file_path = os.path.join("sample_data", "LNTData.xlsx")
    df = pd.read_excel(file_path)

    # 🧹 Clean data
    df = df.dropna(subset=['PSNo', 'FresherAgeingCategory', 'Month', 'Year', 'Segment', 'TotalBillableHours', 'NetAvailableHours'])
    df['TotalBillableHours'] = pd.to_numeric(df['TotalBillableHours'], errors='coerce')
    df['NetAvailableHours'] = pd.to_numeric(df['NetAvailableHours'], errors='coerce')
    df = df.dropna(subset=['TotalBillableHours', 'NetAvailableHours'])
    df['Month'] = df['Month'].astype(int)

    # 📆 Month Mapping
    month_map = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
    df['MonthName'] = df['Month'].map(month_map)

    # 🧮 Compute UT%
    df['UT%'] = (df['TotalBillableHours'] / df['NetAvailableHours']) * 100
    df['UT%'] = df['UT%'].round(1)

    # 🧩 Filter by Year and Segment (if provided)
    filters_applied = []
    if year:
        df = df[df['Year'] == year]
        filters_applied.append(f"Year = {year}")
    if segment:
        df = df[df['Segment'].str.lower() == segment.lower()]
        filters_applied.append(f"Segment = {segment}")

    # 🟦 Pivot for UT% table
    ut_pivot = df.pivot_table(index=['MonthName', 'Segment'], columns='FresherAgeingCategory', values='UT%', aggfunc='mean')
    ut_pivot = ut_pivot.reset_index()
    ut_pivot = ut_pivot.sort_values(by='MonthName', key=lambda x: pd.to_datetime(x, format='%b'))

    # 🟨 Insights generation
    insights = []
    categories = df['FresherAgeingCategory'].unique()
    for cat in categories:
        cat_df = df[df['FresherAgeingCategory'] == cat]
        if not cat_df.empty:
            avg_ut = cat_df['UT%'].mean().round(1)
            months_sorted = sorted(cat_df['Month'].unique())
            if len(months_sorted) >= 2:
                start_month = months_sorted[0]
                end_month = months_sorted[-1]
                start_val = cat_df[cat_df['Month'] == start_month]['UT%'].mean()
                end_val = cat_df[cat_df['Month'] == end_month]['UT%'].mean()
                trend = "↑ Increasing" if end_val > start_val else "↓ Decreasing"
                insights.append(f"• {cat}: Avg UT% = {avg_ut}%, Trend = {trend} ({start_val:.1f}% → {end_val:.1f}%)")

    # 📈 Line Chart
    line_df = df.groupby(['MonthName', 'FresherAgeingCategory'])['UT%'].mean().reset_index()
    line_df['MonthNum'] = line_df['MonthName'].map({v: k for k, v in month_map.items()})
    line_df = line_df.sort_values(by='MonthNum')

    fig, ax = plt.subplots(figsize=(10, 5))
    for cat in line_df['FresherAgeingCategory'].unique():
        sub = line_df[line_df['FresherAgeingCategory'] == cat]
        ax.plot(sub['MonthName'], sub['UT%'], label=cat, linewidth=2)

    ax.set_ylabel("UT%")
    ax.set_title("Fresher UT% Trends (Monthly)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # ✅ Output to Streamlit
    st.markdown("## 📊 Fresher UT% Monthly Trends by Bucket")
    if filters_applied:
        st.success(f"✅ Filter Applied: {', '.join(filters_applied)}")

    with st.expander("🔍 Key Insights", expanded=True):
        for ins in insights:
            st.markdown(ins)

    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.markdown("### 🐣 Monthly UT% Table")
        st.dataframe(ut_pivot.style.format("{:.1f}").set_properties(**{
            'border-color': 'lightgrey',
            'border-style': 'solid',
            'border-width': '1px',
        }), use_container_width=True)

    with col2:
        st.markdown("### 📈 UT% Trend by Fresher Category")
        st.pyplot(fig)

