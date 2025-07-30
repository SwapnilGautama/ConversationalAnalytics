import streamlit as st
import pandas as pd

st.markdown("## Q6. Realized Rate Analysis")

# --- Sidebar filters: captured but used inside run() ---
with st.sidebar:
    st.markdown("### 🛠️ Filters")
    segment_filter = st.text_input("Enter Segment (optional)", value="")
    realized_rate_threshold = st.slider("Realized Rate Threshold", min_value=0.0, max_value=50.0, value=5.0, step=0.5)

# --- Analysis logic ---
def run(df_pnl, df_ut):
    # --- Filter PnL for Revenue only ---
    revenue_df = df_pnl[df_pnl['Type'] == 'Revenue']
    revenue_agg = revenue_df.groupby('Company_Code')['Amount in USD'].sum().reset_index()
    revenue_agg.rename(columns={'Amount in USD': 'Revenue (USD)'}, inplace=True)

    # --- Filter UT based on sidebar input ---
    if segment_filter:
        df_ut = df_ut[df_ut['Segment'] == segment_filter]

    ut_agg = df_ut.groupby('Company_Code')['NetAvailableHours'].sum().reset_index()

    # --- Merge ---
    merged = pd.merge(revenue_agg, ut_agg, on='Company_Code', how='inner')
    merged['Realized Rate'] = merged['Revenue (USD)'] / merged['NetAvailableHours']
    merged = merged.round({'Realized Rate': 2})

    below_threshold = merged[merged['Realized Rate'] < realized_rate_threshold]

    if below_threshold.empty:
        st.success("✅ All accounts are above the threshold.")
    else:
        st.warning("⚠️ The following accounts are below the threshold:")
        st.dataframe(below_threshold[['Company_Code', 'Realized Rate']], use_container_width=True)

# --- Run with error handling ---
try:
    run(df_pnl, df_ut)
except Exception as e:
    st.error(f"❌ Error running analysis: {e}")
