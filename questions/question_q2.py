# question_q2.py

import pandas as pd
import re

def run(df, user_question=None):
    import streamlit as st

    # ---------- Prep ----------
    df.columns = df.columns.str.strip()
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])

    # ✅ Apply Group1-based Revenue logic (preserves existing behavior)
    valid_group1 = ['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']
    df['Type'] = df['Type'].fillna('')
    df.loc[df['Group1'].isin(valid_group1), 'Type'] = 'Revenue'

    # Segment detection (default Transportation if not specified in question)
    segment = "Transportation"
    if user_question:
        for seg in df['Segment'].dropna().unique():
            if seg.lower() in user_question.lower():
                segment = seg
                break

    # Filter to selected segment
    df = df[df['Segment'] == segment].copy()

    # Split revenue/cost frames
    revenue_df = df[df['Type'] == 'Revenue'].copy()
    cost_df = df[df['Type'] == 'Cost'].copy()

    # If there is no cost data, bail early with a friendly message
    if cost_df.empty:
        st.warning(f"No cost data available for segment **{segment}**.")
        return

    # ---------- Monthly series (segment level) ----------
    seg_rev = revenue_df.groupby('Month')['Amount'].sum() if not revenue_df.empty else pd.Series(dtype=float)
    seg_cost = cost_df.groupby('Month')['Amount'].sum()

    # For reference windows
    months_sorted = seg_cost.index.sort_values()
    if len(months_sorted) == 0:
        st.warning("No monthly values found for cost.")
        return

    latest_month = months_sorted.max()
    prev_month = (latest_month - pd.DateOffset(months=1)).replace(day=1)
    prev2_month = (latest_month - pd.DateOffset(months=2)).replace(day=1)

    # Build a clean 3-month (or fewer) view for insights
    last_3_months = [m for m in months_sorted if m >= latest_month - pd.DateOffset(months=2)]
    last_3_cost = seg_cost.reindex(last_3_months).fillna(0.0)

    # ---------- Insight 1: Overall change in cost for the (up to) 3-month period ----------
    # Prefer latest vs two months back; fall back to latest vs previous when only 2 months present
    if len(last_3_months) >= 3 and prev2_month in seg_cost.index:
        base_month = prev2_month
    else:
        base_month = prev_month if prev_month in seg_cost.index else None

    def _fmt_mn(x):
        try:
            return f"{x/1e6:,.1f}"
        except Exception:
            return "0.0"

    def _pct(a, b):
        # pct change from a -> b
        if a == 0:
            return None
        return (b - a) / a * 100.0

    overall_line = "Overall cost change unavailable."
    if base_month is not None:
        base_val = float(seg_cost.get(base_month, 0.0))
        latest_val = float(seg_cost.get(latest_month, 0.0))
        pct_chg = _pct(base_val, latest_val)
        direction = "increased" if latest_val >= base_val else "decreased"
        if pct_chg is not None:
            overall_line = (
                f"Overall cost **{direction} {abs(pct_chg):,.1f}%** "
                f"from **{base_month.strftime('%b %Y')} (${_fmt_mn(base_val)} mn)** "
                f"to **{latest_month.strftime('%b %Y')} (${_fmt_mn(latest_val)} mn)**."
            )
        else:
            overall_line = (
                f"Overall cost in **{latest_month.strftime('%b %Y')}** is "
                f"${_fmt_mn(latest_val)} mn (no valid base month for comparison)."
            )

    # ---------- Insight 2: Cost trend for the last 3 months ----------
    trend_lines = []
    if len(last_3_months) > 0:
        # Show values and MoM deltas
        for i, m in enumerate(last_3_months):
            val = float(last_3_cost.get(m, 0.0))
            if i == 0:
                trend_lines.append(f"- **{m.strftime('%b %Y')}**: ${_fmt_mn(val)} mn")
            else:
                prev_val = float(last_3_cost.get(last_3_months[i-1], 0.0))
                pct_mom = _pct(prev_val, val)
                if pct_mom is None:
                    trend_lines.append(f"- **{m.strftime('%b %Y')}**: ${_fmt_mn(val)} mn (MoM: N/A)")
                else:
                    sign = "↑" if pct_mom > 0 else "↓"
                    trend_lines.append(
                        f"- **{m.strftime('%b %Y')}**: ${_fmt_mn(val)} mn "
                        f"(MoM: {sign} {abs(pct_mom):,.1f}%)"
                    )

    # ---------- Insight 3: Key cost drivers (story) ----------
    # Use Group4 changes between base_month and latest_month to tell a story
    story = "Cost driver story unavailable."
    g4 = None
    if base_month is not None:
        group4_df = cost_df[['Month', 'Amount', 'Group4']].dropna(subset=['Group4']).copy()
        if not group4_df.empty:
            g4 = group4_df.groupby(['Group4', 'Month'])['Amount'].sum().unstack(fill_value=0)

    if g4 is not None and base_month in g4.columns and latest_month in g4.columns:
        g4['abs_change'] = g4[latest_month] - g4[base_month]
        inc = g4[g4['abs_change'] > 0].sort_values('abs_change', ascending=False)
        dec = g4[g4['abs_change'] < 0].sort_values('abs_change', ascending=True)

        # Pick top 3 drivers each side (if available)
        top_inc = inc.head(3)
        top_dec = dec.head(3)

        def _parts(df_part, verb="+"):
            items = []
            for idx, row in df_part.iterrows():
                items.append(f"**{idx}** ({verb}${_fmt_mn(abs(float(row['abs_change'])))} mn)")
            return items

        ups = _parts(top_inc, "+")
        downs = _parts(top_dec, "−")

        # Compose narrative
        if ups and downs:
            story = (
                f"Key drivers of the net change were increases in "
                f"{', '.join(ups)}; partially offset by reductions in {', '.join(downs)}."
            )
        elif ups:
            story = f"Cost increase was primarily driven by {', '.join(ups)}."
        elif downs:
            story = f"Cost decrease was primarily driven by {', '.join(downs)}."

    # ---------- Present Insights ----------
    st.markdown(f"### 🧭 Cost Insights — **{segment}**")
    st.markdown(f"- {overall_line}")

    if trend_lines:
        st.markdown("**3-month trend**")
        for tl in trend_lines:
            st.markdown(tl)

    st.markdown(f"**Key cost drivers** — {story}")

    # ---------- Keep existing margin/summary logic (not displayed now but kept if you extend) ----------
    # Client-level matrices (retained from original for compatibility with any downstream use)
    revenue_m = pd.DataFrame()
    cost_m = pd.DataFrame()
    if not revenue_df.empty:
        revenue_m = revenue_df.groupby(['Client', 'Month'])['Amount'].sum().unstack(fill_value=0)
    if not cost_df.empty:
        cost_m = cost_df.groupby(['Client', 'Month'])['Amount'].sum().unstack(fill_value=0)

    # ---------- Existing Top 8 Group4 cost increases table (preserved) ----------
    # We compare prev_month -> latest_month for this view (as in the original)
    group4_df_table = cost_df[['Month', 'Client', 'Amount', 'Group4']].dropna(subset=['Group4']).copy()
    g4_tbl = group4_df_table.groupby(['Group4', 'Month'])['Amount'].sum().unstack(fill_value=0)

    # If we lack either month, we still try to show a table if possible; otherwise warn and exit gracefully
    if prev_month not in g4_tbl.columns or latest_month not in g4_tbl.columns:
        st.warning("Missing Group4 cost data for one of the comparison months used in the table.")
        return

    g4_raw = g4_tbl.copy()
    # % change vs tiny epsilon to avoid div-by-zero
    g4_tbl['% Change'] = ((g4_raw[latest_month] - g4_raw[prev_month]) /
                          g4_raw[prev_month].replace(0, 0.0001)) * 100
    g4_raw['abs_change'] = (g4_raw[latest_month] - g4_raw[prev_month])

    g4_positive_increase = g4_raw[g4_raw['abs_change'] > 0].copy()
    top8 = g4_positive_increase.sort_values(by='abs_change', ascending=False).head(8)

    table_df = pd.DataFrame({
        f'{prev_month.strftime("%b")} (Mn USD)': top8[prev_month] / 1e6,
        f'{latest_month.strftime("%b")} (Mn USD)': top8[latest_month] / 1e6,
        '% Change': g4_tbl.loc[top8.index, '% Change']
    }, index=top8.index)
    table_df.index.name = 'Group4'

    # Formatting
    table_df[f'{prev_month.strftime("%b")} (Mn USD)'] = table_df[f'{prev_month.strftime("%b")} (Mn USD)'].map(lambda x: f"{x:,.2f}")
    table_df[f'{latest_month.strftime("%b")} (Mn USD)'] = table_df[f'{latest_month.strftime("%b")} (Mn USD)'].map(lambda x: f"{x:,.2f}")
    table_df['% Change'] = table_df['% Change'].map(lambda x: f"{x:.2f}%")

    st.markdown(
        f"### 📊 Top 8 Group4 Cost Increases "
        f"(actual cost in Mn USD, % change from {prev_month.strftime('%b')} to {latest_month.strftime('%b')})"
    )
    st.dataframe(table_df)
