# ✅ FINAL Q4 CODE: Revenue and C&B logic enhanced + formatting improvements
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

    # ✅ Revenue Logic: Filter Group1
    df_rev = df[df['Group1'].isin(['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE'])]

    # ✅ C&B Logic: Filter Group Description
    cb_keywords = [
        "Onsite Salaries & Allowances", "Cost of Onsite TPCs/Retainers",
        "C&B Cost Offshore", "Professional Fee - Retainers/TPC"
    ]
    df_cb = df[df['Group Description'].isin(cb_keywords)]

    # === Main Tabs ===
    trend_tabs = st.tabs(["📈 MoM", "📊 QoQ", "📉 YoY"])

    for i, freq_option in enumerate(['MoM', 'QoQ', 'YoY']):
        with trend_tabs[i]:
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
            df_summary = df_summary.round(1)

            # 📊 Trend Summary Header
            st.markdown(f"### 📊 {title_str}")
            if df_summary.shape[0] >= 2:
                last, prev = df_summary.index[-1], df_summary.index[-2]
                cb_chg = df_summary.loc[last, cb_label]
                rev_chg = df_summary.loc[last, rev_label]
                st.markdown(
                    f"📌 In **{last}**, C&B cost changed by **{cb_chg:+.1f}%** while revenue changed by **{rev_chg:+.1f}%** vs **{prev}**."
                )

            # === Sub-tabs ===
            sub_tabs = st.tabs(["📋 Summary Table", "🏢 Revenue by BU", "🏭 Revenue by DU", "🚛 Revenue by Segment"])

            with sub_tabs[0]:
                df_sum_display = df_summary.reset_index().rename(columns={'Month': 'Period'})
                total_cb = df_sum_display['C&B (Million USD)'].sum()
                total_rev = df_sum_display['Revenue (Million USD)'].sum()
                avg_cb_pct = (total_cb / total_rev) * 100 if total_rev else 0
                avg_cb_chg = df_sum_display[cb_label].mean()
                avg_rev_chg = df_sum_display[rev_label].mean()
                avg_diff = avg_rev_chg - avg_cb_chg

                total_row = {
                    'Period': '**Total**',
                    'C&B (Million USD)': f"**{total_cb:.1f}**",
                    'Revenue (Million USD)': f"**{total_rev:.1f}**",
                    'C&B % of Revenue': f"**{avg_cb_pct:.1f}**",
                    cb_label: f"**{avg_cb_chg:.1f}**",
                    rev_label: f"**{avg_rev_chg:.1f}**",
                    'Rev-C&B Movement Diff': f"**{avg_diff:+.1f}**"
                }

                df_sum_display = pd.concat([df_sum_display, pd.DataFrame([total_row])], ignore_index=True)

                def highlight_diff(val):
                    try:
                        val = float(str(val).replace('**', ''))
                        color = 'red' if val < 0 else 'black'
                        return f'color: {color}'
                    except:
                        return ''

                styled_df = df_sum_display.style.applymap(highlight_diff, subset=['Rev-C&B Movement Diff'])

                st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Pivot table function (reuse for DU/BU/Segment)
            def pivot_and_display(group_field, label):
                df_rev['Period'] = period
                pivot_df = pd.pivot_table(df_rev, index=group_field, columns='Period', values=amount_col, aggfunc='sum').fillna(0) / 1e6
                pivot_df.loc['Total'] = pivot_df.sum()
                st.markdown(f"#### Revenue by {label} (Million USD)")
                st.dataframe(pivot_df.round(1).reset_index())

            with sub_tabs[1]:
                pivot_and_display('BU', 'BU')

            with sub_tabs[2]:
                pivot_and_display('DU', 'DU')

            with sub_tabs[3]:
                pivot_and_display('Segment', 'Segment')
