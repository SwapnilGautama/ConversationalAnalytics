
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

def run(input_text):
    try:
        # Load data
        df = pd.read_excel("Sample_Data/LnTPnL.xlsx", sheet_name=0)

        # Clean and prepare
        df["Month"] = pd.to_datetime(df["Month"])
        df["Amount in INR"] = pd.to_numeric(df["Amount in INR"], errors="coerce")
        df = df[df["Type"].isin(["Revenue", "Cost"])]
        df = df[df["Segment"].notna()]
        df["MonthStr"] = df["Month"].dt.strftime("%b-%Y")

        # Infer latest and previous month
        months = sorted(df["Month"].unique())
        latest_month = months[-1]
        prev_month = months[-2]

        # Extract segment from input
        matched_segment = next((seg for seg in df["Segment"].unique() if seg.lower() in input_text.lower()), None)
        if not matched_segment:
            return "No matching segment found in the input."

        # Filter for the segment
        df = df[df["Segment"] == matched_segment]

        # Revenue & Cost summaries
        df_summary = df[df["Month"].isin([latest_month, prev_month])]
        summary = df_summary.groupby(["Month", "Type"])["Amount in INR"].sum().unstack().fillna(0)
        summary["Margin %"] = ((summary["Revenue"] - summary["Cost"]) / summary["Cost"]) * 100
        margin_latest = summary.loc[latest_month, "Margin %"]
        margin_prev = summary.loc[prev_month, "Margin %"]
        margin_diff = margin_latest - margin_prev

        rev_change = ((summary.loc[latest_month, "Revenue"] - summary.loc[prev_month, "Revenue"]) / summary.loc[prev_month, "Revenue"]) * 100
        cost_change = ((summary.loc[latest_month, "Cost"] - summary.loc[prev_month, "Cost"]) / summary.loc[prev_month, "Cost"]) * 100

        # Clients with margin drop
        df_rev = df[df["Type"] == "Revenue"].groupby(["Company_Code", "Month"])["Amount in INR"].sum().unstack().fillna(0)
        df_cost = df[df["Type"] == "Cost"].groupby(["Company_Code", "Month"])["Amount in INR"].sum().unstack().fillna(0)

        margin_df = pd.DataFrame()
        margin_df["Revenue_Prev"] = df_rev[prev_month]
        margin_df["Revenue_Latest"] = df_rev[latest_month]
        margin_df["Cost_Prev"] = df_cost[prev_month]
        margin_df["Cost_Latest"] = df_cost[latest_month]
        margin_df["Margin % Prev"] = (margin_df["Revenue_Prev"] - margin_df["Cost_Prev"]) / margin_df["Cost_Prev"] * 100
        margin_df["Margin % Latest"] = (margin_df["Revenue_Latest"] - margin_df["Cost_Latest"]) / margin_df["Cost_Latest"] * 100
        margin_df["Margin Drop %"] = margin_df["Margin % Latest"] - margin_df["Margin % Prev"]
        margin_df = margin_df.dropna()
        margin_drop_clients = margin_df[margin_df["Margin Drop %"] < 0]

        segment_health = f"{len(margin_drop_clients)} out of {len(margin_df)} clients in {matched_segment} saw a margin decline"

        # Group4 cost increase
        g4 = df[df["Group4"].notna() & df["Type"].eq("Cost")]
        g4_summary = g4.groupby(["Group4", "Month"])["Amount in INR"].sum().unstack().fillna(0)
        g4_summary = g4_summary[[prev_month, latest_month]]
        g4_summary["% Change"] = ((g4_summary[latest_month] - g4_summary[prev_month]) / g4_summary[prev_month].replace(0, 1)) * 100
        g4_summary = g4_summary.sort_values("% Change", ascending=False).head(8)
        g4_summary = g4_summary / 1e7  # Convert to INR crores
        g4_summary = g4_summary.round(2)

        # Build plot
        fig, ax = plt.subplots(figsize=(10, 5))
        g4_summary[[prev_month, latest_month]].plot(kind="bar", ax=ax)
        ax.set_title("Top Group4 Cost Increases (INR Cr)")
        ax.set_ylabel("INR (Cr)")
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close(fig)
        b64 = base64.b64encode(buf.getvalue()).decode()

        # Prepare response
        insights = f"""
        - 📉 Margin for **{matched_segment}** dropped from {margin_prev:.2f}% in {prev_month.strftime('%b')} to {margin_latest:.2f}% in {latest_month.strftime('%b')} ({margin_diff:.2f}% change)
        - ⚠️ {segment_health}
        - 💰 Overall Cost in {matched_segment} increased by {cost_change:.2f}%, Revenue changed by {rev_change:.2f}%
        """

        return {
            "insights": insights,
            "table": g4_summary.reset_index().rename(columns={prev_month: prev_month.strftime('%b'), latest_month: latest_month.strftime('%b')}).to_dict(orient="records"),
            "chart": f"data:image/png;base64,{b64}"
        }

    except Exception as e:
        return f"Error during analysis: {str(e)}"
