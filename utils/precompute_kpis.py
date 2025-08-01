import os
import pandas as pd
import sys

# Ensure repo root is on sys.path so imports from kpi_engine work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kpi_engine.revenue_aggregated import get_revenue_aggregated
from kpi_engine.net_available_hours_aggregated import get_net_available_hours_aggregated
from kpi_engine.headcount import get_headcount_data
from kpi_engine.realized_rate import get_realized_rate_data
from kpi_engine.revenue_per_person import get_revenue_per_person_data

# Input paths from GitHub repo structure
revenue_input_path = "sample_data/LnTPnL.xlsx"
ut_input_path = "sample_data/LNTData.xlsx"

# Output folder path
precomputed_dir = "sample_data/precomputed"
os.makedirs(precomputed_dir, exist_ok=True)

# Load data
df_pnl = pd.read_excel(revenue_input_path)
df_ut = pd.read_excel(ut_input_path)

# Precompute and save revenue
df_revenue = get_revenue_aggregated(df_pnl, df_ut)
df_revenue.to_csv(os.path.join(precomputed_dir, "revenue.csv"), index=False)
print("✅ Precomputed revenue.csv saved.")

# Precompute and save net available hours
df_net_hours = get_net_available_hours_aggregated(df_ut)
df_net_hours.to_csv(os.path.join(precomputed_dir, "netavailablehours.csv"), index=False)
print("✅ Precomputed netavailablehours.csv saved.")

# Precompute and save headcount
df_headcount = get_headcount_data(df_ut)
df_headcount.to_csv(os.path.join(precomputed_dir, "headcount.csv"), index=False)
print("✅ Precomputed headcount.csv saved.")

# Precompute and save realized rate
df_realized = get_realized_rate_data(df_pnl, df_ut)
df_realized.to_csv(os.path.join(precomputed_dir, "realized_rate.csv"), index=False)
print("✅ Precomputed realized_rate.csv saved.")

# Precompute and save revenue per person
df_rpp = get_revenue_per_person_data(df_pnl, df_ut)
df_rpp.to_csv(os.path.join(precomputed_dir, "revenue_per_person.csv"), index=False)
print("✅ Precomputed revenue_per_person.csv saved.")

print("🎉 All KPI precomputations completed successfully.")
