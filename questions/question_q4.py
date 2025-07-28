# ✅ FINAL Q4 CODE: Enhanced visuals + DU/BU breakdown + clean charts
import pandas as pd
import matplotlib.pyplot as plt

def run(df, user_question=None):
    import streamlit as st
    from io import BytesIO
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor

    df.columns = df.columns.str.strip()

    # 🔍 Detect amount field
    amount_col = next((col for col in df.columns if col.lower().strip() in ['amount', 'amount in usd', 'amountinusd']), None)
    if not amount_col:
        st.error("❌ Column not found: Amount in USD")
        return

    # ✅ Add BU and DU
    df['DU'] = df.get('Exec DU', 'Unknown')
    df['BU'] = df.get('Exec DG', 'Unknown')

    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])

    df_cb = df[df['Group3'].str.contains('C&B', na=False)]
    df_rev = df[df['Type'].str.lower() == 'revenue']

    # 🕒 Frequency Toggle
    freq_option = st.radio("Choose trend frequency", ['MoM', 'QoQ', 'YoY'], horizontal=True)

    if freq_option == 'MoM':
        period = df['Month'].dt.to_period('M')
        title_str = "MoM Revenue vs C&B % of Revenue"
        cb_label = "MoM C&B Change (%)"
        rev_label = "MoM Revenue Change (%)"
        slide_title = "C&B MoM Trend Summary"
    elif freq_option == 'QoQ':
        period = df['Month'].dt.to_period('Q')
        title_str = "QoQ Revenue vs C&B % of Revenue"
        cb_label = "QoQ C&B Change (%)"
        rev_label = "QoQ Revenue Change (%)"
        slide_title = "C&B QoQ Trend Summary"
    else:
        period = df['Month'].dt.to_period('Y')
        title_str = "YoY Revenue vs C&B % of Revenue"
        cb_label = "YoY C&B Change (%)"
        rev_label = "YoY Revenue Change (%)"
        slide_title = "C&B YoY Trend Summary"

    cb_agg = df_cb.groupby(period)[amount_col].sum()
    rev_agg = df_rev.groupby(period)[amount_col].sum()

    df_summary = pd.DataFrame({
        'C&B (Million USD)': cb_agg / 1e6,
        'Revenue (Million USD)': rev_agg / 1e6
    }).dropna()

    df_summary['C&B % of Revenue'] = (df_summary['C&B (Million USD)'] / df_summary['Revenue (Million USD)']) * 100
    df_summary[cb_label] = df_summary['C&B (Million USD)'].pct_change() * 100
    df_summary[rev_label] = df_summary['Revenue (Million USD)'].pct_change() * 100
    df_summary = df_summary.round(2)

    # 🔎 Segment margin drop analysis
    segment_insights = []
    if freq_option == 'MoM':
        latest_month = df['Month'].max()
        prev_month = (latest_month - pd.DateOffset(months=1)).replace(day=1)

        df_latest = df[df['Month'].dt.to_period('M') == latest_month.to_period('M')]
        df_prev = df[df['Month'].dt.to_period('M') == prev_month.to_period('M')]

        def margin_calc(sub_df):
            rev = sub_df[sub_df['Type'].str.lower() == 'revenue'][amount_col].sum()
            cost = sub_df[sub_df['Type'].str.lower() == 'cost'][amount_col].sum()
            return ((rev - cost) / cost * 100) if cost else 0

        for seg in df['Segment'].dropna().unique():
            margin_now = margin_calc(df_latest[df_latest['Segment'] == seg])
            margin_prev = margin_calc(df_prev[df_prev['Segment'] == seg])
            cb_now = df_cb[(df_cb['Segment'] == seg) & (df_cb['Month'].dt.to_period('M') == latest_month.to_period('M'))][amount_col].sum()
            cb_prev = df_cb[(df_cb['Segment'] == seg) & (df_cb['Month'].dt.to_period('M') == prev_month.to_period('M'))][amount_col].sum()

            if cb_now > cb_prev and margin_now < margin_prev:
                segment_insights.append(
                    f"**{seg}**: Margin% dropped from {margin_prev:.1f}% to {margin_now:.1f}% and C&B rose from ${cb_prev/1e6:.1f}M to ${cb_now/1e6:.1f}M"
                )

    # 📊 Summary Block
    st.markdown(f"### 📊 {title_str}")
    if df_summary.shape[0] >= 2:
        last, prev = df_summary.index[-1], df_summary.index[-2]
        cb_chg = df_summary.loc[last, cb_label]
        rev_chg = df_summary.loc[last, rev_label]
        st.markdown(
            f"📌 In **{last}**, C&B cost changed by **{cb_chg:+.1f}%** while revenue changed by **{rev_chg:+.1f}%** vs **{prev}**."
        )
        if segment_insights:
            st.markdown("🔍 Segments with margin drop and C&B increase:")
            for insight in segment_insights:
                st.markdown(f"- {insight}")

    # 📈 Summary Table and Chart
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df_summary.reset_index().rename(columns={'Month': 'Period'}), hide_index=True)

    with col2:
        fig, ax1 = plt.subplots(figsize=(6.5, 4))
        df_summary_plot = df_summary.copy()
        df_summary_plot.index = df_summary_plot.index.to_timestamp()

        ax1.bar(df_summary_plot.index, df_summary_plot['Revenue (Million USD)'],
                width=20, color='#FFFACD')  # pastel yellow
        ax1.set_ylabel("Revenue (Million USD)", color='gray')

        ax2 = ax1.twinx()
        ax2.plot(df_summary_plot.index, df_summary_plot['C&B % of Revenue'],
                 color='#87CEFA', marker='o', linewidth=1.2, linestyle='-', alpha=0.9)
        ax2.set_ylabel("C&B % of Revenue", color='gray')

        for spine in ax1.spines.values():
            spine.set_color('lightgray')
        for spine in ax2.spines.values():
            spine.set_color('lightgray')

        ax1.grid(False)
        ax2.grid(False)
        fig.tight_layout()
        st.pyplot(fig)

    # 🧾 BU/DU Revenue Tables
    st.markdown("### 🧾 Revenue Breakdown by BU and DU")
    df_rev['Period'] = period
    pivot_bu = pd.pivot_table(df_rev, index='Period', columns='BU', values=amount_col, aggfunc='sum').fillna(0) / 1e6
    pivot_du = pd.pivot_table(df_rev, index='Period', columns='DU', values=amount_col, aggfunc='sum').fillna(0) / 1e6

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### Revenue by BU (Million USD)")
        st.dataframe(pivot_bu.round(1).reset_index())
    with col4:
        st.markdown("#### Revenue by DU (Million USD)")
        st.dataframe(pivot_du.round(1).reset_index())

    # 📈 BU Chart
    st.markdown("### 📈 Revenue Trend by BU and DU")
    fig_bu, ax_bu = plt.subplots()
    for col in pivot_bu.columns:
        ax_bu.plot(pivot_bu.index.to_timestamp(), pivot_bu[col], label=col, linewidth=1.2)
    ax_bu.set_title("BU Revenue Trend")
    ax_bu.set_ylabel("Revenue (M USD)")
    for spine in ax_bu.spines.values():
        spine.set_color('lightgray')
    ax_bu.grid(False)
    ax_bu.legend(fontsize=6)
    st.pyplot(fig_bu)

    # 📈 DU Chart moved to new row with bottom legend
    fig_du, ax_du = plt.subplots()
    for col in pivot_du.columns:
        ax_du.plot(pivot_du.index.to_timestamp(), pivot_du[col], label=col, linewidth=1.2)
    ax_du.set_title("DU Revenue Trend")
    ax_du.set_ylabel("Revenue (M USD)")
    for spine in ax_du.spines.values():
        spine.set_color('lightgray')
    ax_du.grid(False)
    ax_du.legend(fontsize=6, loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=3)
    fig_du.tight_layout()
    st.pyplot(fig_du)

    # 📤 PPT Export
    if st.button("📥 Download as PPT"):
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.title.text = slide_title

        content = f"In {last}, C&B changed by {cb_chg:+.1f}% and Revenue by {rev_chg:+.1f}% vs {prev}.\n"
        if segment_insights:
            content += "Segments with margin drop:\n" + "\n".join(i.replace("**", "") for i in segment_insights)

        textbox = slide.shapes.add_textbox(Inches(0.5), Inches(1), Inches(8), Inches(2))
        tf = textbox.text_frame
        tf.text = content
        tf.paragraphs[0].font.size = Pt(14)

        img_stream = BytesIO()
        fig.savefig(img_stream, format='png')
        img_stream.seek(0)
        slide.shapes.add_picture(img_stream, Inches(1), Inches(3), Inches(7), Inches(3.5))

        output = BytesIO()
        prs.save(output)
        st.download_button("Download PPT", data=output.getvalue(), file_name="C&B_Trend_Summary.pptx")
