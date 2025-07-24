# question_q7.py

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns

def compute_fte(total_hours):
    return total_hours / (8 * 21)

def run(df, user_question):
    # Load correct dataset
    df = pd.read_excel("sample_data/LNTData.xlsx")

    df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
    df = df.dropna(subset=['Date_a', 'FinalCustomerName', 'TotalBillableHours'])
    df['FTE'] = df['TotalBillableHours'].astype(float).apply(compute_fte)
    df['Month'] = df['Date_a'].dt.to_period('M').astype(str)

    monthly_fte = df.groupby(['FinalCustomerName', 'Month'])['FTE'].sum().reset_index()
    fte_pivot = monthly_fte.pivot(index='Month', columns='FinalCustomerName', values='FTE').fillna(0)

    # Select top 6 clients by average FTE
    top_clients = fte_pivot.mean().sort_values(ascending=False).head(6).index
    chart_data = fte_pivot[top_clients]

    # 📌 Text Insight: Overall headcount growth
    overall_fte = chart_data.sum(axis=1)
    first_month = overall_fte.index[0]
    last_month = overall_fte.index[-1]
    fte_change = overall_fte.iloc[-1] - overall_fte.iloc[0]
    pct_change = (fte_change / overall_fte.iloc[0]) * 100 if overall_fte.iloc[0] else 0

    st.markdown(
        f"🔍 **Overall FTE (Headcount)** grew from **{overall_fte.iloc[0]:.1f}** in **{first_month}** "
        f"to **{overall_fte.iloc[-1]:.1f}** in **{last_month}**, a change of **{fte_change:.1f} FTEs "
        f"({pct_change:.1f}%)**."
    )

    # 🔄 Layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📋 MoM FTE per Client")
        st.dataframe(
            monthly_fte.rename(columns={"FinalCustomerName": "Client", "FTE": "FTE (Headcount)"}),
            use_container_width=True
        )

    with col2:
        st.markdown("### 📈 MoM FTE Trend (Top 6 Clients)")
        fig, ax = plt.subplots(figsize=(8, 5))

        # Soft grey border
        for spine in ax.spines.values():
            spine.set_color('#D3D3D3')
            spine.set_linewidth(0.6)

        # Pastel smooth lines
        pastel_palette = sns.color_palette("pastel", len(top_clients))
        for idx, client in enumerate(top_clients):
            ax.plot(chart_data.index, chart_data[client], label=client,
                    marker='o', linewidth=2, color=pastel_palette[idx])

        ax.set_title("Monthly FTE (Smoothed Trend)", fontsize=13)
        ax.set_xlabel("Month")
        ax.set_ylabel("FTE (Headcount)")
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(False)
        plt.xticks(rotation=45)
        st.pyplot(fig)

    return monthly_fte
