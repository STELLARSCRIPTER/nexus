import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Read from .env
user = os.getenv("NEXUS_DB_USER", "postgres")
password = os.getenv("NEXUS_DB_PASSWORD", "Sanjaykaushik@123")
host = os.getenv("NEXUS_DB_HOST", "localhost")
port = os.getenv("NEXUS_DB_PORT", "5432")
db = os.getenv("NEXUS_DB_NAME", "nexus")

# Create connection string safely
from sqlalchemy.engine import URL
url = URL.create(
    drivername="postgresql+psycopg2",
    username=user,
    password=password,
    host=host,
    port=port,
    database=db
)

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM bronze.raw_firms;"))
        count = result.scalar()
        print(f"✅ Successfully connected! Found {count:,} firms in the Bronze layer.")
except Exception as e:
    print(f"❌ Connection failed: {e}")