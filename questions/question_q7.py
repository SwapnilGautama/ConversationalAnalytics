# question_q7.py

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def compute_fte(total_hours):
    # Convert total billable hours to FTE (8 hours/day * 21 working days)
    return total_hours / (8 * 21)

def run(df, user_question):
    # Load the correct dataset
    df = pd.read_excel("sample_data/LNTData.xlsx")

    # Convert date to proper datetime
    df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')

    # Drop rows with missing data in key columns
    df = df.dropna(subset=['Date_a', 'FinalCustomerName', 'TotalBillableHours'])

    # Compute FTE
    df['FTE'] = df['TotalBillableHours'].astype(float).apply(compute_fte)

    # Create Month field
    df['Month'] = df['Date_a'].dt.to_period('M').astype(str)

    # Group by Month and FinalCustomerName
    monthly_fte = df.groupby(['FinalCustomerName', 'Month'])['FTE'].sum().reset_index()

    # Pivot for visualization
    fte_pivot = monthly_fte.pivot(index='Month', columns='FinalCustomerName', values='FTE').fillna(0)

    # Plot line chart of top 6 clients by average FTE
    top_clients = fte_pivot.mean().sort_values(ascending=False).head(6).index
    chart_data = fte_pivot[top_clients]

    fig, ax = plt.subplots(figsize=(10, 5))
    chart_data.plot(ax=ax, marker='o')
    ax.set_title("MoM FTE Trends by Client (Top 6)", fontsize=14)
    ax.set_xlabel("Month")
    ax.set_ylabel("FTE (Headcount)")
    ax.grid(True)
    st.pyplot(fig)

    # Return the raw table as well
    st.markdown("### 📋 Raw FTE Table")
    return monthly_fte
