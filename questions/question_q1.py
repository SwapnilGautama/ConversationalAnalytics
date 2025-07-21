# questions/question_q1.py

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from io import BytesIO
from kpi_engine.margin import compute_margin
import re

def extract_threshold(query):
    match = re.search(r'less than (\d+)%', query)
    if match:
        return float(match.group(1))
    return 30.0  # default threshold

def extract_period(query):
    query = query.lower()
    if "last month" in query:
        return "last_month"
    elif "last quarter" in query or "previous quarter" in query:
        return "last_quarter"
    else:
        return "last_quarter"  # default

def generate_bar_chart(df):
    fig, ax = plt.subplots(figsize=(8, 4))
    df_sorted = df.sort_values("Margin %")
    ax.barh(df_sorted["Company_code"], df_sorted["Margin %"], color='skyblue')
    ax.set_xlabel("Margin %")
    ax.set_title("Clients with Margin Below Threshold")
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    return buffer

def run_question():
    st.subheader("📉 Accounts with Margin Below Threshold")

    user_query = st.session_state.get("last_user_query", "").lower()

    # Extract dynamic threshold and time period
    threshold = extract_threshold(user_query)
    period = extract_period(user_query)

    # Load margin KPI and filter
    df = calculate_margin_kpi()

    if period == "last_quarter":
        latest_period = df["Period"].max()
        df = df[df["Period"] == latest_period]
    elif period == "last_month":
        df["Period"] = pd.to_datetime(df["Period"])
        latest_month = df["Period"].max()
        df = df[df["Period"] == latest_month]

    # Filter clients with low margin
    filtered_df = df[df["Margin %"] < threshold].copy()
    filtered_df = filtered_df[["Company_code", "Margin %"]]
    filtered_df["Margin %"] = filtered_df["Margin %"].map("{:.2f}%".format)

    # Summary
    count = len(filtered_df)
    total_clients = df["Company_code"].nunique()
    summary = (
        f"✅ {count} account(s) had margin below {threshold}% "
        f"in the {period.replace('_', ' ')} period, "
        f"which is {round((count / total_clients) * 100, 2)}% of all accounts."
    )

    # Display in two columns
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### Clients with Low Margin")
        st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)
    with col2:
        st.markdown("#### Margin % by Client (Bar Chart)")
        if not filtered_df.empty:
            chart = generate_bar_chart(df[df["Margin %"] < threshold])
            st.image(chart, use_column_width=True)
        else:
            st.info("No clients found below the margin threshold.")

    # Show summary
    st.success(summary)
def run(user_query: str):
    # your logic here
    return {
        "summary": summary,
        "table": formatted_table,
        "chart": chart_buffer,
    }
