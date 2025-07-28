import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

def run(prompt=None):
    st.header("DU-wise Fresher UT% Trend")
    st.markdown(
        "This analysis shows Utilization % trends for freshers by Delivery Unit over months. "
        "**Freshers** are defined as those with `FresherAgeingCategory` in:\n"
        "- Freshers ET(0-3 Months)\n"
        "- Freshers ET(4-6 Months)\n"
        "- Freshers PGET(0-3 Months)\n"
        "- Freshers ETPremium(0-3 Months)"
    )

    # Load data
    @st.cache_data
    def load_data():
        df = pd.read_excel("sample_data/LNTData.xlsx")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Month"] = df["Date"].dt.strftime("%b %Y")
        df["Month"] = pd.Categorical(df["Month"], ordered=True, categories=sorted(df["Month"].dropna().unique(), key=lambda x: pd.to_datetime(x)))
        return df

    df = load_data()

    # Define fresher categories
    fresher_cats = [
        "Freshers ET(0-3 Months)",
        "Freshers ET(4-6 Months)",
        "Freshers PGET(0-3 Months)",
        "Freshers ETPremium(0-3 Months)"
    ]

    # Filter to freshers
    fresher_df = df[df["FresherAgeingCategory"].isin(fresher_cats)].copy()

    # Calculate UT%
    fresher_df["NetAvailableHours"] = pd.to_numeric(fresher_df["NetAvailableHours"], errors="coerce")
    fresher_df["TotalBillableHours"] = pd.to_numeric(fresher_df["TotalBillableHours"], errors="coerce")
    fresher_df["UT%"] = fresher_df["TotalBillableHours"] / fresher_df["NetAvailableHours"] * 100

    # Group by DU and Month
    trend_df = fresher_df.groupby(["Delivery_Unit", "Month"]).agg({"UT%": "mean"}).reset_index()

    if trend_df.empty:
        st.warning("No data available for the selected fresher categories.")
        return

    pivot_df = trend_df.pivot(index="Month", columns="Delivery_Unit", values="UT%")

    # Plotting
    st.subheader("Monthly Fresher UT% by Delivery Unit")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=pivot_df, markers=True, dashes=False)
    ax.set_ylabel("Fresher UT%")
    ax.set_xlabel("Month")
    ax.set_title("Fresher Utilization % Trends by DU")
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)

    # Display table
    st.subheader("Fresher UT% Table")
    st.dataframe(pivot_df.round(2), use_container_width=True)
