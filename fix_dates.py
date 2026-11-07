from src.utils.db import get_engine
from sqlalchemy import text

def fix_dates():
    engine = get_engine()
    with engine.begin() as conn:
        print("Casting dates in raw_interactions...")
        conn.execute(text("ALTER TABLE bronze.raw_interactions ALTER COLUMN interaction_date TYPE DATE USING interaction_date::date;"))
        
        print("Casting dates in raw_transactions...")
        conn.execute(text("ALTER TABLE bronze.raw_transactions ALTER COLUMN transaction_date TYPE DATE USING transaction_date::date;"))
        
        print("✅ Dates fixed!")

if __name__ == "__main__":
    fix_dates()