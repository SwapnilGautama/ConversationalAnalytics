# ✅ Q1 — Margin % is (Revenue - Cost)/Revenue | Tabs by Client, Segment, BU, DU
# This version is robust in environments without Plotly:
#  • Uses Plotly if installed; otherwise falls back to Matplotlib
#  • All insights rendered ABOVE the table
#  • Table lists ALL entities below threshold
#  • Combo chart (bars: Revenue/Cost in mn USD, line: Margin %) shown BELOW the table
import pandas as pd
from dateutil.relativedelta import relativedelta
import streamlit as st
import re

# -------- optional plotting backends --------
_PLOTLY_OK = False
try:
    import plotly.graph_objects as go
    _PLOTLY_OK = True
except Exception:
    _PLOTLY_OK = False

import matplotlib.pyplot as plt
import numpy as np

pd.options.display.float_format = '{:,.1f}'.format  # Force 1 decimal display globally


# -------------------- helpers --------------------
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


def _outlier_masks_iqr(series: pd.Series):
    """
    Return two boolean masks (low_mask, high_mask) via IQR rule:
    low  < Q1 - 1.5 * IQR
    high > Q3 + 1.5 * IQR
    """
    s = series.dropna()
    if s.empty:
        f = pd.Series([False] * len(series), index=series.index)
        return f, f
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    low_cut = q1 - 1.5 * iqr
    high_cut = q3 + 1.5 * iqr
    return (series < low_cut), (series > high_cut)


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
def _plot_combo_plotly(cdf: pd.DataFrame):
    """Plot with Plotly if available."""
    color_rev = "#A5D8FF"   # pastel blue
    color_cost = "#FFD6A5"  # pastel peach
    color_line = "#FF6B6B"  # soft coral
    soft_grey = "#D0D0D0"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Revenue (mn USD)", x=cdf["MonthLabel"], y=cdf["Revenue_mn"],
        marker_color=color_rev
    ))
    fig.add_trace(go.Bar(
        name="Cost (mn USD)", x=cdf["MonthLabel"], y=cdf["Cost_mn"],
        marker_color=color_cost
    ))
    fig.add_trace(go.Scatter(
        name="Margin %", x=cdf["MonthLabel"], y=cdf["Margin %"],
        mode="lines+markers",
        line=dict(color=color_line, width=2, shape="spline"),
        yaxis="y2"
    ))

    fig.update_layout(
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=20, r=10, l=10, b=10),
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
    st.plotly_chart(fig, use_container_width=True)


def _plot_combo_matplotlib(cdf: pd.DataFrame):
    """Matplotlib fallback with similar styling."""
    # Colors
    color_rev = "#A5D8FF"
    color_cost = "#FFD6A5"
    color_line = "#FF6B6B"
    soft_grey = "#D0D0D0"

    x = np.arange(len(cdf))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(8, 3.0))
    # No gridlines; white background
    ax1.set_facecolor("white")
    fig.patch.set_facecolor("white")

    # Bars
    ax1.bar(x - width/2, cdf["Revenue_mn"], width, color=color_rev, label="Revenue (mn USD)")
    ax1.bar(x + width/2, cdf["Cost_mn"], width, color=color_cost, label="Cost (mn USD)")

    # Axis styles (soft grey lines/border via spines)
    for spine in ["bottom", "left", "right", "top"]:
        ax1.spines[spine].set_color(soft_grey)
        ax1.spines[spine].set_linewidth(1.0)

    ax1.tick_params(axis="x", colors="#333333")
    ax1.tick_params(axis="y", colors="#333333")
    ax1.set_ylabel("Revenue/Cost (mn USD)")

    # Secondary axis for margin %
    ax2 = ax1.twinx()
    ax2.plot(x, cdf["Margin %"], color=color_line, linewidth=2, marker="o")
    # Make line look smoother by simple interpolation if enough points
    if len(x) >= 3:
        from scipy.interpolate import make_interp_spline  # might not exist; guard
        try:
            xs = np.linspace(x.min(), x.max(), len(x)*10)
            spl = make_interp_spline(x, cdf["Margin %"], k=2)
            ax2.lines[-1].set_visible(False)
            ax2.plot(xs, spl(xs), color=color_line, linewidth=2)
        except Exception:
            pass

    # Mirror style on right axis
    ax2.spines["right"].set_color(soft_grey)
    ax2.spines["right"].set_linewidth(1.0)
    ax2.set_ylabel("Margin %")

    ax1.set_xticks(x)
    ax1.set_xticklabels(cdf["MonthLabel"], rotation=0)

    # Legend
    handles1, labels1 = ax1.get_legend_handles_labels()
    # Add line label manually
    line_proxy = plt.Line2D([0], [0], color=color_line, lw=2)
    handles1.append(line_proxy)
    labels1.append("Margin %")
    leg = ax1.legend(handles1, labels1, loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=3, frameon=False)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# -------------------- analysis --------------------
