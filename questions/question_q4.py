# ✅ FINAL Q4 CODE (v19 with Bold Totals, Header Coloring, Rev-C&B Diff Highlighting)
import pandas as pd
import re

def run(df, user_question=None):
    import streamlit as st

    df.columns = df.columns.str.strip()

    amount_col = next((col for col in df.columns if col.lower().strip() in ['amount', 'amount in usd', 'amountinusd']), None)
    if not amount_col:
        st.error("❌ Column not found: Amount in USD")
        return

    # Extract Segment from chatbot prompt
    segment_match = re.search(r"\b(?:in|for)?\s*(Transportation|Med Tech|Media & Technology|Plant Engineering|Industrial Products)\b",
                              user_question or "", re.IGNORECASE)
    segment_filter = segment_match.group(1) if segment_match else None

    if segment_filter and 'Segment' in df.columns:
        df['Segment'] = df['Segment'].fillna('').str.strip()
        df = df[df['Segment'].str.lower() == segment_filter.lower()]

    df['DU'] = df.get('Exec DU', 'Unknown')
    df['BU'] = df.get('Exec DG', 'Unknown')
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])

    df_cb = df[df['Group3'].str.contains('C&B', na=False)]
    df_rev = df[df['Type'].str.lower() == 'revenue']

    freq_option = st.radio("Choose trend frequency", ['MoM', 'QoQ', 'YoY'], horizontal=True)

    if freq_option == 'MoM':
        period = df['Month'].dt.to_period('M')
        title_str = "MoM Revenue vs C&B % of Revenue"
        cb_label = "MoM C&B Change (%)"
        rev_label = "MoM Revenue Change (%)"
    elif freq_option == 'QoQ':
        period = df['Month'].dt.to_period('Q')
        title_str = "QoQ Revenue vs C&B % of Revenue"
        cb_label = "QoQ C&B Change (%)"
        rev_label = "QoQ Revenue Change (%)"
    else:
        period = df['Month'].dt.to_period('Y')
        title_str = "YoY Revenue vs C&B % of Revenue"
        cb_label = "YoY C&B Change (%)"
        rev_label = "YoY Revenue Change (%)"

    cb_agg = df_cb.groupby(period)[amount_col].sum()
    rev_agg = df_rev.groupby(period)[amount_col].sum()

    df_summary = pd.DataFrame({
        'C&B (Million USD)': cb_agg / 1e6,
        'Revenue (Million USD)': rev_agg / 1e6
    }).dropna()

    df_summary['C&B % of Revenue'] = (df_summary['C&B (Million USD)'] / df_summary['Revenue (Million USD)']) * 100
    df_summary[cb_label] = df_summary['C&B (Million USD)'].pct_change() * 100
    df_summary[rev_label] = df_summary['Revenue (Million USD)'].pct_change() * 100
    df_summary['Rev-C&B Movement Diff'] = df_summary[rev_label] - df_summary[cb_label]
    df_summary = df_summary.round(2)

    # 📊 Summary Block
    st.markdown(f"### 📊 {title_str}")
    if df_summary.shape[0] >= 2:
        last, prev = df_summary.index[-1], df_summary.index[-2]
        cb_chg = df_summary.loc[last, cb_label]
        rev_chg = df_summary.loc[last, rev_label]
        st.markdown(
            f"📌 In **{last}**, C&B cost changed by **{cb_chg:+.1f}%** while revenue changed by **{rev_chg:+.1f}%** vs **{prev}**."
        )

    # 📋 Summary Table
    st.markdown("### Summary Table")
    df_sum_display = df_summary.reset_index().rename(columns={'Month': 'Period'})

    total_cb = df_sum_display['C&B (Million USD)'].sum()
    total_rev = df_sum_display['Revenue (Million USD)'].sum()
    avg_cb_pct = (total_cb / total_rev) * 100 if total_rev else 0
    avg_cb_chg = df_sum_display[cb_label].mean()
    avg_rev_chg = df_sum_display[rev_label].mean()
    avg_diff = avg_rev_chg - avg_cb_chg

    total_row = {
        'Period': '**Total**',
        'C&B (Million USD)': f"**{total_cb:.2f}**",
        'Revenue (Million USD)': f"**{total_rev:.2f}**",
        'C&B % of Revenue': f"**{avg_cb_pct:.2f}**",
        cb_label: f"**{avg_cb_chg:.2f}**",
        rev_label: f"**{avg_rev_chg:.2f}**",
        'Rev-C&B Movement Diff': f"**{avg_diff:+.2f}**"
    }

    df_sum_display = pd.concat([df_sum_display, pd.DataFrame([total_row])], ignore_index=True)

    def highlight_diff(val):
        if isinstance(val, str) and val.startswith("**"):
            try:
                num = float(val.strip("*").replace("+", ""))
                color = 'green' if num > 0 else 'red'
                return f'color: {color}; font-weight: bold'
            except:
                return ''
        return ''

    pastel_colors = ['#dceefb', '#fcefe3', '#e7f5e6']  # pastel blue, peach, green
    header_styles = [f"background-color: {color}; font-weight: bold;" for color in pastel_colors]

    def style_summary_table(df):
        styler = df.style
        for i, style in enumerate(header_styles):
            if i < len(df.columns):
                styler = styler.set_table_styles([{ 'selector': f'th.col{i}', 'props': style.split('; ') }], overwrite=False)
        styler = styler.applymap(highlight_diff, subset=['Rev-C&B Movement Diff'])
        return styler

    st.dataframe(style_summary_table(df_sum_display), hide_index=True)

    # 🧾 BU/DU Revenue Tables
    st.markdown("### 🧾 Revenue Breakdown by BU and DU")
    df_rev['Period'] = period

    pivot_bu = pd.pivot_table(df_rev, index='Period', columns='BU', values=amount_col, aggfunc='sum').fillna(0) / 1e6
    pivot_bu.loc['Total'] = pivot_bu.sum()
    st.markdown("#### Revenue by BU (Million USD)")
    st.dataframe(pivot_bu.round(1).reset_index())

    pivot_du = pd.pivot_table(df_rev, index='Period', columns='DU', values=amount_col, aggfunc='sum').fillna(0) / 1e6
    pivot_du.loc['Total'] = pivot_du.sum()
    st.markdown("#### Revenue by DU (Million USD)")
    st.dataframe(pivot_du.round(1).reset_index())
