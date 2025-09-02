# ✅ Q1 — Margin % is (Revenue - Cost)/Revenue | Tabs by Client, Segment, BU, DU
# Changes in this version:
#  • Removed Outliers (IQR) section.
#  • Added "Revenue at risk" metric (amount + % of total revenue in selection).
#  • Added "Top contributors to risk" (largest revenue accounts below threshold).
#  • Preserved: unique Plotly keys (no router/AI fallback), 6-month chart, compact table.

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

pd.options.display.float_format = '{:,.1f}'.format  # 1-decimal global display


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
    """Plotly combo chart (if Plotly is available)."""
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
    st.plotly_chart(fig, use_container_width=True, key=key)  # unique key avoids router collision


def _plot_combo_matplotlib(cdf: pd.DataFrame):
    """Matplotlib fallback (no SciPy needed)."""
    color_rev = "#A5D8FF"
    color_cost = "#FFD6A5"
    color_line = "#FF6B6B"
    soft_grey = "#D0D0D0"

    x = np.arange(len(cdf))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(8, 3.2))
    ax1.set_facecolor("white")
    fig.patch.set_facecolor("white")

    ax1.bar(x - width/2, cdf["Revenue_mn"].values, width, color=color_rev, label="Revenue (mn USD)")
    ax1.bar(x + width/2, cdf["Cost_mn"].values, width, color=color_cost, label="Cost (mn USD)")

    for spine in ["bottom", "left", "right", "top"]:
        ax1.spines[spine].set_color(soft_grey)
        ax1.spines[spine].set_linewidth(1.0)

    ax1.tick_params(axis="x", colors="#333333")
    ax1.tick_params(axis="y", colors="#333333")
    ax1.set_ylabel("Revenue/Cost (mn USD)")

    ax2 = ax1.twinx()
    yline = cdf["Margin %"].fillna(0).values
    ax2.plot(x, yline, color=color_line, linewidth=2, marker="o")
    ax2.spines["right"].set_color(soft_grey)
    ax2.spines["right"].set_linewidth(1.0)
    ax2.set_ylabel("Margin %")

    ax1.set_xticks(x)
    ax1.set_xticklabels(cdf["MonthLabel"].tolist(), rotation=0)

    handles1, labels1 = ax1.get_legend_handles_labels()
    line_proxy = plt.Line2D([0], [0], color=color_line, lw=2)
    handles1.append(line_proxy)
    labels1.append("Margin %")
    ax1.legend(handles1, labels1, loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=3, frameon=False)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# -------------------- analysis --------------------
