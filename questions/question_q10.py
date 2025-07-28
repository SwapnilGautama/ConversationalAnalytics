import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run(prompt: str):
    st.subheader("📊 Fresher UT% Monthly Trends by Bucket")

    @st.cache_data
    def load_data():
        df = pd.read_excel("sample_data/LNTData.xlsx")
        return df

    df = load_data()

    # ✅ Convert Year field like '2024-25' -> 2024
    df['Year_clean'] = df['Year'].astype(str).str[:4].astype(int)
    df['Month_Name'] = df['Month'].map({1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
                                        7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'})

    # ✅ Extract year from user prompt
    if '2025' in prompt:
        selected_year = 2025
    elif '2024' in prompt:
        selected_year = 2024
    else:
        selected_year = df['Year_clean'].max()

    # ✅ Extract segment from prompt (if mentioned)
    segments = df['Segment'].dropna().unique().tolist()
    selected_segment = None
    for seg in segments:
        if seg.lower() in prompt.lower():
            selected_segment = seg
            break

    # ✅ Filter only Billable + selected year + segment (if any)
    df = df[df['Status'].astype(str).str.lower() == 'billable']
    df = df[df['Year_clean'] == selected_year]
    if selected_segment:
        df = df[df['Segment'] == selected_segment]

    if df.empty:
        st.warning("No data available for selected filters.")
        return

    # ✅ Pivot table for visualization and tabulation
    pivot_df = df.pivot_table(
        index=['Month_Name', 'Segment'],
        columns='FresherAgeingCategory',
        values='Utilization %',
        aggfunc='mean'
    ).sort_index()

    # ✅ Insights (2 points)
    st.markdown("### 🔍 Key Insights")
    latest_month = df['Month'].max()
    latest_month_name = df[df['Month'] == latest_month]['Month_Name'].iloc[0]
    latest_summary = df[df['Month'] == latest_month].groupby('FresherAgeingCategory')['Utilization %'].mean()

    insight1 = f"1. In **{latest_month_name} {selected_year}**, highest fresher utilization was in **{latest_summary.idxmax()}** at **{latest_summary.max():.1f}%**."
    trend = df.groupby('FresherAgeingCategory')['Utilization %'].mean().sort_values(ascending=False)
    insight2 = f"2. On average during the year, **{trend.idxmax()}** had the best UT% at **{trend.max():.1f}%**."

    st.markdown(insight1)
    st.markdown(insight2)

    # ✅ Table (left) and Chart (right)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📋 UT% Table")
        styled_table = pivot_df.style.format("{:.1f}%").set_table_styles(
            [{'selector': 'td', 'props': [('border', '1px solid lightgrey')]},
             {'selector': 'th', 'props': [('border', '1px solid lightgrey'), ('background-color', '#f9f9f9')]}]
        )
        st.dataframe(styled_table, use_container_width=True)

    with col2:
        st.markdown("### 📈 Monthly Trend Chart")
        line_data = df.groupby(['Month_Name', 'FresherAgeingCategory'])['Utilization %'].mean().reset_index()
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        line_data['Month_Name'] = pd.Categorical(line_data['Month_Name'], categories=month_order, ordered=True)
        line_data.sort_values('Month_Name', inplace=True)

        fig, ax = plt.subplots(figsize=(6, 3.5))
        sns.lineplot(data=line_data, x='Month_Name', y='Utilization %', hue='FresherAgeingCategory', linewidth=2, palette='pastel')
        ax.set_ylabel("UT %")
        ax.set_xlabel("Month")
        ax.set_title("Fresher UT% by Month")
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('lightgrey')
        ax.spines['bottom'].set_color('lightgrey')
        ax.legend(title='Fresher Category', loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=2)
        st.pyplot(fig)
