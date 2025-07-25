import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns

def run(df, user_question):
    st.title("Q7. Accounts with Realized Rate Drop")

    # Standardize column names
    df.columns = df.columns.str.strip()
    df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
    df['Month'] = df['Date_a'].dt.to_period('M').astype(str)

    # Drop rows with missing critical values
    df = df.dropna(subset=['Revenue', 'Cost', 'PSNo'])

    # Step 1: Compute realized rate = revenue / headcount per month per client
    agg_df = df.groupby(['Company_Code', 'Month']).agg({
        'Revenue': 'sum',
        'Cost': 'sum',
        'PSNo': pd.Series.nunique
    }).reset_index().rename(columns={'PSNo': 'Headcount'})

    agg_df['Realized_Rate'] = agg_df['Revenue'] / agg_df['Headcount']

    # Step 2: Pivot to compare current and previous quarter realized rates
    agg_df['Quarter'] = pd.to_datetime(agg_df['Month']).dt.to_period('Q')
    latest_quarter = agg_df['Quarter'].max()
    prev_quarter = latest_quarter - 1

    curr_q = agg_df[agg_df['Quarter'] == latest_quarter]
    prev_q = agg_df[agg_df['Quarter'] == prev_quarter]

    merged = pd.merge(curr_q, prev_q, on='Company_Code', suffixes=('_curr', '_prev'))

    # Step 3: Identify accounts where realized rate dropped > $3
    merged['Drop'] = merged['Realized_Rate_prev'] - merged['Realized_Rate_curr']
    significant_drop = merged[merged['Drop'] > 3]

    st.subheader("Summary Insights")

    if significant_drop.empty:
        st.info("No accounts found with a significant drop (> $3) in realized rate.")
    else:
        count = significant_drop.shape[0]
        st.markdown(f"- ✅ Found **{count}** accounts with realized rate drop > $3 in {latest_quarter}")
        st.markdown("- 📉 These may signal underpricing or declining efficiency.")
        st.markdown("- 🔎 Recommended for margin analysis.")

        # Step 4: Show table of such accounts
        display_cols = ['Company_Code', 'Realized_Rate_prev', 'Realized_Rate_curr', 'Drop']
        st.dataframe(significant_drop[display_cols].round(2).rename(columns={
            'Company_Code': 'Client',
            'Realized_Rate_prev': 'Prev Realized Rate',
            'Realized_Rate_curr': 'Curr Realized Rate',
            'Drop': 'Drop in Rate'
        }))

    st.markdown("---")
    st.subheader("Headcount Composition Over Time")

    # Monthly breakdown: Billable vs Non-Billable
    count_df = df.groupby(['Month', 'Status']).agg({'PSNo': pd.Series.nunique}).reset_index()
    pivot_status = count_df.pivot(index='Month', columns='Status', values='PSNo').fillna(0).sort_index()

    # Monthly breakdown: Onsite vs Offshore
    count_df2 = df.groupby(['Month', 'Onsite/Offshore']).agg({'PSNo': pd.Series.nunique}).reset_index()
    pivot_location = count_df2.pivot(index='Month', columns='Onsite/Offshore', values='PSNo').fillna(0).sort_index()

    # Summary for latest month
    latest_month = df['Month'].max()
    recent = df[df['Month'] == latest_month]
    total = recent['PSNo'].nunique()
    billable_pct = recent[recent['Status'] == 'Billable']['PSNo'].nunique() / total * 100 if total else 0
    onsite_pct = recent[recent['Onsite/Offshore'] == 'Onsite']['PSNo'].nunique() / total * 100 if total else 0

    st.markdown(f"- 👨‍💼 In {latest_month}, **{billable_pct:.1f}%** of headcount is Billable")
    st.markdown(f"- 🌐 In {latest_month}, **{onsite_pct:.1f}%** of headcount is Onsite")

    # Charts
    st.subheader("Monthly Headcount Split (Stacked View)")
    fig, axes = plt.subplots(1, 2, figsize=(16, 5), sharey=True)

    pastel_green = sns.color_palette("Greens", n_colors=3)[1]
    pastel_red = sns.color_palette("Reds", n_colors=3)[1]
    pastel_blue = sns.color_palette("Blues", n_colors=3)[1]
    pastel_orange = sns.color_palette("Oranges", n_colors=3)[1]
    grey_border = "#cccccc"

    # Chart 1: Billable vs Non-Billable
    pivot_status.plot(kind='bar', stacked=True, ax=axes[0],
                      color=[pastel_green, pastel_red], edgecolor=grey_border)
    axes[0].set_title("Billable vs Non-Billable (Monthly)")
    axes[0].set_xlabel("Month")
    axes[0].set_ylabel("Headcount")
    axes[0].legend(title="Status", loc="upper left")

    # Chart 2: Onsite vs Offshore
    pivot_location.plot(kind='bar', stacked=True, ax=axes[1],
                        color=[pastel_blue, pastel_orange], edgecolor=grey_border)
    axes[1].set_title("Onsite vs Offshore (Monthly)")
    axes[1].set_xlabel("Month")
    axes[1].legend(title="Location", loc="upper left")

    plt.tight_layout()
    st.pyplot(fig)
