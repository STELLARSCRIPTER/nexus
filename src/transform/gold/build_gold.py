import pandas as pd
import numpy as np
from sqlalchemy import text
from src.utils.db import get_engine

def build_gold_tables():
    engine = get_engine()
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
        
    print("1. Loading cleaned firm mapping and interactions...")
    with engine.connect() as conn:
        firms = pd.read_sql("SELECT firm_master_id, canonical_name, sector, region FROM silver.dim_firms", conn)
        interactions = pd.read_sql("SELECT * FROM bronze.raw_interactions", conn)
        mapping = pd.read_sql("SELECT firm_id, firm_master_id FROM silver.firm_id_mapping", conn)
        deals = pd.read_sql("SELECT * FROM bronze.raw_deals", conn)
        transactions = pd.read_sql("SELECT * FROM bronze.raw_transactions", conn)

    print("2. Resolving IDs from Bronze to Silver (Master Data)...")
    interactions = interactions.merge(mapping, on="firm_id", how="inner")
    deals = deals.merge(mapping, left_on="originator_firm_id", right_on="firm_id", how="left")
    transactions = transactions.merge(mapping, on="firm_id", how="inner")

    print("3. Calculating Relationship Intelligence (Module B)...")
    interactions['interaction_date'] = pd.to_datetime(interactions['interaction_date'])
    max_date = interactions['interaction_date'].max()
    recent_cutoff = max_date - pd.Timedelta(days=180)
    
    recent_interactions = interactions[interactions['interaction_date'] >= recent_cutoff]
    
    engagement = recent_interactions.groupby('firm_master_id').agg(
        recent_interactions=('interaction_id', 'count'),
        unique_contacts=('contact_id', 'nunique')
    ).reset_index()
    
    rel_intel = firms.merge(engagement, on='firm_master_id', how='left').fillna(0)
    
    # FIX: Log scaling to prevent outliers from crushing the average score
    rel_intel['log_interactions'] = np.log1p(rel_intel['recent_interactions'])
    rel_intel['log_contacts'] = np.log1p(rel_intel['unique_contacts'])
    
    p99_int = rel_intel['log_interactions'].quantile(0.99)
    p99_cont = rel_intel['log_contacts'].quantile(0.99)
    
    # Prevent division by zero
    p99_int = p99_int if p99_int > 0 else 1
    p99_cont = p99_cont if p99_cont > 0 else 1
    
    rel_intel['relationship_score'] = (
        (rel_intel['log_interactions'] / p99_int * 40) +
        (rel_intel['log_contacts'] / p99_cont * 60)
    ).clip(upper=100).round(2)
    
    print("4. Calculating Revenue Intelligence (Module D)...")
    revenue = transactions.groupby('firm_master_id').agg(
        total_revenue_usd_m=('amount_usd_m', 'sum'),
        transaction_count=('transaction_id', 'count')
    ).reset_index()
    
    total_market_rev = revenue['total_revenue_usd_m'].sum()
    revenue['market_share'] = revenue['total_revenue_usd_m'] / total_market_rev
    
    # FIX: HHI Calculation (Decimal squared, multiplied by 10,000 for readable scale)
    revenue['hhi_contribution'] = (revenue['market_share'] ** 2) * 10000
    
    rev_intel = firms.merge(revenue, on='firm_master_id', how='left').fillna(0)
    
    print("5. Saving to Gold Layer...")
    firms.to_sql("dim_firm", engine, schema="gold", if_exists="replace", index=False)
    rel_intel.to_sql("fct_relationship_intelligence", engine, schema="gold", if_exists="replace", index=False)
    rev_intel.to_sql("fct_revenue_intelligence", engine, schema="gold", if_exists="replace", index=False)
    
    print(f"   -> gold.dim_firm: {len(firms)} rows")
    print(f"   -> gold.fct_relationship_intelligence: {len(rel_intel)} rows")
    print(f"   -> gold.fct_revenue_intelligence: {len(rev_intel)} rows")
    
    print("\n✅ Gold Layer build complete!")

if __name__ == "__main__":
    build_gold_tables()