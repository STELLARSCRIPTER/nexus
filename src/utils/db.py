import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("NEXUS_DB_USER"),
        password=os.getenv("NEXUS_DB_PASSWORD"),
        host=os.getenv("NEXUS_DB_HOST"),
        port=os.getenv("NEXUS_DB_PORT"),
        database=os.getenv("NEXUS_DB_NAME")
    )
    return create_engine(url)