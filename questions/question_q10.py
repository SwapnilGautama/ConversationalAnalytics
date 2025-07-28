import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from kpi_engine.utilization import load_ut_data

# Setup
st.subheader("Fresher UT% Monthly Trends by Bucket")

# Optional year input from prompt or default to "2025-26"
year_input = st.text_input("Enter Year (2024-25 or 2025-26):", "2025-26")
valid_years = {"2024-25": "2024", "2025-26": "2025"}
year_filter = valid_years.get(year_input.strip(), "2025")

# Load UT data
df = load_ut_data()

# Ensure clean column names
df.columns = df.columns.str.strip()

# Map month numbers to names
month_map = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}

# Filter data for selected year and Billable freshers
fresher_categories = [
    "Freshers ET(0-3 Months)",
    "Freshers ET(4-6 Months)",
    "Freshers PGET(0-3 Months)",
    "Freshers ETPremium(0-3 Months)"
]
df = df[(df['FresherAgeingCategory'].isin(fresher_categories)) &
        (df['Status'] == 'Billable') &
        (df['Year'] == year_filter)]

# Group and prepare data
df_grouped = df.groupby(['Month', 'FresherAgeingCategory'])['UT%'].mean().reset_index()
df_grouped['MonthName'] = df_grouped['Month'].map(month_map)
df_grouped = df_grouped.sort_values(by='Month')
df_pivot = df_grouped.pivot(index='MonthName', columns='FresherAgeingCategory', values='UT%')

# --- Insights Section --- #
st.markdown("""
### 🔍 Key Insights
""")
insights = []
for cat in fresher_categories:
    trend = df_grouped[df_grouped['FresherAgeingCategory'] == cat].sort_values("Month")
    if len(trend) >= 2:
        diff = trend["UT%"].iloc[-1] - trend["UT%"].iloc[0]
        direction = "increased" if diff > 0 else "decreased"
        insights.append(f"- {cat} UT% has {direction} by {abs(diff):.1f}% from {month_map[trend['Month'].iloc[0]]} to {month_map[trend['Month'].iloc[-1]]}.")
if insights:
    st.markdown("\n".join(insights))
else:
    st.info("Not enough data to generate insights.")

# --- Side-by-Side Table and Chart --- #
st.markdown("""
### 🏋️ Monthly UT% Table
""")
col1, col2 = st.columns(2)
with col1:
    st.dataframe(df_pivot.style.set_table_styles([
        {'selector': 'td', 'props': [('border', '1px solid lightgrey')]},
        {'selector': 'th', 'props': [('border', '1px solid lightgrey')]}
    ]), height=400)

with col2:
    st.markdown("""
    ### 🌀 UT% Trend by Fresher Category
    """)
    pastel_colors = sns.color_palette("pastel")
    plt.figure(figsize=(7, 4))
    for i, cat in enumerate(df_pivot.columns):
        plt.plot(df_pivot.index, df_pivot[cat], label=cat, linewidth=2, linestyle='-', marker='o', color=pastel_colors[i % len(pastel_colors)])
    plt.title("Fresher UT% Trends (Monthly)")
    plt.xlabel("Month")
    plt.ylabel("UT%")
    plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    plt.legend(loc='upper right', fontsize=8)
    plt.tight_layout()
    st.pyplot(plt)
