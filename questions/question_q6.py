import streamlit as st
import pandas as pd

def run_question_q6(df_revenue: pd.DataFrame, df_hours: pd.DataFrame):
    st.markdown("## 💡 Realized Rate Analysis (by FinalCustomerName & Segment)")

    # ⏱️ Left Filter Pane
    with st.sidebar:
        st.markdown("### 🎛️ Filters")
        min_rate = st.slider("Minimum Realized Rate", 0.0, 1000.0, 0.0, step=1.0)
        max_rate = st.slider("Maximum Realized Rate", 0.0, 1000.0, 1000.0, step=1.0)

        segment_options = ["All"] + sorted(df_hours["Segment"].dropna().unique())
        segment = st.selectbox("Segment", segment_options)

        bu_options = ["All"] + sorted(df_hours["BU"].dropna().unique())
        bu = st.selectbox("BU", bu_options)

        du_options = ["All"] + sorted(df_hours["DU"].dropna().unique())
        du = st.selectbox("DU", du_options)

    # 🧹 Clean + filter
    for df in [df_revenue, df_hours]:
        df["Month"] = df["date_a"].dt.strftime("%b")
        df["Year"] = df["date_a"].dt.year.astype(str)
        df["MonthYear"] = df["Month"] + " " + df["Year"]

    if segment != "All":
        df_hours = df_hours[df_hours["Segment"] == segment]
    if bu != "All":
        df_hours = df_hours[df_hours["BU"] == bu]
    if du != "All":
        df_hours = df_hours[df_hours["DU"] == du]

    # 🧮 Aggregate before merging to avoid duplication
    agg_hours = df_hours.groupby(["FinalCustomerName", "MonthYear", "Segment", "BU", "DU"], as_index=False)["NetAvailableHours"].sum()
    agg_rev = df_revenue.groupby(["FinalCustomerName", "MonthYear"], as_index=False)["Revenue"].sum()

    # 🔗 Merge
    df = pd.merge(agg_rev, agg_hours, on=["FinalCustomerName", "MonthYear"], how="inner")

    # 🧾 Compute Realized Rate
    df["RealizedRate"] = df.apply(
        lambda row: round(row["Revenue"] / row["NetAvailableHours"], 2) if row["NetAvailableHours"] > 0 else 0,
        axis=1
    )

    # 🎚️ Apply Rate filter
    df_filtered = df[(df["RealizedRate"] >= min_rate) & (df["RealizedRate"] <= max_rate)]

    # 🧮 Pivot Tables
    def get_pivots(df, group_col):
        rr = df.pivot_table(index=group_col, columns="MonthYear", values="RealizedRate", aggfunc="mean").fillna(0)
        rev = df.pivot_table(index=group_col, columns="MonthYear", values="Revenue", aggfunc="sum").fillna(0).astype(int
