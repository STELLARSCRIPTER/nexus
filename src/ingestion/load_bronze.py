import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def get_engine():
    user = os.getenv("NEXUS_DB_USER", "postgres")
    password = os.getenv("NEXUS_DB_PASSWORD", "")
    host = os.getenv("NEXUS_DB_HOST", "localhost")
    port = os.getenv("NEXUS_DB_PORT", "5432")
    db = os.getenv("NEXUS_DB_NAME", "nexus")
    
    # Using SQLAlchemy's URL.create safely handles special characters like '@'
    from sqlalchemy.engine import URL
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=db
    )
    return create_engine(url)

def load_bronze():
    engine = get_engine()
    raw_dir = Path("data/raw")
    
    # Ensure schema exists
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))

    for csv_file in raw_dir.glob("*.csv"):
        table_name = f"raw_{csv_file.stem}"
        print(f"Loading {csv_file.name} into bronze.{table_name}...")
        
        df = pd.read_csv(csv_file)
        
        # Add audit columns
        df["_loaded_at"] = pd.Timestamp.utcnow()
        df["_source_file"] = csv_file.name
        
        df.to_sql(
            name=table_name,
            con=engine,
            schema="bronze",
            if_exists="replace",
            index=False,
            chunksize=10000 # Chunking prevents memory crashes
        )
    print("✅ Bronze layer loaded successfully.")

if __name__ == "__main__":
    load_bronze()