# ✅ FINAL Q4 CODE: Cleaned up DU/BU charts, added smooth lines and lighter visuals
import pandas as pd
import matplotlib.pyplot as plt

def run(df, user_question=None):
    import streamlit as st
    from io import BytesIO
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from scipy.interpolate import make_interp_spline
    import numpy as np

    df.columns = df.columns.str.strip()

    amount_col = next((col for col in df.columns if col.lower().strip() in ['amount', 'amount in usd', 'amountinusd']), None)
    if not amount_col:
        st.error("❌ Column not found: Amount in USD")
        return

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

    # 📊 Summary Block
    st.markdown(f"### 📊 {title_str}")
    if df_summary.shape[0] >= 2:
        last, prev = df_summary.index[-1], df_summary.index[-2]
        cb_chg = df_summary.loc[last, cb_label]
        rev_chg = df_summary.loc[last, rev_label]
        st.markdown(
            f"📌 In **{last}**, C&B cost changed by **{cb_chg:+.1f}%** while revenue changed by **{rev_chg:+.1f}%** vs **{prev}**."
        )

    # 📈 Summary Table and Chart
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df_summary.reset_index().rename(columns={'Month': 'Period'}), hide_index=True)

    with col2:
        fig, ax1 = plt.subplots(figsize=(6.5, 4))
        df_summary_plot = df_summary.copy()
        df_summary_plot.index = df_summary_plot.index.to_timestamp()

        ax1.bar(df_summary_plot.index, df_summary_plot['Revenue (Million USD)'], width=20, color='#FFFACD')
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

    # 📈 Revenue Trend Charts (cleaned up)
    st.markdown("## 📈 Revenue Trend by BU and DU")

    def plot_group_trend(pivot_df, group_name, ax, smooth=True):
        periods = pivot_df.index.astype(str).tolist()
        x = np.arange(len(periods))

        for col in pivot_df.columns:
            y = pivot_df[col].values
            if smooth and len(x) >= 4:
                try:
                    xnew = np.linspace(x.min(), x.max(), 300)
                    spl = make_interp_spline(x, y, k=2)
                    y_smooth = spl(xnew)
                    ax.plot(xnew, y_smooth, label=col, linewidth=1)
                except Exception:
                    ax.plot(x, y, label=col, linewidth=1)
            else:
                ax.plot(x, y, label=col, linewidth=1)

        ax.set_xticks(x)
        ax.set_xticklabels(periods, rotation=45)
        ax.set_title(f"{group_name} Revenue Trend", fontsize=14)
        ax.set_ylabel("Revenue (M USD)", fontsize=12)
        ax.set_facecolor("#fffef6")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
            spine.set_color("lightgrey")
        ax.tick_params(axis='both', labelsize=10)

    # BU Chart
    fig_bu, ax_bu = plt.subplots(figsize=(10, 3.5))
    plot_group_trend(pivot_bu, "BU", ax_bu)
    ax_bu.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=3, fontsize=7.5, frameon=False)
    fig_bu.tight_layout()
    st.pyplot(fig_bu)

    # DU Chart
    fig_du, ax_du = plt.subplots(figsize=(10, 3.5))
    plot_group_trend(pivot_du, "DU", ax_du)
    ax_du.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=4, fontsize=7.5, frameon=False)
    fig_du.tight_layout()
    st.pyplot(fig_du)

    # 📤 PPT Export
    if st.button("📥 Download as PPT"):
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.title.text = slide_title

        content = f"In {last}, C&B changed by {cb_chg:+.1f}% and Revenue by {rev_chg:+.1f}% vs {prev}."
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
