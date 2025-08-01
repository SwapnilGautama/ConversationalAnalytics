import os
import pandas as pd

from kpi_engine.revenue_aggregated import get_revenue_aggregated
from kpi_engine.net_available_hours_aggregated import get_net_available_hours_aggregated

# Define input paths
PNL_FILE = "sample_data/LnTPnL.xlsx"
UT_FILE = "sample_data/LNTData.xlsx"

# Define output folder
OUTPUT_FOLDER = "sample_data/precomputed"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def precompute_all_kpis():
    print("Starting KPI precomputation...")

    # Compute Revenue Aggregated
    print("Computing revenue_aggregated...")
    df_revenue = get_revenue_aggregated(PNL_FILE)
    revenue_outfile = os.path.join(OUTPUT_FOLDER, "revenue_aggregated.csv")
    df_revenue.to_csv(revenue_outfile, index=False)
    print(f"✅ Saved: {revenue_outfile}")

    # Compute Net Available Hours Aggregated
    print("Computing netavailablehours_aggregated...")
    df_hours = get_net_available_hours_aggregated(UT_FILE)
    hours_outfile = os.path.join(OUTPUT_FOLDER, "netavailablehours_aggregated.csv")
    df_hours.to_csv(hours_outfile, index=False)
    print(f"✅ Saved: {hours_outfile}")

    print("✅ All precomputations completed successfully.")

# Run when executed directly
if __name__ == "__main__":
    precompute_all_kpis()
