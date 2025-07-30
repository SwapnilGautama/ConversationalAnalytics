import pandas as pd
import streamlit as st
import re

from kpi_engine.realized_rate import calculate_realized_rate

def run(pnl_df: pd.DataFrame, ut_df: pd.DataFrame, user_question: str = ""):
    st.markdown("## Q6. Realized Rate Analysis")

    # 🧠 Extract segment from chatbot question (like q4.py)
    segment_match = re.search(r"\b(?:in|for)?\s*(Transportation|Med Tech|Media & Technology|Plant Engineering|Industrial Products)\b", user_question or "", re.IGNORECASE)
    segment_filter = segment_match.group(1) if segment_match else None

    # 🎛️ Sidebar Filters
    with st.sidebar:
        st.markdown("### 🛠️ Filters")
        segment_input = st.selectbox("Select Segment (optional)", options=[""] + sorted(pnl_df['Segment'].dropna().unique().tolist()))
        segment = segment_input if segment_input else segment_filter
        threshold = st.slider("Realized Rate Threshold", min_value=0.0, max_value=50.0, value=5.0, step=0.5)

    # 🧮 Ensure column existence like q4.py
    pnl_df.columns = pnl_df.columns.str.strip()
    ut_df.columns = ut_df.columns.str.strip()

    amount_col = next((col for col in pnl_df.columns if col.lower() in ["amount", "amount in usd", "amountinusd"]), None)
    if not amount_col:
        st.error("❌ Column not found: Amount in USD")
        return

    # Rename dynamically to expected name
    pnl_df = pnl_df.rename(columns={amount_col: "Amount in USD"})

    # ✅ Run KPI
    result_df = calculate_realized_rate(pnl_df, ut_df, segment=segment)

    if result_df.empty:
        st.warning("⚠️ No data available after filters.")
        return

    below_threshold = result_df[result_df["RealizedRate"] < threshold].copy()

    st.markdown(f"### 📊 Accounts with Realized Rate below {threshold}")
    if below_threshold.empty:
        st.success("✅ No accounts found with Realized Rate below the selected threshold.")
    else:
        st.dataframe(
            below_threshold.style.format({
                "Revenue": "{:,.0f}",
                "AvailableHrs": "{:,.0f}",
                "RealizedRate": "{:.2f}"
            }),
            use_container_width=True
        )
