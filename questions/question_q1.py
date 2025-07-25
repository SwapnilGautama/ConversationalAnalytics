import pandas as pd
from dateutil.relativedelta import relativedelta
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import re

def compute_margin(df):
    df = df.copy()
    pivot = df.pivot_table(index=["Month", "Client"], 
                           columns="Type", 
                           values="Amount", 
                           aggfunc="sum").reset_index()
    pivot["Revenue"] = pivot.get("Revenue", 0)
    pivot["Cost"] = pivot.get("Cost", 0)
    pivot["Margin %"] = ((pivot["Revenue"] - pivot["Cost"]) / pivot["Revenue"]) * 100
    return pivot

def extract_threshold(user_question, default_threshold=30):
    if user_question:
        patterns = [
            r"margin\s*<\s*(\d+)",
            r"less than\s*(\d+)",
            r"below\s*(\d+)",
            r"under\s*(\d+)",
            r"margin.*?(\d+)\s*%"
        ]
        for pattern in patterns:
            match = re.search(pattern, user_question.lower())
            if match:
                return float(match.group(1))
    return default_threshold

def extract_month(user_question):
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }
    if user_question:
        user_question = user_question.lower()
        for name, num in months.items():
            if name in user_question:
                year_match = re.search(rf"{name}\s*(\d{{4}})", user_question)
                if year_match:
                    year = int(year_match.group(1))
                    return pd.Timestamp(year=year, month=num, day=1)
    return None

def run(df, user_question=None):
    df_margin = compute_margin(df)

    if "Month" not in df_margin or "Client" not in df_margin or "Margin %" not in df_margin:
        st.error("Required fields missing. Ensure Margin % calculation is correctly applied.")
        return

    threshold = extract_threshold(user_question)
    target_month = extract_month(user_question)

    if target_month:
        filtered_data = df_margin[df_margin["Month"].dt.to_period("M") == target_month.to_period("M")]
        time_label = target_month.strftime("%B %Y")
    else:
        latest_month = df_margin["Month"].max()
        quarter_start = latest_month - relativedelta(months=2)
        filtered_data = df_margin[(df_margin["Month"] >= quarter_start) & (df_margin["Month"] <= latest_month)]
        time_label = "the last quarter"

    agg = filtered_data.groupby("Client").agg({
        "Margin %": "mean",
        "Revenue": "sum",
        "Cost": "sum"
    }).reset_index()

    agg.rename(columns={
        "Margin %": "Latest Margin %",
        "Revenue": "Revenue (Million USD)",
        "Cost": "Cost (Million USD)"
    }, inplace=True)

    agg["Revenue (Million USD)"] = (agg["Revenue (Million USD)"] / 1e6).round(2)
    agg["Cost (Million USD)"] = (agg["Cost (Million USD)"] / 1e6).round(2)
    agg["Latest Margin %"] = agg["Latest Margin %"].round(2)

    filtered_df = agg[(agg["Latest Margin %"] < threshold) & (agg["Revenue (Million USD)"] > 0)]

    top_10 = filtered_df.sort_values("Latest Margin %", ascending=False).head(10)

    total_clients = agg["Client"].nunique()
    low_margin_count = filtered_df["Client"].nunique()
    proportion = (low_margin_count / total_clients * 100) if total_clients else 0

    st.markdown(
        f"🔍 **For {time_label}**, **{low_margin_count} accounts** had an average margin below **{threshold}%** "
        f"and non-zero revenue, which is **{proportion:.1f}%** of all **{total_clients} accounts**."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"#### 📋 Accounts with Margin < {threshold}% (non-zero revenue)")
        st.dataframe(
            top_10[["Client", "Latest Margin %", "Revenue (Million USD)", "Cost (Million USD)"]].reset_index(drop=True),
            use_container_width=True
        )

    with col2:
        st.markdown("#### 📊 Margin % by Client (Bar Chart)")
        fig, ax = plt.subplots()
        margins = top_10["Latest Margin %"]
        colors = []
        for val in margins:
            if val >= 0:
                green_intensity = 0.9 - (val / margins.max()) * 0.6 if margins.max() != 0 else 0.9
                colors.append((green_intensity, 1.0, green_intensity))
            else:
                red_intensity = 0.9 - (abs(val) / abs(margins.min())) * 0.6 if margins.min() != 0 else 0.9
                colors.append((1.0, red_intensity, red_intensity))

        for spine in ax.spines.values():
            spine.set_color('#D3D3D3')
            spine.set_linewidth(0.6)

        ax.barh(top_10["Client"], top_10["Latest Margin %"], color=colors, edgecolor='none')
        ax.set_xlabel(f"Margin % ({time_label})")
        ax.set_ylabel("Client")
        ax.set_title(f"Top 10 Clients with Margin < {threshold}%")
        ax.set_xlim(-100, 100)
        ax.invert_yaxis()
        ax.grid(False)
        plt.tight_layout()
        st.pyplot(fig)

    # ✅ NEW DYNAMIC CHART: C&B as % of Revenue
    st.markdown("#### 📉 C&B Cost as % of Revenue (for low-margin accounts over last 3 months)")
    df_cb = df[(df["Group3"] == "C&B") & df["Client"].isin(filtered_df["Client"])]

    if not df_cb.empty:
        df_cb = df_cb.copy()
        df_cb["Month"] = pd.to_datetime(df_cb["Month"])
        cb_pivot = df_cb.pivot_table(index=["Month", "Client"], values="Amount", aggfunc="sum").reset_index()
        rev_pivot = df[df["Type"] == "Revenue"].groupby(["Month", "Client"])["Amount"].sum().reset_index()
        merged = pd.merge(cb_pivot, rev_pivot, on=["Month", "Client"], suffixes=("_CB", "_Revenue"))

        merged["CB_pct_of_Rev"] = (merged["Amount_CB"] / merged["Amount_Revenue"]) * 100
        merged["Month"] = merged["Month"].dt.strftime("%b %Y")

        fig_cb, ax_cb = plt.subplots(figsize=(8, 4))
        for client in merged["Client"].unique():
            data = merged[merged["Client"] == client]
            ax_cb.plot(data["Month"], data["CB_pct_of_Rev"], marker="o", label=client)

        ax_cb.set_ylabel("C&B as % of Revenue")
        ax_cb.set_xlabel("Month")
        ax_cb.set_title("C&B Cost % of Revenue (for low-margin clients)")
        ax_cb.set_ylim(0, merged["CB_pct_of_Rev"].max() * 1.1)
        ax_cb.grid(True, linestyle="--", linewidth=0.5)
        for spine in ax_cb.spines.values():
            spine.set_color('#D3D3D3')
            spine.set_linewidth(0.6)
        st.pyplot(fig_cb)

    return None