def margin_analysis(df, group_field, threshold, target_month):
    """
    Renders (INSIGHTS first), then:
      • filtered table (only Revenue/Cost/Margin in mn USD and Margin %)
      • combo chart below (last 6 months)
    """
    group_name = group_field if isinstance(group_field, str) else " × ".join(group_field)
    group_cols = [group_field] if isinstance(group_field, str) else group_field

    # Monthly pivot per group
    df_margin = compute_margin(df, group_cols)

    # Time window for calculations (selection drives insights/table)
    if target_month is not None:
        window_mask = df_margin["Month"].dt.to_period("M") == target_month.to_period("M")
        filtered_data = df_margin[window_mask]
        time_label = target_month.strftime("%B %Y")
    else:
        latest_month = df_margin["Month"].max()
        quarter_start = latest_month - relativedelta(months=2)
        filtered_data = df_margin[(df_margin["Month"] >= quarter_start) & (df_margin["Month"] <= latest_month)]
        time_label = "the last quarter"

    # Aggregate to group level across selected period
    grouped = filtered_data.groupby(group_cols, dropna=False).agg({
        "Revenue": "sum",
        "Cost": "sum"
    }).reset_index()

    # Core metrics
    grouped["Margin %"] = ((grouped["Revenue"] - grouped["Cost"]) / grouped["Revenue"]) * 100
    grouped["Revenue (Million USD)"] = grouped["Revenue"] / 1e6
    grouped["Cost (Million USD)"] = grouped["Cost"] / 1e6
    grouped["Margin (Million USD)"] = (grouped["Revenue"] - grouped["Cost"]) / 1e6

    # Net margin %
    agg_rev = grouped["Revenue"].sum()
    agg_cost = grouped["Cost"].sum()
    net_margin_pct = ((agg_rev - agg_cost) / agg_rev * 100) if agg_rev else None

    # Below-threshold entities for this selection
    below_df = grouped[(grouped["Margin %"] < threshold) & (grouped["Revenue (Million USD)"] > 0)]
    total_entities = grouped.shape[0]
    low_margin_count = below_df.shape[0]
    proportion = (low_margin_count / total_entities * 100) if total_entities else 0

    # ---------- INSIGHTS ----------
    st.markdown(
        f"🔍 **{group_name}** — For **{time_label}**, **{low_margin_count}** of **{total_entities}** "
        f"entities had average margin below **{threshold}%** (**{proportion:,.1f}%**)."
    )

    # KPI tiles: Net margin %, Revenue at risk
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.metric(
            label="Net Margin % (Aggregated)",
            value=f"{net_margin_pct:,.1f}%" if net_margin_pct is not None else "N/A",
            help=f"Across all selected {group_name.lower()} for {time_label}"
        )
    with c2:
        rev_at_risk = below_df["Revenue"].sum()
        total_rev = grouped["Revenue"].sum()
        risk_pct = (rev_at_risk / total_rev * 100) if total_rev else 0
        st.metric(
            label="Revenue at Risk (below margin threshold)",
            value=f"${rev_at_risk/1e6:,.1f} mn",
            delta=f"{risk_pct:,.1f}% of selection revenue",
            help="Revenue contributed by entities below the margin threshold"
        )

    # Top contributors to risk (largest revenue in low-margin set)
    if not below_df.empty:
        top_n = 5
        top_risk = (
            below_df[group_cols + ["Revenue"]]
            .sort_values("Revenue", ascending=False)
            .head(top_n)
        )
        names = top_risk[group_cols[0]].astype(str).tolist()
        vals = (top_risk["Revenue"] / 1e6).round(1).tolist()
        bullets = ", ".join([f"{n} (${v:,.1f} mn)" for n, v in zip(names, vals)])
        st.markdown(f"**Top contributors to risk** — {bullets}")

    # Month aggregates for drivers (based on selected window)
    month_agg = (
        filtered_data.groupby(["Month"], dropna=False)[["Revenue", "Cost"]]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    # Margin % trend and drivers
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

    # ---------- TABLE (ONLY requested columns & formats) ----------
    if not below_df.empty:
        show_cols = group_cols + [
            "Revenue (Million USD)", "Cost (Million USD)", "Margin (Million USD)", "Margin %"
        ]
        display_df = (
            below_df[show_cols]
            .copy()
            .sort_values("Margin %")  # ascending (lowest first)
            .reset_index(drop=True)
        )

        # Round and format
        display_df["Revenue (Million USD)"] = display_df["Revenue (Million USD)"].round(1)
        display_df["Cost (Million USD)"] = display_df["Cost (Million USD)"].round(1)
        display_df["Margin (Million USD)"] = display_df["Margin (Million USD)"].round(1)
        display_df["Margin %"] = display_df["Margin %"].round(0).astype("Int64")

        st.caption("Entities below threshold (all)")
        st.dataframe(
            display_df.style.format({
                "Revenue (Million USD)": "{:,.1f}",
                "Cost (Million USD)": "{:,.1f}",
                "Margin (Million USD)": "{:,.1f}",
                "Margin %": "{:,.0f}"
            }),
            use_container_width=True
        )
    else:
        st.info("No records found below the margin threshold.")

    # ---------- CHART (LAST 6 MONTHS) ----------
    # Build chart from last 6 months globally (not just selection window)
    df_month = (
        df_margin.groupby("Month")[["Revenue", "Cost"]]
        .sum()
        .reset_index()
        .sort_values("Month")
    )
    if not df_month.empty:
        latest = df_month["Month"].max()
        six_start = latest - relativedelta(months=5)
        cdf = df_month[(df_month["Month"] >= six_start) & (df_month["Month"] <= latest)].copy()

        if not cdf.empty:
            cdf["MonthLabel"] = cdf["Month"].dt.strftime("%b %Y")
            cdf["Revenue_mn"] = (cdf["Revenue"] / 1e6).fillna(0.0)
            cdf["Cost_mn"] = (cdf["Cost"] / 1e6).fillna(0.0)
            with np.errstate(divide='ignore', invalid='ignore'):
                cdf["Margin %"] = (((cdf["Revenue"] - cdf["Cost"]) / cdf["Revenue"]) * 100).replace([np.inf, -np.inf], np.nan)

            st.markdown("**Revenue/Cost vs Margin % (last 6 months)**")
            if _PLOTLY_OK:
                chart_key = f"q1_plotly_{group_name.replace(' ', '_')}"
                _plot_combo_plotly(cdf, key=chart_key)  # unique key per tab
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
