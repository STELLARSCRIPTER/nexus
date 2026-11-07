import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

# Load .env for local testing
load_dotenv()

@st.cache_resource
def get_db_engine():
    # Check if we are running on Streamlit Cloud (Secrets exist)
    if "postgres" in st.secrets:
        host = st.secrets["postgres"]["host"]
        port = st.secrets["postgres"]["port"]
        db = st.secrets["postgres"]["database"]
        user = st.secrets["postgres"]["username"]
        password = st.secrets["postgres"]["password"]
    else:
        # Local fallback
        host = os.getenv("NEXUS_DB_HOST", "localhost")
        port = os.getenv("NEXUS_DB_PORT", "5432")
        db = os.getenv("NEXUS_DB_NAME", "nexus")
        user = os.getenv("NEXUS_DB_USER", "postgres")
        password = os.getenv("NEXUS_DB_PASSWORD", "")

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=db,
        query={"sslmode": "require"} # Force SSL for Supabase
    )
    return create_engine(url)

@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    engine = get_db_engine()
    with engine.connect() as conn:
        return pd.read_sql(query, conn)