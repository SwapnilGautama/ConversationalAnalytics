import pandas as pd

def calculate_revenue_trends(df: pd.DataFrame) -> dict:
    """
    Calculates YoY, QoQ, and MoM revenue trends by DU, BU, and Account.

    Args:
        df (pd.DataFrame): Input DataFrame containing columns:
            - 'Date'
            - 'Delivery_Unit'
            - 'Business_Unit'
            - 'Final_Customer_Name'
            - 'Revenue'

    Returns:
        dict: Contains dataframes with revenue trends for YoY, QoQ, and MoM.
    """
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Quarter'] = df['Date'].dt.to_period("Q")
    df['Month'] = df['Date'].dt.to_period("M")

    # Grouped revenue summaries
    yoy_df = df.groupby(['Delivery_Unit', 'Business_Unit', 'Final_Customer_Name', 'Year'])['Revenue'].sum().reset_index()
    qoq_df = df.groupby(['Delivery_Unit', 'Business_Unit', 'Final_Customer_Name', 'Quarter'])['Revenue'].sum().reset_index()
    mom_df = df.groupby(['Delivery_Unit', 'Business_Unit', 'Final_Customer_Name', 'Month'])['Revenue'].sum().reset_index()

    return {
        "yoy_trend": yoy_df,
        "qoq_trend": qoq_df,
        "mom_trend": mom_df
    }
