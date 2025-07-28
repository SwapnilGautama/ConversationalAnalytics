import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_option('deprecation.showPyplotGlobalUse', False)

def run(user_query):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

    # Load data
    df = pd.read_excel("sample_data/LNTData.xlsx")
    df = df[df['Status'] == 'Billable']
    df = df.dropna(subset=['FresherAgeingCategory'])

    # Convert 'Month' column (int) to month names
    month_map = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    df['MonthName'] = df['Month'].map(month_map)

    # Handle segment filtering via chatbot
    if "Segment" in df.columns:
        possible_segments = df["Segment"].dropna().unique().tolist()
        selected_segment = None
        for seg in possible_segments:
            try:
                if isinstance(seg, str) and seg.lower() in user_query.lower():
                    selected_segment = seg
                    break
            except Exception:
                continue
        if selected_segment:
            df = df[df["Segment"] == selected_segment]

    # Handle year filtering via chatbot
    if "Year" in df.columns:
        year_mapping = {"2024": "2024-25", "2025": "2025-26"}
        for year in year_mapping:
            if year in user_query:
                df = df[df["Year"] == year_mapping[year]]
                break

    # Aggregate UT% by MonthName and FresherAgeingCategory
    df_summary = df.groupby(['MonthName', 'FresherAgeingCategory'])['Utilization %'].mean().unstack().fillna(0)
    df_summary = df_summary.loc[month_map.values()]  # Reorder by month

    # Key Insights - top 2 movers
    movement_summary = []
    for col in df_summary.columns:
        values = df_summary[col].values
        if len(values) < 2:
            continue
        start = values[0]
        end = values[-1]
        avg_ut = values.mean()
        trend = "↑ Increasing" if end > start else "↓ Decreasing"
        movement_summary.append({
            "bucket": col,
            "avg": round(avg_ut, 1),
            "start": round(start, 1),
            "end": round(end, 1),
            "trend": trend,
            "diff": abs(end - start)
        })

    movement_summary = sorted(movement_summary, key=lambda x: x["diff"], reverse=True)[:2]
    st.subheader("🔍 Key Insights")
    for item in movement_summary:
        st.markdown(f"**{item['bucket']}**: Avg UT% = {item['avg']}%, Trend = {item['trend']} ({item['start']}% → {item['end']}%)")

    # Display table
    st.subheader("🤸 Monthly UT% Table")
    st.dataframe(df_summary.style.format("{:.1f}%").set_table_styles([{
        'selector': 'th, td', 'props': [('border', '1px solid lightgrey')]
    }]), use_container_width=True)

    # Line chart
    st.subheader("🌐 UT% Trend by Fresher Category")
    fig, ax = plt.subplots(figsize=(10, 4))
    for col in df_summary.columns:
        ax.plot(df_summary.index, df_summary[col], label=col)
    ax.set_ylabel("UT%")
    ax.set_title("Fresher UT% Trends (Monthly)")
    ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    st.pyplot(fig)
