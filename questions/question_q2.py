import pandas as pd

def run(user_query: str, df: pd.DataFrame) -> dict:
    # Extract segment name from user_query
    segment = None
    for word in user_query.split():
        if word.lower() in df['Segment'].str.lower().unique():
            segment = word.title()
            break
    if not segment:
        return {"answer": "Please specify a valid segment name in your query (e.g., Transportation, Healthcare)."}

    # Filter only that segment
    segment_df = df[df['Segment'].str.lower() == segment.lower()]

    if segment_df.empty:
        return {"answer": f"No data found for segment '{segment}'."}

    # Ensure 'Month' is datetime type
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    segment_df['Month'] = pd.to_datetime(segment_df['Month'], errors='coerce')

    # Extract Quarter and Year
    segment_df['Quarter'] = segment_df['Month'].dt.to_period('Q')

    # Group revenue by client and quarter
    grouped = segment_df.groupby(['Client Name', 'Quarter'])['Revenue'].sum().unstack(fill_value=0)

    # Get the 2 most recent quarters
    recent_quarters = sorted(grouped.columns)[-2:]
    if len(recent_quarters) < 2:
        return {"answer": f"Not enough data for two quarters in '{segment}' segment."}

    q_prev, q_curr = recent_quarters
    grouped['Revenue Drop'] = grouped[q_prev] - grouped[q_curr]
    grouped['% Drop'] = grouped['Revenue Drop'] / grouped[q_prev].replace(0, pd.NA) * 100

    # Sort by biggest drop
    result = grouped.sort_values(by='Revenue Drop', ascending=False).reset_index()

    # Generate summary
    top_client = result.iloc[0]
    summary = (
        f"In the '{segment}' segment, the client with the biggest revenue drop from {q_prev} to {q_curr} "
        f"is **{top_client['Client Name']}**, whose revenue fell from ₹{top_client[q_prev]:,.0f} to "
        f"₹{top_client[q_curr]:,.0f} — a drop of ₹{top_client['Revenue Drop']:,.0f} ({top_client['% Drop']:.1f}%)."
    )

    # Format final table
    table = result[['Client Name', q_prev, q_curr, 'Revenue Drop', '% Drop']]

    return {
        "answer": summary,
        "tables": [{"title": f"Client Revenue Comparison in '{segment}' Segment", "df": table}]
    }
