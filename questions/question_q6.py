import pandas as pd
import streamlit as st
from kpi_engine.realized_rate import calculate_realized_rate

def run(pnl_df: pd.DataFrame, ut_df: pd.DataFrame):
    st.subheader("Q6. Realized Rate Analysis")

    with st.sidebar:
        st.markdown("### 🛠️ Filters")
        segment = st.selectbox("Select Segment (optional)", options=[''] + sorted(pnl_df['Segment'].dropna().unique()))
        threshold = st.slider("Realized Rate Threshold", min_value=0.0, max_value=50.0, value=5.0, step=0.5)

    # Compute realized rate using existing KPI engine
    realized_df = calculate_realized_rate(pnl_df, ut_df, segment=segment if segment else None)

    # Filter accounts below threshold
    below_threshold = realized_df[realized_df['RealizedRate'] < threshold].copy()

    if below_threshold.empty:
        st.success("✅ No accounts found with Realized Rate below the selected threshold.")
    else:
        st.warning(f"⚠️ {len(below_threshold)} accounts found with Realized Rate below {threshold}")
        st.dataframe(
            below_threshold.style.format({
                'Revenue': '{:,.0f}',
                'AvailableHrs': '{:,.0f}',
                'RealizedRate': '{:.2f}'
            })
        )
