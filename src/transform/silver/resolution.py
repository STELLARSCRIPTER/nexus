import pandas as pd
from sqlalchemy import text
from src.utils.db import get_engine
from rapidfuzz import fuzz, process

def resolve_entities():
    engine = get_engine()
    
    print("1. Fetching raw firms from Bronze...")
    with engine.connect() as conn:
        firms = pd.read_sql("SELECT * FROM bronze.raw_firms", conn)

    print("2. Finding duplicates using fuzzy matching...")
    # We only want to compare firms in the same country to save time
    unique_firms = firms.drop_duplicates(subset=["legal_name"]).copy()
    
    # This will store the mapping: duplicate_name -> canonical_name
    name_mapping = {}
    
    for country, group in unique_firms.groupby("country"):
        names = group["legal_name"].tolist()
        
        # For every name, find the best match
        for name in names:
            if name in name_mapping:
                continue # Already mapped
                
            # Find matches in the same country with > 90% similarity
            matches = process.extract(name, names, scorer=fuzz.token_set_ratio, limit=5)
            
            # The first match is the name itself, so we look at the others
            for match_name, score, index in matches[1:]:
                if score >= 90:
                    # We found a duplicate! Map the duplicate to the original
                    name_mapping[match_name] = name
                    break

    print(f"   -> Found {len(name_mapping)} duplicate firm names.")

    print("3. Applying mapping and creating Silver Firms table...")
    # Apply the mapping to create a canonical name
    firms["canonical_name"] = firms["legal_name"].apply(
        lambda x: name_mapping.get(x, x)
    )
    
    # Create a new ID based on the canonical name
    firms["firm_master_id"] = firms.groupby("canonical_name").ngroup() + 1
    firms["firm_master_id"] = "FM_" + firms["firm_master_id"].astype(str).str.zfill(6)
    
    # Save the cleaned dimensional table to the Silver schema
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver;"))
        
    silver_firms = firms[["firm_master_id", "canonical_name", "sector", "region", "country", "aum_usd_m"]]
    silver_firms = silver_firms.drop_duplicates(subset=["firm_master_id"])
    
    silver_firms.to_sql("dim_firms", engine, schema="silver", if_exists="replace", index=False)
    
    print(f"   -> Created silver.dim_firms with {len(silver_firms)} unique firms.")
    
    # Create a mapping table so we can join the dirty CRM data later
    id_mapping = firms[["firm_id", "firm_master_id"]]
    id_mapping.to_sql("firm_id_mapping", engine, schema="silver", if_exists="replace", index=False)
    
    print("4. Silver Entity Resolution complete!")

if __name__ == "__main__":
    resolve_entities()