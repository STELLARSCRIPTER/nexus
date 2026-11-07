import pandas as pd
import hashlib
from sqlalchemy import text
from src.utils.db import get_engine

def run_quota_modeling():
    engine = get_engine()
    print("1. Simulating RM Capacity & Quota...")
    
    query = """
    SELECT r.firm_master_id, r.total_revenue_usd_m 
    FROM gold.fct_revenue_intelligence r 
    WHERE r.total_revenue_usd_m > 0
    """
    df = pd.read_sql(query, engine)
    
    def assign_rm(firm_id):
        hash_val = int(hashlib.md5(str(firm_id).encode()).hexdigest(), 16)
        return (hash_val % 10) + 1
        
    df['rm_id'] = df['firm_master_id'].apply(assign_rm)
    
    rm_summary = df.groupby('rm_id').agg(
        portfolio_size=('firm_master_id', 'count'),
        total_revenue=('total_revenue_usd_m', 'sum')
    ).reset_index()
    
    rm_summary['quota'] = rm_summary['total_revenue'] * 1.10
    rm_summary['attainment_pct'] = (rm_summary['total_revenue'] / rm_summary['quota']) * 100
    
    print(rm_summary)
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
    rm_summary.to_sql("fct_rm_quota", engine, schema="gold", if_exists="replace", index=False)
    print("✅ RM Quota data saved.")

if __name__ == "__main__":
    run_quota_modeling()