def margin_analysis(df, group_field, threshold, target_month):
    """
    Renders (all INSIGHTS first):
      • Summary sentence
      • Net margin % (aggregated across selected period & scope)
      • Outliers on margin % (low & high) as inline text
      • Margin% trend for last 3 months + reasons (revenue/cost drivers)
      • THEN the table of ALL entities below threshold
      • FINALLY a combo chart (bars: Revenue/Cost, line: Margin%)
    """
    group_name = group_field if isinstance(group_field, str) else " × ".join(group_field)
    group_cols = [group_field] if isinstance(group_field, str) else group_field

    # monthly pivot per group
    df_margin = compute_margin(df, group_cols)

    # Time window selection
    if target_month is not None:
        window_mask = df_margin["Month"].dt.to_period("M") == target_month.to_period("M")
        filtered_data = df_margin[window_mask]
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

    # Core metrics at group level
    grouped["Margin %"] = ((grouped["Revenue"] - grouped["Cost"]) / grouped["Revenue"]) * 100
    grouped["Revenue (Million USD)"] = grouped["Revenue"] / 1e6
    grouped["Cost (Million USD)"] = grouped["Cost"] / 1e6

    # ---- Net Margin % (aggregated across selected entities & period)
    agg_rev = grouped["Revenue"].sum()
    agg_cost = grouped["Cost"].sum()
    net_margin_pct = ((agg_rev - agg_cost) / agg_rev * 100) if agg_rev else None

    # ---- Entities below threshold: ALL (shown later as a table)
    below_df = grouped[(grouped["Margin %"] < threshold) & (grouped["Revenue (Million USD)"] > 0)]
    total_entities = grouped.shape[0]
    low_margin_count = below_df.shape[0]
    proportion = (low_margin_count / total_entities * 100) if total_entities else 0

    # ---- Outliers (both low & high) via IQR — text lists
    low_list, high_list = "None", "None"
    if "Margin %" in grouped.columns and grouped["Margin %"].notna().any():
        low_mask, high_mask = _outlier_masks_iqr(grouped["Margin %"])
        low_outliers = grouped.loc[low_mask, group_cols + ["Margin %"]].sort_values("Margin %")
        high_outliers = grouped.loc[high_mask, group_cols + ["Margin %"]].sort_values("Margin %", ascending=False)
        if not low_outliers.empty:
            low_list = ", ".join(low_outliers[group_cols[0]].astype(str).tolist())
        if not high_outliers.empty:
            high_list = ", ".join(high_outliers[group_cols[0]].astype(str).tolist())

    # ---- 3-month margin% trend + reasons (drivers)
    month_agg = (
        filtered_data.groupby(["Month"], dropna=False)[["Revenue", "Cost"]]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    # ---------- INSIGHTS (ABOVE the table) ----------
    st.markdown(
        f"🔍 **{group_name}** — For **{time_label}**, **{low_margin_count}** of **{total_entities}** "
        f"entities had average margin below **{threshold}%** (**{proportion:,.1f}%**)."
    )

    c1, c2 = st.columns([1, 4])
    with c1:
        st.metric(
            label="Net Margin % (Aggregated)",
            value=f"{net_margin_pct:,.1f}%" if net_margin_pct is not None else "N/A",
            help=f"Across all selected {group_name.lower()} for {time_label}"
        )

    st.markdown(
        f"**Outliers (IQR):** Low margin → *{low_list}*  |  High margin → *{high_list}*"
    )

    if len(month_agg) >= 1:
        month_agg["Margin %"] = ((month_agg["Revenue"] - month_agg["Cost"]) / month_agg["Revenue"]) * 100
        last_3 = month_agg.tail(3).reset_index(drop=True)
        labels = [m.strftime("%b %Y") for m in last_3["Month"]]
        mvals = [f"{x:,.1f}%" if pd.notnull(x) else "N/A" for x in last_3["Margin %"]]

        st.markdown("**Margin % trend (last 3 months)**")
        st.write(", ".join([f"{lab}: {val}" for lab, val in zip(labels, mvals)]))

        if len(last_3) >= 2:
            lines = []
            for i in range(1, len(last_3)):
                r_chg = _pct_change(last_3.loc[i-1, "Revenue"], last_3.loc[i, "Revenue"])
                c_chg = _pct_change(last_3.loc[i-1, "Cost"], last_3.loc[i, "Cost"])
                lines.append(
                    f"From **{labels[i-1]} → {labels[i]}**: "
                    f"Revenue {_fmt_pct(r_chg)}, Cost {_fmt_pct(c_chg)}."
                )
            r_total = _pct_change(last_3.loc[0, "Revenue"], last_3.loc[len(last_3)-1, "Revenue"])
            c_total = _pct_change(last_3.loc[0, "Cost"], last_3.loc[len(last_3)-1, "Cost"])
            lines.append(
                f"Overall (**{labels[0]} → {labels[-1]}**): "
                f"Revenue {_fmt_pct(r_total)}, Cost {_fmt_pct(c_total)}."
            )
            st.caption("**Drivers**")
            for ln in lines:
                st.markdown(f"- {ln}")

    # ---------- TABLE ----------
    if not below_df.empty:
        st.caption("Entities below threshold (all)")
        display_df = below_df.sort_values("Margin %").reset_index(drop=True).copy()
        st.dataframe(
            display_df.style.format({
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

    # ---------- CHART ----------
    if not month_agg.empty:
        cdf = month_agg.copy()
        cdf["MonthLabel"] = cdf["Month"].dt.strftime("%b %Y")
        cdf["Revenue_mn"] = cdf["Revenue"] / 1e6
        cdf["Cost_mn"] = cdf["Cost"] / 1e6
        cdf["Margin %"] = ((cdf["Revenue"] - cdf["Cost"]) / cdf["Revenue"]) * 100

        st.markdown("**Revenue/Cost vs Margin % (by Month)**")
        if _PLOTLY_OK:
            _plot_combo_plotly(cdf)
        else:
            _plot_combo_matplotlib(cdf)


# -------------------- entry point --------------------
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
