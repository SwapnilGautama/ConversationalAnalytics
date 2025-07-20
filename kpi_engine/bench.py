# kpi_engine/bench.py

import pandas as pd

def load_resource_data(filepath, sheet_name="ResourceMaster"):
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

def preprocess_resource_data(df):
    df.columns = df.columns.str.strip()
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df['Billability'] = df['Billability'].str.strip().str.upper()
    df['BenchFlag'] = df['Billability'].apply(lambda x: 1 if x == 'BENCH' else 0)
    return df.dropna(subset=['Month'])

def total_bench_count(df):
    return df['BenchFlag'].sum()

def bench_percentage(df):
    total = len(df)
    bench = total_bench_count(df)
    return round((bench / total) * 100, 2) if total > 0 else 0.0

def bench_by_client(df):
    return df[df['BenchFlag'] == 1].groupby('Client').size().reset_index(name='BenchCount')

def bench_by_location(df):
    return df[df['BenchFlag'] == 1].groupby('Location').size().reset_index(name='BenchCount')

def bench_trend(df):
    return df.groupby('Month')['BenchFlag'].sum().reset_index(name='BenchCount')

def bench_summary(df):
    trend = bench_trend(df).sort_values('BenchCount', ascending=False)
    summary = [
        f"Total bench headcount is {total_bench_count(df)}.",
        f"Bench percentage across all resources is {bench_percentage(df)}%.",
        f"Month with highest bench: {trend.iloc[0].to_dict() if not trend.empty else 'N/A'}"
    ]
    return summary
