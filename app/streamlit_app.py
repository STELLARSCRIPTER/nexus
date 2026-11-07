import streamlit as st

st.set_page_config(page_title="NEXUS | Institutional Intelligence", layout="wide")

st.title("NEXUS: Institutional Intelligence Platform")
st.markdown("""
Welcome to the **NEXUS** executive decision interface. 
This platform transforms fragmented institutional data into actionable relationship, deal, and revenue intelligence.
""")

st.sidebar.header("Navigation")
st.sidebar.info("Select a page above to explore the data.")

# Metrics on the landing page
st.subheader("Platform Status")
col1, col2, col3 = st.columns(3)
col1.metric("Connected Records", "1,525,790", "Synthetic")
col2.metric("Institutions Tracked", "22,672", "Cleaned & Resolved")
col3.metric("Active Funds", "40", "M&A & Growth Equity")

st.markdown("---")
st.markdown("*Data is entirely synthetic and generated for portfolio demonstration purposes.*")