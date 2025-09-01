# ✅ FINAL Q1 — Margin % is (Revenue - Cost)/Revenue | Tabs by Segment, DU, BU, Customer
# + Net Margin% (aggregated) metric
# + Outlier list (IQR-based) for low-margin entities
import pandas as pd
from dateutil.relativedelta import relativedelta
import streamlit as st
import re

pd.options.display.float_format = '{:,.1f}'.format  # Force 1 decimal display globally


# -------------------- helpers (preserved) --------------------
def compute_margin(df, groupby_fields):
    """
    Builds a Month x (group fields) pivot with Revenue/Cost totals.
    Expects df columns: Month, Type (Revenue/Cost), Amount (USD).
    """
    df = df.copy()
    pivot = df.pivot_table(
        index=["Month"] + groupby_fields,
        columns="Type",
        values="Amount",
        aggfunc="sum"
    ).reset_index()

    pivot["Revenue"] = pivot.get("Revenue", 0)
    pivot["Cost"] = pivot.get("Cost", 0)
    return pivot


def extract_threshold(user_question, default_threshold=30):
    if user_question:
        patterns = [
            r"margin\s*<\s*(\d+)",
            r"less than\s*(\d+)",
            r"below\s*(\d+)",
            r"under\s*(\d+)",
            r"margin.*?(\d+)\s*%"
        ]
        for pattern in patterns:
            match = re.search(pattern, user_question.lower())
            if match:
                return float(match.group(1))
    return default_threshold


def extract_month(user_question):
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }
    if user_question:
        uq = user_question.lower()
        for name, num in months.items():
            if name in uq:
                year_match = re.search(rf"{name}\s*(\d{{4}})", uq)
                if year_match:
                    year = int(year_match.group(1))
                    return pd.Timestamp(year=year, month=num, day=1)
    return None


# -------------------- NEW: Outlier detection --------------------
def _low_margin_outliers_iqr(series: pd.Series):
    """
    Return a boolean mask marking *low* outliers via IQR rule:
    value < Q1 - 1.5 * IQR
    Robust to skew; ignores NaNs.
    """
    s = series.dropna()
    if s.empty:
        return pd.Series([False] * len(series), index=series.index)

    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    cutoff = q1 - 1.5 * iqr
    return series < cutoff


# -------------------- analysis (extended) --------------------
def margin_analysis(df, group_field, threshold, target_month):
    """
    Renders:
      • summary sentence
      • NEW: Net margin % (aggregated across selected period) as st.metric
      • Table of entities below threshold (top10)
      • NEW: Outliers on margin % using IQR (low outliers only)
    """
    group_name = group_field if isinstance(group_field, str) else " × ".join(group_field)
    group_cols = [group_field] if isinstance(group_field, str) else group_field

    # monthly pivot per group
    df_margin = compute_margin(df, group_cols)

    # Time window
    if target_month is not None:
        filtered_data = df_margin[df_margin["Month"].dt.to_period("M") == target_month.to_period("M")]
        time_label = target_month.strftime("%B %Y")
    else:
        latest_month = df_margin["Month"].max()
        quarter_start = latest_month - relativedelta(months=2)
        filtered_data = df_margin[(df_margin["Month"] >= quarter_start) & (df_margin["Month"] <= latest_month)]
        time_label = "the last quarter"

    # Aggregate to group level across the selected period
    grouped = filtered_data.groupby(group_cols, dropna=False).agg({
        "Revenue": "sum",
        "Cost": "sum"
    }).reset_index()

    # Core metrics
    grouped["Margin %"] = ((grouped["Revenue"] - grouped["Cost"]) / grouped["Revenue"]) * 100
    grouped["Revenue (Million USD)"] = grouped["Revenue"] / 1e6
    grouped["Cost (Million USD)"] = grouped["Cost"] / 1e6

    # --- NEW: Net Margin % (aggregated across selected entities & period)
    agg_rev = grouped["Revenue"].sum()
    agg_cost = grouped["Cost"].sum()
    net_margin_pct = ((agg_rev - agg_cost) / agg_rev * 100) if agg_rev else None

    c1, c2 = st.columns([1, 4])
    with c1:
        st.metric(
            label="Net Margin % (Aggregated)",
            value=f"{net_margin_pct:,.1f}%" if net_margin_pct is not None else "N/A",
            help=f"Across all selected {group_name.lower()} for {time_label}"
        )

    # Threshold filter
    filtered_df = grouped[(grouped["Margin %"] < threshold) & (grouped["Revenue (Million USD)"] > 0)]
    top_10 = filtered_df.sort_values("Margin %", ascending=False).head(10)

    total_entities = grouped.shape[0]
    low_margin_count = filtered_df.shape[0]
    proportion = (low_margin_count / total_entities * 100) if total_entities else 0

    st.markdown(
        f"🔍 **{group_name}** — For **{time_label}**, **{low_margin_count}** of **{total_entities}** "
        f"entities had average margin below **{threshold}%** (**{proportion:,.1f}%**)."
    )

    if not top_10.empty:
        st.caption("Entities below threshold (top 10)")
        st.dataframe(
            top_10.reset_index(drop=True).style.format({
                "Revenue": "{:,.1f}",
                "Cost": "{:,.1f}",
                "Margin %": "{:,.1f}",
                "Revenue (Million USD)": "{:,.1f}",
                "Cost (Million USD)": "{:,.1f}"
            }),
            use_container_width=True
        )
    else:
        st.info("No records found below the margin threshold.")

    # --- NEW: Outliers (low margin %) via IQR
    if "Margin %" in grouped.columns and grouped["Margin %"].notna().any():
        mask_outliers = _low_margin_outliers_iqr(grouped["Margin %"])
        outliers = grouped.loc[mask_outliers, group_cols + ["Margin %"]].sort_values("Margin %")
        if not outliers.empty:
            st.caption("Low-margin outliers (IQR method)")
            st.dataframe(
                outliers.reset_index(drop=True).style.format({"Margin %": "{:,.1f}"}),
                use_container_width=True
            )
        else:
            st.caption("Low-margin outliers (IQR): None detected.")


# -------------------- entry point (preserved) --------------------
def run(df, user_question=None):
    df = df.copy()

    # Normalize schema
    df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
    df = df.dropna(subset=["Month"])

    # Standardized dimension names
    df["Client"] = df.get("FinalCustomerName", "Unknown")
    df["Segment"] = df.get("Segment", "Unknown")
    df["BU"] = df.get("Exec DG", "Unknown")
    df["DU"] = df.get("Exec DU", "Unknown")

    # Parse inputs
    threshold = extract_threshold(user_question)
    target_month = extract_month(user_question)

    tabs = st.tabs(["📋 By Client", "🚛 By Segment", "🏢 By BU", "🏭 By DU"])

    with tabs[0]:
        margin_analysis(df, "Client", threshold, target_month)

    with tabs[1]:
        margin_analysis(df, "Segment", threshold, target_month)

    with tabs[2]:
        margin_analysis(df, "BU", threshold, target_month)

    with tabs[3]:
        margin_analysis(df, "DU", threshold, target_month)
