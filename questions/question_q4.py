import pandas as pd
import streamlit as st

def run(prompt=None):
    # Load data
    @st.cache_data
    def load_data():
        df = pd.read_excel("sample_data/LNTData.xlsx")  # ✅ Correct filename
        df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
        df['Month_Year'] = df['Date_a'].dt.strftime('%b %Y')
        df['Quarter'] = df['Date_a'].dt.to_period("Q").astype(str)  # ✅ Convert Period to string
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

    # DU Table
    st.subheader("Utilization % by DU")
    du_pivot = df_filtered.groupby([group_col, 'Delivery_Unit'])['UT%'].mean().unstack().sort_index()
    st.dataframe(du_pivot.style.format("{:.2f}"))

    # BU Table
    st.subheader("Utilization % by BU")
    bu_pivot = df_filtered.groupby([group_col, 'DeliveryGroup'])['UT%'].mean().unstack().sort_index()
    st.dataframe(bu_pivot.style.format("{:.2f}"))

    # Optional Agent Level Table
    if not agents:
        st.subheader("Agent-Level Summary Table")
        agent_table = df_filtered.groupby(['PSNo', group_col])['UT%'].mean().unstack().sort_index()
        st.dataframe(agent_table.style.format("{:.2f}"))
