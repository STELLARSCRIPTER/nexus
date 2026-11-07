import streamlit as st
import plotly.express as px
import pandas as pd
from components.db import run_query
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.title("Network Analysis & Centrality")
st.markdown("Analyze the institutional ecosystem using Graph Theory and Relationship Manager capacity.")

# ==========================================
# 1. Top Influential Firms
# ==========================================
st.subheader("Most Influential Institutions")
query_centrality = """
SELECT f.canonical_name, f.sector, n.degree_centrality, n.betweenness_centrality, COALESCE(r.total_revenue_usd_m, 0) as total_revenue
FROM gold.fct_network_centrality n
JOIN gold.dim_firm f ON n.firm_master_id = f.firm_master_id
LEFT JOIN gold.fct_revenue_intelligence r ON n.firm_master_id = r.firm_master_id
ORDER BY n.betweenness_centrality DESC LIMIT 50
"""
df_cent = run_query(query_centrality)

col1, col2 = st.columns([1, 1])
with col1:
    st.dataframe(
        df_cent.style.format({"degree_centrality": "{:.4f}", "betweenness_centrality": "{:.4f}", "total_revenue": "${:,.1f}M"}).background_gradient(subset=["betweenness_centrality"], cmap="Blues"),
        use_container_width=True, height=400
    )
with col2:
    fig = px.scatter(df_cent, x="degree_centrality", y="betweenness_centrality", size="total_revenue", color="sector", hover_name="canonical_name", size_max=30)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=400)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==========================================
# 2. Interactive Node Graph (PyVis)
# ==========================================
st.subheader("Interactive Deal Graph (Top 150 Institutions)")
query_graph_nodes = """
SELECT firm_master_id, canonical_name, sector 
FROM gold.fct_network_centrality n
JOIN gold.dim_firm f USING (firm_master_id)
ORDER BY degree_centrality DESC LIMIT 150
"""
df_nodes = run_query(query_graph_nodes)
node_ids = tuple(df_nodes['firm_master_id'].tolist())

query_edges = f"""
SELECT m1.firm_master_id AS source, m2.firm_master_id AS target
FROM bronze.raw_deals d
JOIN silver.firm_id_mapping m1 ON d.originator_firm_id = m1.firm_id
JOIN silver.firm_id_mapping m2 ON d.counterparty_firm_id = m2.firm_id
WHERE m1.firm_master_id IN {node_ids} AND m2.firm_master_id IN {node_ids} AND m1.firm_master_id != m2.firm_master_id
"""
df_edges = run_query(query_edges)

net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black", directed=False)
net.force_atlas_2based()

sector_colors = {"Private Equity": "#4A90E2", "Hedge Fund": "#50E3C2", "Family Office": "#F5A623", "Pension Fund": "#D0021B", "Investment Bank": "#9013FE"}

for _, row in df_nodes.iterrows():
    color = sector_colors.get(row['sector'], "#CCCCCC")
    net.add_node(row['firm_master_id'], label=row['canonical_name'], title=f"{row['canonical_name']} ({row['sector']})", color=color, size=15)

edges_added = set()
for _, row in df_edges.iterrows():
    edge = tuple(sorted([row['source'], row['target']]))
    if edge not in edges_added:
        net.add_edge(row['source'], row['target'], color="#E0E0E0")
        edges_added.add(edge)

net.save_graph("network.html")
with open("network.html", "r", encoding="utf-8") as f:
    components.html(f.read(), height=500)

st.divider()

# ==========================================
# 3. RM CAPACITY & QUOTA
# ==========================================
st.subheader("Relationship Manager Quota Attainment")
query_rm = "SELECT rm_id, portfolio_size, total_revenue, quota, attainment_pct FROM gold.fct_rm_quota ORDER BY total_revenue DESC"
df_rm = run_query(query_rm)

if not df_rm.empty:
    fig_quota = px.bar(
        df_rm, 
        x='rm_id', 
        y='total_revenue', 
        text='attainment_pct', 
        title="RM Revenue vs Quota", 
        labels={'rm_id': 'Relationship Manager ID', 'total_revenue': 'Revenue (USD M)'}
    )
    # Apply formatting ONLY to the bar chart trace
    fig_quota.update_traces(
        texttemplate='%{text:.1f}%', 
        textposition='outside',
        selector=dict(type='bar') # <--- This prevents the error on the scatter trace
    )
    # Add the red quota line
    fig_quota.add_scatter(
        x=df_rm['rm_id'], 
        y=df_rm['quota'], 
        mode='markers', 
        name='Quota Target', 
        marker=dict(color='red', size=12, symbol='line-ew')
    )
    st.plotly_chart(fig_quota, use_container_width=True)