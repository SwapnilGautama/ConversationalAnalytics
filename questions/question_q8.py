import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

def run(prompt=None):  # ✅ Accept the prompt argument
    # Load data
    @st.cache_data
    def load_data():
        df = pd.read_excel("sample_data/LNTData.xlsx")  # ✅ Corrected filename
        df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
        df['Month_Year'] = df['Date_a'].dt.strftime('%b %Y')
        df['Quarter'] = df['Date_a'].dt.to_period("Q")
        df['Year'] = df['Date_a'].dt.year
        df['NetAvailableHours'] = pd.to_numeric(df['NetAvailableHours'], errors='coerce')
        df['TotalBillableHours'] = pd.to_numeric(df['TotalBillableHours'], errors='coerce')
        df['UT%'] = (df['TotalBillableHours'] / df['NetAvailableHours']) * 100
        return df

    df = load_data()

    # Sidebar filters
    st.sidebar.header("Filters")
    time_view = st.sidebar.radio("Select Trend Type:", ["Month", "Quarter", "Year"])
    segments = st.sidebar.multiselect("Select Segment(s):", df['Segment'].dropna().unique(), default=None)
    bus = st.sidebar.multiselect("Select BU(s):", df['DeliveryGroup'].dropna().unique(), default=None)
    dus = st.sidebar.multiselect("Select DU(s):", df['Delivery_Unit'].dropna().unique(), default=None)
    agents = st.sidebar.multiselect("Select Agent(s):", df['PSNo'].dropna().unique(), default=None)

    # Filter data
    df_filtered = df.copy()
    if segments:
        df_filtered = df_filtered[df_filtered['Segment'].isin(segments)]
    if bus:
        df_filtered = df_filtered[df_filtered['DeliveryGroup'].isin(bus)]
    if dus:
        df_filtered = df_filtered[df_filtered['Delivery_Unit'].isin(dus)]
    if agents:
        df_filtered = df_filtered[df_filtered['PSNo'].isin(agents)]

    # Grouping by time dimension
    if time_view == "Month":
        group_col = "Month_Year"
    elif time_view == "Quarter":
        group_col = "Quarter"
    else:
        group_col = "Year"

    def draw_line_chart(pivot_df, title):
        fig, ax = plt.subplots(figsize=(8, 3))
        for col in pivot_df.columns:
            ax.plot(pivot_df.index, pivot_df[col], label=col, linewidth=1.5)
        ax.set_title(title, fontsize=12)
        ax.set_ylabel("UT %")
        ax.set_xlabel(group_col)
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.45), ncol=3, fontsize=8)
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('lightgrey')
        ax.spines['bottom'].set_color('lightgrey')
        st.pyplot(fig)

    # DU Table and Chart
    st.subheader("Utilization % by DU")
    du_pivot = df_filtered.groupby([group_col, 'Delivery_Unit'])['UT%'].mean().unstack().sort_index()
    st.dataframe(du_pivot.style.format("{:.2f}"))
    draw_line_chart(du_pivot, "DU-wise UT% Trend")

    # BU Table and Chart
    st.subheader("Utilization % by BU")
    bu_pivot = df_filtered.groupby([group_col, 'DeliveryGroup'])['UT%'].mean().unstack().sort_index()
    st.dataframe(bu_pivot.style.format("{:.2f}"))
    draw_line_chart(bu_pivot, "BU-wise UT% Trend")

    # Optional Agent Level View
    if not agents:
        st.subheader("Agent-Level Summary Table")
        agent_table = df_filtered.groupby(['PSNo', group_col])['UT%'].mean().unstack().sort_index()
        st.dataframe(agent_table.style.format("{:.2f}"))
