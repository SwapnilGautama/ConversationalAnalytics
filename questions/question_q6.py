import pandas as pd
import streamlit as st
import os
import sys

# === Load realized rate KPI from kpi_engine folder ===
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from kpi_engine.realized_rate import calculate_realized_rate

def run(_, user_question=None):
    st.markdown("### 🔍 Accounts with Realized Rate below Threshold")

    # === 📁 Load Data ===
    try:
        df_pnl = pd.read_excel("data/LnTPnL.xlsx", sheet_name="LnTPnL")
        df_ut = pd.read_excel("data/LNTData.xlsx", sheet_name="LNTData")
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return

    # === 🧹 Clean + Enrich ===
    for df in [df_pnl, df_ut]:
        df.columns = df.columns.str.strip()

    # Handle Month → Quarter conversion
    for df in [df_pnl, df_ut]:
        if 'Month' in df.columns:
            df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
            df['Quarter'] = df['Month'].dt.to_period('Q').astype(str)
        else:
            st.error("❌ 'Month' column not found in one of the datasets.")
            return

    # === 🔎 Sidebar Filters ===
    segments = sorted(set(df_ut['Segment'].dropna().unique()))
    default_segment = segments[0] if segments else None
    selected_segment = st.sidebar.selectbox("📍 Select Segment", options=segments, index=0 if default_segment else None)

    threshold = st.sidebar.slider("🎯 Realized Rate Threshold (USD/hr)", min_value=0.0, max_value=100.0, value=30.0, step=1.0)

    # === 📊 Calculate Realized Rate ===
    try:
        result = calculate_realized_rate(df_pnl, df_ut, segment=selected_segment)
        if result.empty:
            st.warning("⚠️ No matching data found for the selected filters.")
            return

        # Filter by threshold
        below_threshold = result[result['RealizedRate'] < threshold]
        below_threshold = below_threshold.sort_values(by='RealizedRate')

        if below_threshold.empty:
            st.success("✅ No accounts found below the selected threshold!")
            return

        st.markdown(f"### 📉 Accounts in '{selected_segment}' with Realized Rate < {threshold}")
        st.dataframe(below_threshold[['FinalCustomerName', 'Quarter', 'RealizedRate']].round(2), hide_index=True)

    except Exception as e:
        st.error(f"❌ Error calculating realized rate: {e}")
