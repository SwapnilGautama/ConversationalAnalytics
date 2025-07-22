import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

def run(pn_df: pd.DataFrame, ut_df: pd.DataFrame, user_question: str):
    # --- Step 1: Identify the segment from question ---
    segment_list = pn_df['segment'].dropna().unique().tolist()
    segment = next((seg for seg in segment_list if seg.lower() in user_question.lower()), None)
    if not segment:
        return "❌ Could not identify a valid segment from your question.", None, None

    # --- Step 2: Filter for this segment ---
    df = pn_df[pn_df['segment'].str.lower() == segment.lower()].copy()
    if df.empty:
        return f"❌ No data found for segment: {segment}", None, None

    # --- Step 3: Ensure 'Quarter' exists and pick latest 2 ---
    if 'Quarter' not in df.columns:
        return "❌ 'Quarter' column missing in P&L data.", None, None

    latest_quarters = sorted(df['Quarter'].unique())[-2:]
    if len(latest_quarters) < 2:
        return f"Only current quarter data is available for **{segment}** segment. Please add previous quarter data to compare changes.", None, None

    q1, q2 = latest_quarters  # q1 = older, q2 = latest

    # --- Step 4: Revenue by Client for both quarters ---
    rev_q1 = df[df['Quarter'] == q1].groupby('Client Name')['Revenue'].sum().rename('Revenue_Q1')
    rev_q2 = df[df['Quarter'] == q2].groupby('Client Name')['Revenue'].sum().rename('Revenue_Q2')

    revenue_df = pd.concat([rev_q1, rev_q2], axis=1).fillna(0)
    revenue_df['Revenue_Drop'] = revenue_df['Revenue_Q2'] - revenue_df['Revenue_Q1']
    revenue_df['Abs_Drop'] = revenue_df['Revenue_Drop'].abs()

    # --- Step 5: Sort by absolute drop ---
    sorted_df = revenue_df.sort_values(by='Abs_Drop', ascending=False)
    top_drops = sorted_df[sorted_df['Revenue_Drop'] < 0]

    if top_drops.empty:
        return f"✅ No revenue drop detected for any client in **{segment}** segment between {q1} and {q2}.", None, None

    # --- Step 6: Plot pie chart ---
    fig, ax = plt.subplots()
    ax.pie(top_drops['Abs_Drop'], labels=top_drops.index, autopct='%1.1f%%', startangle=90)
    ax.set_title(f'Revenue Drop Share by Client ({segment})')
    plt.tight_layout()

    # Save to base64
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png")
    img_buf.seek(0)
    img_base64 = base64.b64encode(img_buf.read()).decode("utf-8")
    plt.close()

    # --- Step 7: Summary ---
    summary = f"### 📉 Revenue Drop Analysis for {segment} ({q1} → {q2})\n"
    summary += f"The following clients in **{segment}** segment experienced a revenue drop.\n\n"
    summary += f"Total drop: ₹{top_drops['Abs_Drop'].sum():,.0f}\n\n"

    return summary, top_drops[['Revenue_Q1', 'Revenue_Q2', 'Revenue_Drop']], img_base64
