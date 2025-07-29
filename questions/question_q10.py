import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

def run(prompt=None):
    st.title("📊 Fresher UT% Monthly Trends by Bucket")

    # Load data
    @st.cache_data
    def load_data():
        df = pd.read_excel("sample_data/LNTData.xlsx")
        df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
        df['NetAvailableHours'] = pd.to_numeric(df['NetAvailableHours'], errors='coerce')
        df['TotalBillableHours'] = pd.to_numeric(df['TotalBillableHours'], errors='coerce')
        df['UT%'] = (df['TotalBillableHours'] / df['NetAvailableHours']) * 100
        df['MonthName'] = df['Month'].map({1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                                           7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'})
        return df

    df = load_data()

    # Apply year filter from prompt if available
    selected_year = None
    if prompt:
        for yr in [2023, 2024, 2025, 2026]:
            if str(yr) in prompt:
                selected_year = yr
                break
    if selected_year:
        df = df[df['Year'] == selected_year]

    # Check required columns
    required_cols = ['FresherAgeingCategory', 'Segment', 'Month', 'MonthName', 'UT%', 'DeliveryGroup', 'Delivery_Unit']
    missing = [col for col in required_cols if col not in df.columns]
    if len(missing) > 0:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return

    # Group and pivot for table
    table_df = df.groupby(['MonthName', 'FresherAgeingCategory', 'Segment'])['UT%'].mean().reset_index()
    pivot_table = table_df.pivot_table(index='MonthName', columns=['FresherAgeingCategory', 'Segment'], values='UT%')

    # Plot line chart
    line_df = df.groupby(['MonthName', 'FresherAgeingCategory'])['UT%'].mean().reset_index()
    pivot_line = line_df.pivot(index='MonthName', columns='FresherAgeingCategory', values='UT%')
    pivot_line = pivot_line.reindex(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])

    pastel_palette = sns.color_palette("pastel")

    fig, ax = plt.subplots(figsize=(10, 4))
    for idx, column in enumerate(pivot_line.columns):
        ax.plot(pivot_line.index, pivot_line[column], label=column, linewidth=2, color=pastel_palette[idx % len(pastel_palette)])
    ax.set_title("UT% Trend by Fresher Bucket")
    ax.set_ylabel("UT %")
    ax.set_xlabel("Month")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_facecolor('white')
    for spine in ax.spines.values():
        spine.set_edgecolor('lightgrey')
    ax.legend()
    st.pyplot(fig)

    # Show table
    st.subheader("📋 UT% Table by Month × Fresher Category × Segment")
    st.dataframe(pivot_table.style.format("{:.2f}").set_properties(**{
        'border-color': 'lightgrey',
        'border-style': 'solid',
        'border-width': '0.5px'
    }))
