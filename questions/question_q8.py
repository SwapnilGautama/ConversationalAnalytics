import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from kpi_engine.utilization import load_ut_data

def run(params):
    df = load_ut_data()

    # Confirm available columns
    expected_cols = ['DU', 'BU', 'Segment', 'PSNo', 'UT%', 'Month', 'Quarter', 'Year']
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Missing columns in data: {missing_cols}")
        return

    trend_type = params.get("trend_type", "Month")
    selected_segment = params.get("segment")
    selected_bu = params.get("bu")
    selected_du = params.get("du")
    selected_agent = params.get("agent")

    # Apply filters safely
    filters = {
        "Segment": selected_segment,
        "BU": selected_bu,
        "DU": selected_du,
        "PSNo": selected_agent,
    }

    for col, selected_val in filters.items():
        if selected_val and col in df.columns:
            df = df[df[col].isin(selected_val)]

    # Standardize time column
    time_col = trend_type
    df[time_col] = df[time_col].astype(str)  # Avoid Period() error

    def generate_summary_table(df, group_col, time_col):
        pivot = df.pivot_table(index=group_col, columns=time_col, values="UT%", aggfunc="mean")
        pivot = pivot.sort_index(axis=1)
        diff = pivot.diff(axis=1)
        latest_cols = pivot.columns[-2:] if len(pivot.columns) >= 2 else pivot.columns
        arrows = diff[latest_cols[-1]].apply(
            lambda x: "↑" if x > 1 else ("↓" if x < -1 else "")
        )
        pct_change = (
            (pivot[latest_cols[-1]] - pivot[latest_cols[-2]])
            / pivot[latest_cols[-2]].replace(0, pd.NA)
            * 100
            if len(latest_cols) == 2 else pd.Series([""] * len(pivot))
        )
        combined = pivot.copy()
        combined[latest_cols[-1]] = pivot[latest_cols[-1]].round(2).astype(str) + " " + arrows + " (" + pct_change.round(1).astype(str) + "%)"
        return combined.fillna("None")

    if "DU" in df.columns:
        st.subheader(f"Utilization % by DU")
        du_table = generate_summary_table(df, "DU", time_col)
        st.dataframe(du_table.style.set_properties(border_color='lightgrey', border_width='1px'))

    if "BU" in df.columns:
        st.subheader(f"Utilization % by BU")
        bu_table = generate_summary_table(df, "BU", time_col)
        st.dataframe(bu_table.style.set_properties(border_color='lightgrey', border_width='1px'))

    if "PSNo" in df.columns:
        st.subheader(f"Utilization % by Agent")
        agent_table = df.pivot_table(index="PSNo", columns=time_col, values="UT%", aggfunc="mean").sort_index(axis=1)
        st.dataframe(agent_table.style.set_properties(border_color='lightgrey', border_width='1px'))

    # Trend Charts
    if "DU" in df.columns:
        st.subheader("Trend Chart by DU")
        trend_df = df.groupby([time_col, "DU"])["UT%"].mean().reset_index()
        plt.figure(figsize=(12, 5))
        sns.lineplot(data=trend_df, x=time_col, y="UT%", hue="DU", palette="pastel", marker="o")
        plt.xticks(rotation=45)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        st.pyplot(plt)

    if "BU" in df.columns:
        st.subheader("Trend Chart by BU")
        trend_df_bu = df.groupby([time_col, "BU"])["UT%"].mean().reset_index()
        plt.figure(figsize=(12, 5))
        sns.lineplot(data=trend_df_bu, x=time_col, y="UT%", hue="BU", palette="pastel", marker="o")
        plt.xticks(rotation=45)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        st.pyplot(plt)

    if "PSNo" in df.columns:
        st.subheader("Trend Chart by Agent")
        top_agents = df["PSNo"].value_counts().head(10).index.tolist()
        trend_df_agent = df[df["PSNo"].isin(top_agents)].groupby([time_col, "PSNo"])["UT%"].mean().reset_index()
        plt.figure(figsize=(12, 5))
        sns.lineplot(data=trend_df_agent, x=time_col, y="UT%", hue="PSNo", palette="pastel", marker="o")
        plt.xticks(rotation=45)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        st.pyplot(plt)
