import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def run(df):
    try:
        # Clean column names
        df.columns = df.columns.str.strip()

        # Only filter rows relevant to C&B cost
        df = df[df['Group3'].str.contains("C&B", case=False, na=False)]

        # Clean and convert Month
        df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
        df = df.dropna(subset=['Month'])

        # Extract Year and Quarter
        df['Quarter'] = df['Month'].dt.to_period('Q')

        # Filter last two quarters
        latest_quarters = sorted(df['Quarter'].unique())[-2:]
        if len(latest_quarters) < 2:
            st.error("Not enough data to compare two quarters.")
            return

        df_q = df[df['Quarter'].isin(latest_quarters)]

        # Aggregate by Segment and Quarter
        grouped = df_q.groupby(['Segment', 'Quarter'])['Amount in INR'].sum().reset_index()
        pivoted = grouped.pivot(index='Segment', columns='Quarter', values='Amount in INR').fillna(0)
        pivoted.columns = pivoted.columns.astype(str)

        # Ensure both quarters exist
        q1, q2 = pivoted.columns
        pivoted['% Change'] = ((pivoted[q2] - pivoted[q1]) / pivoted[q1].replace(0, 1e-6)) * 100
        pivoted = pivoted.sort_values('% Change', ascending=False)

        # Summary stats
        total_cb = df[df['Quarter'] == latest_quarters[-1]]['Amount in INR'].sum()
        top_segments = pivoted[q2].nlargest(3)
        total_change = ((df[df['Quarter'] == latest_quarters[-1]]['Amount in INR'].sum() -
                        df[df['Quarter'] == latest_quarters[-2]]['Amount in INR'].sum()) /
                        df[df['Quarter'] == latest_quarters[-2]]['Amount in INR'].sum()) * 100

        # Revenue comparison if present
        total_revenue_q1 = df[(df['Quarter'] == latest_quarters[-2]) & (df['Type'] == 'Revenue')]['Amount in INR'].sum()
        total_revenue_q2 = df[(df['Quarter'] == latest_quarters[-1]) & (df['Type'] == 'Revenue')]['Amount in INR'].sum()
        revenue_change = ((total_revenue_q2 - total_revenue_q1) / total_revenue_q1) * 100 if total_revenue_q1 else 0

        # Display insights
        st.markdown("### 🧠 Summary Insights")
        st.markdown(f"1. **Total C&B Cost** in latest quarter: ₹{total_cb:,.2f}. Top segments: {', '.join(top_segments.index)}.")
        st.markdown(f"2. **QoQ % Change in C&B**: {total_change:.2f}%. Segment drivers: {', '.join(pivoted.head(3).index)}")
        st.markdown(f"3. **Overall C&B vs Revenue Change**: C&B {total_change:.2f}% vs Revenue {revenue_change:.2f}%")

        # Display table and chart
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("### 📋 C&B Cost by Segment")
            st.dataframe(pivoted.reset_index().rename(columns={q1: f"{q1}", q2: f"{q2}"}))
        with col2:
            st.markdown("### 📊 % Change in C&B Cost")
            fig, ax = plt.subplots(figsize=(5, 5))
            pivoted['% Change'].plot(kind='barh', ax=ax, color='orange')
            ax.set_xlabel('% Change')
            ax.set_title('% Change in C&B Cost by Segment')
            st.pyplot(fig)

    except Exception as e:
        st.error(f"An error occurred in Q3: {e}")
