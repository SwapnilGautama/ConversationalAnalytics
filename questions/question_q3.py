import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import io
import base64
from datetime import datetime

def run(LNTData: pd.DataFrame, user_prompt: str):
    # --- Extract relevant fields ---
    required_columns = ['Month', 'Year', 'Type', 'Group3', 'Segment', 'Amount in INR']
    data = LNTData[required_columns].copy()

    # --- Preprocessing ---
    data['YearMapped'] = data['Year'].map({'2024-25': 2024, '2025-26': 2025})
    data = data.dropna(subset=['YearMapped'])
    data['MonthMapped'] = data['Month'].apply(lambda x: datetime(2000, x, 1).strftime('%b'))
    data['YearMonth'] = pd.to_datetime(data['YearMapped'].astype(str) + '-' + data['Month'].astype(str).str.zfill(2) + '-01')

    # --- Segment filter from chatbot ---
    user_prompt_lower = user_prompt.lower()
    unique_segments = data['Segment'].dropna().unique()
    selected_segment = None
    for segment in unique_segments:
        if str(segment).lower() in user_prompt_lower:
            selected_segment = segment
            break
    if selected_segment:
        data = data[data['Segment'] == selected_segment]

    # --- Filter for C&B cost and revenue ---
    cb_data = data[data['Group3'].str.lower().str.contains("c&b", na=False)]
    cb_data = cb_data[data['Type'].isin(['Cost', 'Revenue'])]

    # --- Group and pivot ---
    pivot = cb_data.groupby(['Segment', 'Type', 'YearMapped'])['Amount in INR'].sum().reset_index()
    pivot_table = pivot.pivot(index='Segment', columns=['Type', 'YearMapped'], values='Amount in INR').fillna(0)

    # --- Add % change columns ---
    for cost_type in ['Cost', 'Revenue']:
        if (cost_type, 2024) in pivot_table.columns and (cost_type, 2025) in pivot_table.columns:
            pivot_table[(cost_type, '% Change')] = (
                (pivot_table[(cost_type, 2025)] - pivot_table[(cost_type, 2024)]) / pivot_table[(cost_type, 2024)]
            ).replace([float('inf'), -float('inf')], 0) * 100

    # --- Formatting for display ---
    display_table = pivot_table.copy()
    display_table.columns = [' '.join(map(str, col)).strip() for col in display_table.columns.values]
    display_table.reset_index(inplace=True)

    # --- Create horizontal bar chart for C&B % change ---
    cb_bar = display_table[['Segment', 'Cost % Change']].copy()
    cb_bar = cb_bar.sort_values(by='Cost % Change', ascending=False)
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    sns.barplot(data=cb_bar, y='Segment', x='Cost % Change', ax=ax1, palette='Blues_d')
    ax1.set_title("C&B % Change by Segment")
    ax1.set_xlabel("C&B % Change")
    ax1.xaxis.set_major_formatter(mtick.PercentFormatter())

    buffer1 = io.BytesIO()
    plt.tight_layout()
    fig1.savefig(buffer1, format='png')
    buffer1.seek(0)
    cb_img_uri = base64.b64encode(buffer1.read()).decode('utf-8')
    plt.close(fig1)

    # --- Stacked bar chart for C&B and Revenue absolute values ---
    bar_data = pivot[['Segment', 'Type', 'YearMapped', 'Amount in INR']].copy()
    bar_pivot = bar_data.pivot_table(index=['Segment', 'YearMapped'], columns='Type', values='Amount in INR', aggfunc='sum').fillna(0)
    bar_pivot.reset_index(inplace=True)

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    segments = bar_pivot['Segment'].unique()
    width = 0.35
    for i, seg in enumerate(segments):
        subset = bar_pivot[bar_pivot['Segment'] == seg]
        x = subset['YearMapped'] + (i - len(segments) / 2) * width
        ax2.bar(x, subset['Cost'], width=width, label=f'{seg} - Cost')
        ax2.bar(x, subset['Revenue'], width=width, bottom=subset['Cost'], label=f'{seg} - Revenue')

    ax2.set_title('C&B + Revenue by Segment')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('INR')
    ax2.legend()
    buffer2 = io.BytesIO()
    plt.tight_layout()
    fig2.savefig(buffer2, format='png')
    buffer2.seek(0)
    bar_img_uri = base64.b64encode(buffer2.read()).decode('utf-8')
    plt.close(fig2)

    # --- Add conditional insight bullets ---
    insights = []
    insights.append(f"C&B costs increased in {display_table['Segment'].iloc[0]} by {display_table['Cost % Change'].iloc[0]:.1f}%")
    insights.append(f"Revenue changed by {display_table['Revenue % Change'].iloc[0]:.1f}% in the same segment")

    # --- Output ---
    return {
        "insights": insights,
        "tables": [
            {
                "title": "C&B vs Revenue Comparison by Segment",
                "data": display_table.round(2).to_dict(orient="records")
            }
        ],
        "charts": [
            {
                "title": "C&B % Change by Segment",
                "type": "image",
                "data": f"data:image/png;base64,{cb_img_uri}"
            },
            {
                "title": "C&B + Revenue by Segment",
                "type": "image",
                "data": f"data:image/png;base64,{bar_img_uri}"
            }
        ]
    }
