import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

def run(user_question: str):
    # Load data
    file_path = "sample_data/LNTData.xlsx"
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return

    # Identify actual BU/DU field names from q8 pattern
    bu_col = next((col for col in df.columns if "bu" in col.lower()), None)
    du_col = next((col for col in df.columns if "du" in col.lower()), None)

    # Validate required columns
    required_cols = ["FresherAgeingCategory", "Segment", "Month", "Utilization %", "Year", "Status"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if bu_col is None:
        missing_cols.append("BU")
    if du_col is None:
        missing_cols.append("DU")
    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
        return

    # Filter to Billable only
    df = df[df["Status"] == "Billable"]

    # Extract year as numeric
    df["Year"] = df["Year"].astype(str).str.extract(r"(\d{4})").astype(int)

    # Map numeric months to short names
    month_map = {i: name for i, name in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
    df["Month"] = df["Month"].map(month_map)

    # Group and pivot UT%
    agg_df = df.groupby(["Year", "Month", "FresherAgeingCategory"])["Utilization %"].mean().reset_index()
    agg_df = agg_df.sort_values(["Year", "Month"], key=lambda x: pd.Categorical(x, categories=month_map.values(), ordered=True))
    pivot_df = agg_df.pivot(index="Month", columns="FresherAgeingCategory", values="Utilization %")

    # Line Chart
    fig, ax = plt.subplots(figsize=(8, 4))
    pastel_palette = sns.color_palette("pastel")
    pivot_df.plot(ax=ax, linewidth=2.5, marker='o', color=pastel_palette)
    ax.set_title("UT% Trend by Fresher Category", fontsize=14)
    ax.set_ylabel("Utilization %")
    ax.set_xlabel("Month")
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    ax.set_facecolor("#FAFAFA")
    sns.despine()
    st.pyplot(fig)

    # Table
    styled_table = pivot_df.style.format("{:.1f}").set_table_styles([
        {'selector': 'thead th', 'props': [('background-color', '#f2f2f2'), ('border', '1px solid #ddd')]},
        {'selector': 'tbody td', 'props': [('border', '1px solid #ddd')]},
        {'selector': 'table', 'props': [('border-collapse', 'collapse')]}
    ])
    st.dataframe(styled_table, use_container_width=True)

    # Insights
    summary = []
    for category in pivot_df.columns:
        trend = pivot_df[category].dropna()
        if trend.empty:
            continue
        change = trend.iloc[-1] - trend.iloc[0]
        direction = "increased" if change > 0 else "decreased" if change < 0 else "remained stable"
        summary.append(f"• UT% for **{category}** has {direction} from **{trend.iloc[0]:.1f}%** to **{trend.iloc[-1]:.1f}%**.")
    if summary:
        st.markdown("### 📊 Key Insights")
        for point in summary:
            st.markdown(point)
    else:
        st.warning("No usable UT% data available for fresher buckets.")

