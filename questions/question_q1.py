# ✅ Q1 — Margin % is (Revenue - Cost)/Revenue | Tabs by Client, Segment, BU, DU
# Updates:
#  • Single-row KPI header (Net Margin %, Revenue at Risk, Total Revenue, Total Cost, Margin Gap).
#  • Rounded all USD values to 2 decimals (KPIs, tables, charts).
#  • Added labels on bar + line chart.
#  • All previous features preserved.

import pandas as pd
from dateutil.relativedelta import relativedelta
import streamlit as st
import re

# Optional Plotly; fallback to Matplotlib if not present
_PLOTLY_OK = False
try:
    import plotly.graph_objects as go
    _PLOTLY_OK = True
except Exception:
    _PLOTLY_OK = False

import matplotlib.pyplot as plt
import numpy as np


# -------------------- helpers --------------------
def compute_margin(df, groupby_fields):
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


def _pct_change(old, new):
    try:
        old = float(old); new = float(new)
        if old == 0:
            return None
        return (new - old) / old * 100.0
    except Exception:
        return None


def _fmt_pct(p):
    if p is None:
        return "N/A"
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:,.1f}%"


# -------------------- plotting --------------------
def _plot_combo_plotly(cdf: pd.DataFrame, key: str):
    color_rev = "#A5D8FF"   # pastel blue
    color_cost = "#FFD6A5"  # pastel peach
    color_line = "#FF6B6B"  # soft coral
    soft_grey = "#D0D0D0"

    rev_labels = cdf["Revenue_mn"].round(2)
    cost_labels = cdf["Cost_mn"].round(2)
    margin_labels = cdf["Margin %"].round(0).astype("Int64").astype(str)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Revenue (mn USD)",
        x=cdf["MonthLabel"],
        y=cdf["Revenue_mn"],
        marker_color=color_rev,
        text=rev_labels,
        textposition="outside",
        cliponaxis=False
    ))
    fig.add_trace(go.Bar(
        name="Cost (mn USD)",
        x=cdf["MonthLabel"],
        y=cdf["Cost_mn"],
        marker_color=color_cost,
        text=cost_labels,
        textposition="outside",
        cliponaxis=False
    ))
    fig.add_trace(go.Scatter(
        name="Margin %",
        x=cdf["MonthLabel"],
        y=cdf["Margin %"],
        mode="lines+markers+text",
        line=dict(color=color_line, width=2, shape="spline"),
        text=margin_labels,
        textposition="top center",
        yaxis="y2"
    ))

    fig.update_layout(
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=30, r=10, l=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_yaxes(
        title_text="Revenue/Cost (mn USD)", showgrid=False,
        showline=True, linecolor=soft_grey, mirror=True
    )
    fig.update_layout(
        yaxis2=dict(
            title="Margin %",
            overlaying="y", side="right",
            showgrid=False, showline=True, linecolor=soft_grey, mirror=True
        )
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=soft_grey, mirror=True)
    st.plotly_chart(fig, use_container_width=True, key=key)


# -------------------- analysis --------------------
def margin_analysis(df, group_field, threshold, target_month):
    group_name = group_field if isinstance(group_field, str) else " × ".join(group_field)
    group_cols = [group_field] if isinstance(group_field, str) else group_field

    df_margin = compute_margin(df, group_cols)

    if target_month is not None:
        window_mask = df_margin["Month"].dt.to_period("M") == target_month.to_period("M")
        filtered_data = df_margin[window_mask]
        time_label = target_month.strftime("%B %Y")
    else:
        latest_month = df_margin["Month"].max()
        quarter_start = latest_month - relativedelta(months=2)
        filtered_data = df_margin[(df_margin["Month"] >= quarter_start) & (df_margin["Month"] <= latest_month)]
        time_label = "the last quarter"

    grouped = filtered_data.groupby(group_cols, dropna=False).agg({
        "Revenue": "sum",
        "Cost": "sum"
    }).reset_index()

    grouped["Margin %"] = ((grouped["Revenue"] - grouped["Cost"]) / grouped["Revenue"]) * 100
    grouped["Revenue (Million USD)"] = (grouped["Revenue"] / 1e6).round(2)
    grouped["Cost (Million USD)"] = (grouped["Cost"] / 1e6).round(2)
    grouped["Margin (Million USD)"] = ((grouped["Revenue"] - grouped["Cost"]) / 1e6).round(2)

    agg_rev = grouped["Revenue"].sum()
    agg_cost = grouped["Cost"].sum()
    net_margin_pct = ((agg_rev - agg_cost) / agg_rev * 100) if agg_rev else None

    below_df = grouped[(grouped["Margin %"] < threshold) & (grouped["Revenue (Million USD)"] > 0)]
    total_entities = grouped.shape[0]
    low_margin_count = below_df.shape[0]
    proportion = (low_margin_count / total_entities * 100) if total_entities else 0

    st.markdown(
        f"🔍 **{group_name}** — For **{time_label}**, **{low_margin_count}** of **{total_entities}** "
        f"entities had average margin below **{threshold}%** (**{proportion:,.1f}%**)."
    )

    # KPI Row
    c1, c2, c3, c4, c5 = st.columns([1.0, 1.4, 1.1, 1.1, 1.4])
    with c1:
        st.metric("Net Margin % (Aggregated)", f"{net_margin_pct:,.1f}%")
    with c2:
        rev_at_risk = below_df["Revenue"].sum()
        risk_pct = (rev_at_risk / agg_rev * 100) if agg_rev else 0
        st.metric("Revenue at Risk (below margin threshold)", f"${rev_at_risk/1e6:,.2f} mn", f"{risk_pct:,.1f}%")
    with c3:
        st.metric("Total Revenue (selection)", f"${agg_rev/1e6:,.2f} mn")
    with c4:
        st.metric("Total Cost (selection)", f"${agg_cost/1e6:,.2f} mn")
    with c5:
        if not below_df.empty:
            curr_margin_amt = (below_df["Revenue"] - below_df["Cost"])
            req_margin_amt = (threshold / 100.0) * below_df["Revenue"]
            gap = np.maximum(0.0, req_margin_amt - curr_margin_amt)
            st.metric("Margin gap to reach threshold", f"${gap.sum()/1e6:,.2f} mn")
        else:
            st.metric("Margin gap to reach threshold", "$0.00 mn")

    # Table
    if not below_df.empty:
        show_cols = group_cols + [
            "Revenue (Million USD)", "Cost (Million USD)", "Margin (Million USD)", "Margin %"
        ]
        st.caption("Entities below threshold (all)")
        st.dataframe(
            below_df[show_cols].sort_values("Margin %").reset_index(drop=True).style.format({
                "Revenue (Million USD)": "{:,.2f}",
                "Cost (Million USD)": "{:,.2f}",
                "Margin (Million USD)": "{:,.2f}",
                "Margin %": "{:,.0f}"
            }),
            use_container_width=True
        )

    # Chart (last 6 months)
    df_month = df_margin.groupby("Month")[["Revenue", "Cost"]].sum().reset_index().sort_values("Month")
    if not df_month.empty:
        latest = df_month["Month"].max()
        six_start = latest - relativedelta(months=5)
        cdf = df_month[(df_month["Month"] >= six_start) & (df_month["Month"] <= latest)].copy()

        cdf["MonthLabel"] = cdf["Month"].dt.strftime("%b %Y")
        cdf["Revenue_mn"] = (cdf["Revenue"] / 1e6).round(2)
        cdf["Cost_mn"] = (cdf["Cost"] / 1e6).round(2)
        cdf["Margin %"] = (((cdf["Revenue"] - cdf["Cost"]) / cdf["Revenue"]) * 100).round(0)

        st.markdown("**Revenue/Cost vs Margin % (last 6 months)**")
        if _PLOTLY_OK:
            chart_key = f"q1_plotly_{group_name.replace(' ', '_')}"
            _plot_combo_plotly(cdf, key=chart_key)
