import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def get_db_engine():
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("NEXUS_DB_USER"),
        password=os.getenv("NEXUS_DB_PASSWORD"),
        host=os.getenv("NEXUS_DB_HOST"),
        port=os.getenv("NEXUS_DB_PORT"),
        database=os.getenv("NEXUS_DB_NAME")
    )
    return create_engine(url)

@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    engine = get_db_engine()
    with engine.connect() as conn:
        return pd.read_sql(query, conn)