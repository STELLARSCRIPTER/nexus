from src.utils.db import get_engine
from sqlalchemy import text

def check_counts():
    engine = get_engine()
    with engine.connect() as conn:
        print("--- BRONZE LAYER (Raw, Dirty Data) ---")
        # Get all tables in the bronze schema
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'bronze'
        """)
        tables = [row[0] for row in conn.execute(query)]
        
        for table in sorted(tables):
            count = conn.execute(text(f"SELECT COUNT(*) FROM bronze.{table}")).scalar()
            print(f"{table:30} : {count:>10,} rows")
            
        print("\n--- SILVER LAYER (Cleaned Data) ---")
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'silver'
        """)
        tables = [row[0] for row in conn.execute(query)]
        
        for table in sorted(tables):
            count = conn.execute(text(f"SELECT COUNT(*) FROM silver.{table}")).scalar()
            print(f"{table:30} : {count:>10,} rows")

if __name__ == "__main__":
    check_counts()