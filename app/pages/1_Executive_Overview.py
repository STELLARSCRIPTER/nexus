import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from components.db import run_query



st.set_page_config(layout="wide", page_title="NEXUS | Executive Overview")

st.title(" NEXUS Institutional Intelligence")
st.markdown("Connecting data to decisions: A unified view of institutional performance, risks, and opportunities.")

# ==========================================
# 1. SIDEBAR FILTERS
# ==========================================
st.sidebar.header("Global Filters")

# Fetch sectors dynamically
sectors_df = run_query("SELECT DISTINCT sector FROM gold.dim_firm ORDER BY sector")
sector_list = sectors_df['sector'].tolist()

selected_sectors = st.sidebar.multiselect(
    "Institutional Sector",
    options=sector_list,
    default=sector_list
)

min_rev = st.sidebar.slider(
    "Minimum Historical Revenue (USD M)",
    min_value=0,
    max_value=1000,
    value=0,
    step=50
)

# Prepare SQL string for the IN clause
if selected_sectors:
    sector_sql = "(" + ", ".join([f"'{s}'" for s in selected_sectors]) + ")"
else:
    sector_sql = "('')"

# ==========================================
# 2. TOP KPI CARDS (Filtered)
# ==========================================
# FIX: Calculates Expected Pipeline Revenue (Deal Size * 1.5% Fee)
query_kpis = f"""
WITH filtered_firms AS (
    SELECT f.firm_master_id 
    FROM gold.dim_firm f
    JOIN gold.fct_revenue_intelligence r ON f.firm_master_id = r.firm_master_id
    WHERE f.sector IN {sector_sql}
    AND r.total_revenue_usd_m >= {min_rev}
)
SELECT 
    (SELECT COUNT(*) FROM filtered_firms) AS total_institutions,
    (SELECT COUNT(*) FROM gold.fct_relationship_intelligence i 
     JOIN filtered_firms f ON i.firm_master_id = f.firm_master_id 
     WHERE i.relationship_score > 30) AS active_relationships,
    (SELECT SUM(total_revenue_usd_m) FROM gold.fct_revenue_intelligence r 
     JOIN filtered_firms f ON r.firm_master_id = f.firm_master_id) AS total_revenue,
    (SELECT SUM(d.deal_size_usd_m * 0.015) FROM bronze.raw_deals d
     JOIN silver.firm_id_mapping m ON d.originator_firm_id = m.firm_id
     JOIN gold.dim_firm gf ON m.firm_master_id = gf.firm_master_id
     WHERE gf.sector IN {sector_sql} AND d.current_stage NOT IN ('Closed', 'Dead')) AS expected_pipeline_rev
"""
kpis = run_query(query_kpis).iloc[0]

# Formatting helpers
rev_val = kpis['total_revenue'] if pd.notna(kpis['total_revenue']) else 0
rev_display = f"${rev_val / 1000:,.2f}B" if rev_val > 1000 else f"${rev_val:,.1f}M"

# FIX: Formatting expected pipeline rev correctly
pipe_val = kpis['expected_pipeline_rev'] if pd.notna(kpis['expected_pipeline_rev']) else 0
pipe_display = f"${pipe_val / 1000:,.2f}B" if pipe_val > 1000 else f"${pipe_val:,.1f}M"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Institutions Tracked", f"{int(kpis['total_institutions']):,}", "Filtered")
col2.metric("Active Relationships", f"{int(kpis['active_relationships']):,}", "Score > 30")
col3.metric("Revenue (Filtered)", rev_display, "Simulated")
col4.metric("Expected Pipeline Rev", pipe_display, "Win Rate * 1.5% Fee")

st.divider()

# ==========================================
# 3. MIDDLE ROW: Network & Forecast
# ==========================================
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("Top Network Connections")
    st.markdown("High-centrality institutions based on Deal Flow graph.")
    
    query_network = f"""
    SELECT 
        f.canonical_name,
        n.degree_centrality,
        n.betweenness_centrality,
        f.sector
    FROM gold.fct_network_centrality n
    JOIN gold.dim_firm f ON n.firm_master_id = f.firm_master_id
    WHERE f.sector IN {sector_sql}
    ORDER BY n.degree_centrality DESC
    LIMIT 30
    """
    df_network = run_query(query_network)
    
    if not df_network.empty:
        fig_net = px.scatter(
            df_network, 
            x="degree_centrality", 
            y="betweenness_centrality",
            size="degree_centrality",
            color="sector",
            hover_name="canonical_name",
            size_max=40
        )
        fig_net.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=350,
            showlegend=False,
            xaxis_title="Degree (Direct Deals)",
            yaxis_title="Betweenness (Bridges)"
        )
        st.plotly_chart(fig_net, use_container_width=True)
    else:
        st.warning("No network data matches the current filters.")

with col_right:
    st.subheader("Revenue Forecast (90d)")
    st.markdown("Monte Carlo Simulation (10k iterations).")
    
    query_mc = "SELECT simulated_revenue_usd_m FROM gold.fct_monte_carlo_revenue"
    df_mc = run_query(query_mc)
    
    # Scale the Monte Carlo forecast dynamically based on the filtered revenue
    total_base_rev = run_query("SELECT SUM(total_revenue_usd_m) as total FROM gold.fct_revenue_intelligence").iloc[0]['total']
    scaling_factor = rev_val / total_base_rev if total_base_rev > 0 else 0
    
    df_mc['scaled_revenue'] = df_mc['simulated_revenue_usd_m'] * scaling_factor
    mean_rev = df_mc['scaled_revenue'].mean()
    
    fig_mc = px.histogram(df_mc, x="scaled_revenue", nbins=50, color_discrete_sequence=['#636EFA'])
    fig_mc.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=200,
        showlegend=False,
        xaxis_title="Simulated Revenue (USD M)",
        yaxis_title=None
    )
    fig_mc.update_yaxes(showticklabels=False)
    st.plotly_chart(fig_mc, use_container_width=True)
    
    st.metric("Expected Revenue (Next 90d)", f"${mean_rev:.1f}M")

