import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

def run(prompt=None):
    st.header("DU-wise Fresher UT% Trend")

    st.markdown("""
    This analysis shows Utilization % trends for freshers by Delivery Unit over months.  
    **Freshers** are defined as those with `FresherAgeingCategory` in:
    - Freshers ET(0-3 Months)
    - Freshers ET(4-6 Months)
    - Freshers PGET (4-6 months)
    - Freshers ET-Premium (4-6 months)
    """)

    @st.cache_data
    def load_data():
        df = pd.read_excel("sample_data/LNTData.xlsx")  # Update if path is different
        df["Date_a"] = pd.to_datetime(df["Date_a"], errors="coerce")
        df["Month"] = df["Date_a"].dt.strftime("%b %Y")
        return df

    df = load_data()

    # Clean category
    df["FresherAgeingCategory"] = df["FresherAgeingCategory"].str.strip()

    # Define fresher buckets
    buckets = {
        "Freshers ET(0-3 Months)",
        "Freshers ET(4-6 Months)",
        "Freshers PGET (4-6 months)",
        "Freshers ET-Premium (4-6 months)"
    }

    df_fresh = df[df["FresherAgeingCategory"].isin(buckets)].copy()
    df_fresh = df_fresh.dropna(subset=["NetAvailableHours", "TotalBillableHours"])

    df_fresh["NetAvailableHours"] = pd.to_numeric(df_fresh["NetAvailableHours"], errors="coerce")
    df_fresh["TotalBillableHours"] = pd.to_numeric(df_fresh["TotalBillableHours"], errors="coerce")
    df_fresh["UT%"] = (df_fresh["TotalBillableHours"] / df_fresh["NetAvailableHours"]) * 100

    # Optional segment filtering
    segments = df_fresh["Segment"].dropna().unique().tolist()
    selected_segment = st.selectbox("Select Segment", ["All"] + segments)
    if selected_segment != "All":
        df_fresh = df_fresh[df_fresh["Segment"] == selected_segment]

    # Group
    df_grouped = df_fresh.groupby(["Month", "FresherAgeingCategory"])["UT%"].mean().reset_index()
    df_pivot = df_grouped.pivot(index="Month", columns="FresherAgeingCategory", values="UT%").sort_index()

    st.subheader("Monthly UT% Table")
    st.dataframe(df_pivot.style.format("{:.1f}").set_properties(**{
        'border': '1px solid lightgrey'
    }), use_container_width=True)

    # Chart
    st.subheader("Monthly UT% Line Chart")

    pastel_palette = sns.color_palette("pastel")
    sns.set(style="whitegrid", palette=pastel_palette)
    plt.figure(figsize=(12, 6))

    for column in df_pivot.columns:
        plt.plot(df_pivot.index, df_pivot[column], label=column, marker="o", linewidth=2)

    plt.xlabel("Month")
    plt.ylabel("Utilization %")
    plt.title("Fresher UT% Trend by Category")
    plt.xticks(rotation=45)
    plt.legend(title="Fresher Category")
    plt.grid(color="lightgrey", linewidth=0.5)
    st.pyplot(plt)
