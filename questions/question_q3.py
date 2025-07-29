import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from dateutil.relativedelta import relativedelta

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel("LNTDataSample.xlsx", sheet_name="LNTDataSample")
    return df

def filter_segment(df, user_query):
    segment_keywords = ['Transportation', 'Industrial Products', 'Media & Technology', 'Energy & Utilities', 'CPG & Retail']
    for seg in segment_keywords:
        if seg.lower() in user_query.lower():
            return df[df['Segment'].str.lower().str.contains(seg.lower())], seg
    return df, None

def preprocess(df):
    df = df[df['Type'].isin(['Revenue', 'Cost'])]

    df['Date'] = pd.to_datetime(df['Year'].astype(str) + "-" + df['Month'].astype(str).str.zfill(2) + "-01")
    df['C&B Flag'] = df['Group4'].str.contains("C&B", case=False, na=False)

    df_cnb = df[df['C&B Flag']]
    df_rev = df[df['Type'] == 'Revenue']

    agg_cnb = df_cnb.groupby('Date')['Amount in INR'].sum().reset_index().rename(columns={'Amount in INR': 'C&B'})
    agg_rev = df_rev.groupby('Date')['Amount in INR'].sum().reset_index().rename(columns={'Amount in INR': 'Revenue'})

    merged = pd.merge(agg_cnb, agg_rev, on='Date', how='inner')
    merged['C&B % of Revenue'] = (merged['C&B'] / merged['Revenue']) * 100
    merged = merged.sort_values('Date')

    merged['MoM C&B Change (%)'] = merged['C&B'].pct_change() * 100
    merged['MoM Revenue Change (%)'] = merged['Revenue'].pct_change() * 100
    merged['Period'] = merged['Date'].dt.strftime('%Y-%m')

    return merged

def display_insights(df, segment=None):
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    cnb_change = latest['MoM C&B Change (%)']
    rev_change = latest['MoM Revenue Change (%)']
    period = latest['Period']
    prev_period = prev['Period']

    seg_label = f" in {segment}" if segment else ""
    st.markdown(f"📌 In **{period}**, C&B cost changed by **{cnb_change:+.1f}%** while revenue changed by **{rev_change:+.1f}%** vs **{prev_period}**{seg_label}.")

def display_table(df):
    display_df = df[['Period', 'C&B', 'Revenue', 'C&B % of Revenue', 'MoM C&B Change (%)', 'MoM Revenue Change (%)']].copy()
    display_df.columns = ['Period', 'C&B (Million USD)', 'Revenue (Million USD)', 'C&B % of Revenue (%)', 'MoM C&B Change (%)', 'MoM Revenue Change (%)']
    st.dataframe(display_df.style.format({
        'C&B (Million USD)': '{:,.2f}',
        'Revenue (Million USD)': '{:,.2f}',
        'C&B % of Revenue (%)': '{:,.1f}',
        'MoM C&B Change (%)': '{:+.1f}',
        'MoM Revenue Change (%)': '{:+.1f}'
    }), use_container_width=True)

def plot_chart(df):
    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax2 = ax1.twinx()
    sns.barplot(x='Period', y='C&B % of Revenue', data=df, ax=ax1, color='lightyellow')
    sns.lineplot(x='Period', y='Revenue', data=df, ax=ax2, marker='o', color='skyblue')

    ax1.set_ylabel('C&B % of Revenue (%)')
    ax2.set_ylabel('Revenue (Million USD)')
    ax1.set_title('Monthly Revenue vs C&B % of Revenue')

    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

def run(user_question):
    st.markdown("### 📊 MoM Revenue vs C&B % of Revenue")

    df = load_data()
    df_filtered, segment = filter_segment(df, user_question)
    df_trend = preprocess(df_filtered)

    display_insights(df_trend, segment)
    display_table(df_trend)
    plot_chart(df_trend)
