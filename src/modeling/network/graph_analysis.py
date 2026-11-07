import pandas as pd
import networkx as nx
from sqlalchemy import text
from src.utils.db import get_engine

def run_network_analysis():
    engine = get_engine()
    
    print("1. Fetching firm relationships from Bronze...")
    with engine.connect() as conn:
        # We use the Silver mapping to ensure we are looking at the Master Firms
        query = """
        SELECT 
            m1.firm_master_id AS source_firm,
            m2.firm_master_id AS target_firm
        FROM bronze.raw_deals d
        JOIN silver.firm_id_mapping m1 ON d.originator_firm_id = m1.firm_id
        JOIN silver.firm_id_mapping m2 ON d.counterparty_firm_id = m2.firm_id
        WHERE m1.firm_master_id != m2.firm_master_id
        """
        df_edges = pd.read_sql(query, conn)

    print(f"   -> Found {len(df_edges):,} deal relationships.")
    
    print("2. Building NetworkX Graph...")
    # Build undirected graph
    G = nx.from_pandas_edgelist(df_edges, 'source_firm', 'target_firm')
    
    print(f"   -> Graph has {G.number_of_nodes():,} nodes and {G.number_of_edges():,} edges.")
    
    print("3. Calculating Centrality Metrics...")
    # Degree centrality: How many direct connections does a firm have?
    degree_dict = nx.degree_centrality(G)
    
    # Betweenness centrality: How often is a firm a "bridge" between two other firms?
    # (Note: This can be slow on large graphs, so we use k-sampling)
    print("   -> Calculating Betweenness Centrality (sampled)...")
    betweenness_dict = nx.betweenness_centrality(G, k=500, seed=42)
    
    # 4. Save results
    print("4. Saving network metrics to Gold layer...")
    
    df_metrics = pd.DataFrame({
        "firm_master_id": list(degree_dict.keys()),
        "degree_centrality": list(degree_dict.values()),
        "betweenness_centrality": [betweenness_dict.get(node, 0) for node in degree_dict.keys()]
    })
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
        
    df_metrics.to_sql("fct_network_centrality", engine, schema="gold", if_exists="replace", index=False)
    print("✅ Network metrics saved to gold.fct_network_centrality")

if __name__ == "__main__":
    run_network_analysis()