st.divider()

# ==========================================
# 4. BOTTOM ROW: Key Business Insights & Anomalies
# ==========================================
col_insights, col_alerts = st.columns([1, 1])

with col_insights:
    st.subheader("Key Business Insights")
    
    # Dynamically calculate insights based on the filtered data
    query_hhi = f"""
    SELECT SUM(r.hhi_contribution) as total_hhi 
    FROM gold.fct_revenue_intelligence r
    JOIN gold.dim_firm f ON r.firm_master_id = f.firm_master_id
    WHERE f.sector IN {sector_sql}
    """
    total_hhi_df = run_query(query_hhi)
    total_hhi = total_hhi_df.iloc[0]['total_hhi'] if pd.notna(total_hhi_df.iloc[0]['total_hhi']) else 0
    
    query_top_rev = f"""
    SELECT SUM(total_revenue_usd_m) as top_10_rev 
    FROM (
        SELECT r.total_revenue_usd_m 
        FROM gold.fct_revenue_intelligence r
        JOIN gold.dim_firm f ON r.firm_master_id = f.firm_master_id
        WHERE f.sector IN {sector_sql}
        ORDER BY r.total_revenue_usd_m DESC LIMIT 10
    ) t
    """
    top_10_rev_df = run_query(query_top_rev)
    top_10_rev = top_10_rev_df.iloc[0]['top_10_rev'] if pd.notna(top_10_rev_df.iloc[0]['top_10_rev']) else 0
    
    pct_concentration = (top_10_rev / rev_val) * 100 if rev_val > 0 else 0
    
    st.success(f"**Revenue Concentration:** Top 10 filtered institutions represent **{pct_concentration:.1f}%** of the filtered revenue (HHI: {total_hhi:.2f}).")
    
    query_at_risk = f"""
    SELECT COUNT(*) as count FROM gold.fct_predictive_risk p
    JOIN gold.dim_firm f ON p.firm_master_id = f.firm_master_id
    WHERE p.risk_probability > 0.7 AND f.sector IN {sector_sql}
    """
    at_risk_count = run_query(query_at_risk).iloc[0]['count']
    st.warning(f"**Churn Risk:** **{int(at_risk_count):,}** filtered firms have a >70% probability of becoming inactive in the next 90 days.")
    
    st.info("**Deal Pipeline:** M&A advisory remains the dominant revenue driver across the selected sectors.")

with col_alerts:
    st.subheader(" Critical Anomalies")
    st.markdown("Transactions flagged by Isolation Forest.")
    
    query_anomalies = f"""
    SELECT 
        f.canonical_name,
        a.amount_usd_m,
        a.transaction_date
    FROM gold.fct_anomaly_alerts a
    JOIN gold.dim_firm f ON a.firm_master_id = f.firm_master_id
    WHERE f.sector IN {sector_sql}
    ORDER BY a.amount_usd_m DESC
    LIMIT 5
    """
    df_anomalies = run_query(query_anomalies)
    
    if len(df_anomalies) > 0:
        st.dataframe(
            df_anomalies.style.format({"amount_usd_m": "${:,.1f}M"}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("No anomalies detected for the selected sectors.")

st.divider()

# ==========================================
# 5. THE SANKEY DIAGRAM (Deal Pipeline Flow)
# ==========================================
st.subheader("Deal Pipeline Flow (Sankey)")
st.markdown("How deal volume flows from initial sourcing through the pipeline stages, segmented by deal type.")

# Note: The Sankey uses the raw deals, but we can filter it by sector if we join the originator
query_pipeline = f"""
SELECT d.current_stage, d.deal_type, COUNT(*) as count
FROM bronze.raw_deals d
JOIN silver.firm_id_mapping m ON d.originator_firm_id = m.firm_id
JOIN gold.dim_firm f ON m.firm_master_id = f.firm_master_id
WHERE f.sector IN {sector_sql}
GROUP BY d.current_stage, d.deal_type
"""
df_pipeline = run_query(query_pipeline)

if not df_pipeline.empty:
    # Format for Sankey
    stages = df_pipeline['current_stage'].unique().tolist()
    types = df_pipeline['deal_type'].unique().tolist()
    labels = types + stages

    source = [types.index(t) for t in df_pipeline['deal_type']]
    target = [len(types) + stages.index(s) for s in df_pipeline['current_stage']]
    values = df_pipeline['count'].tolist()

    # Color mapping for a professional look
    node_colors = ["#4A90E2"] * len(types) + ["#50E3C2"] * len(stages)

    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15, 
            thickness=20, 
            line=dict(color="black", width=0.5),
            label=labels, 
            color=node_colors
        ),
        link=dict(
            source=source, 
            target=target, 
            value=values, 
            color="rgba(74, 144, 226, 0.2)" # Light blue transparent links
        )
    )])

    fig_sankey.update_layout(
        height=500,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_sankey, use_container_width=True)
else:
    st.warning("No pipeline data available for the selected filters.")