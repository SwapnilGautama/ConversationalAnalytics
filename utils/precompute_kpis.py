import os
import pandas as pd
from kpi_engine.revenue_aggregated import get_revenue_aggregated
from kpi_engine.net_available_hours_aggregated import get_net_available_hours_aggregated

# Input paths (from GitHub repo structure)
revenue_input_path = "sample_data/LnTPnL.xlsx"
ut_input_path = "sample_data/LNTData.xlsx"

# Output folder path
precomputed_dir = "sample_data/precomputed"
os.makedirs(precomputed_dir, exist_ok=True)

# Precompute revenue
df_revenue = get_revenue_aggregated(revenue_input_path)
df_revenue.to_csv(os.path.join(precomputed_dir, "revenue.csv"), index=False)
print("✅ Precomputed revenue.csv saved.")

# Precompute Net Available Hours
df_net_hours = get_net_available_hours_aggregated(ut_input_path)
df_net_hours.to_csv(os.path.join(precomputed_dir, "netavailablehours.csv"), index=False)
print("✅ Precomputed netavailablehours.csv saved.")
