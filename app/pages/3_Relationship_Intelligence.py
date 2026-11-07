import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from components.db import run_query

st.set_page_config(layout="wide")

st.title(" Revenue Intelligence & RevOps")
st.markdown("Analyze commercial performance, deal efficiency, and revenue concentration.")

# ==========================================
# 1. REVOPS KPI CARDS
# ==========================================
query_arpr = """
SELECT 
    SUM(total_revenue_usd_m) / COUNT(CASE WHEN total_revenue_usd_m > 0 THEN 1 END) as arpr,
    SUM(total_revenue_usd_m) as total_rev,
    COUNT(CASE WHEN total_revenue_usd_m > 0 THEN 1 END) as active_clients
FROM gold.fct_revenue_intelligence
"""
arpr_data = run_query(query_arpr).iloc[0]
arpr = arpr_data['arpr'] if pd.notna(arpr_data['arpr']) else 0

query_win_rate = """
SELECT 
    COUNT(CASE WHEN current_stage = 'Closed' THEN 1 END) as closed_deals,
    COUNT(CASE WHEN current_stage IN ('Closed', 'Dead') THEN 1 END) as total_resolved_deals
FROM bronze.raw_deals
"""
win_data = run_query(query_win_rate).iloc[0]
win_rate = (win_data['closed_deals'] / win_data['total_resolved_deals']) * 100 if win_data['total_resolved_deals'] > 0 else 0

query_hhi = "SELECT SUM(hhi_contribution) as total_hhi FROM gold.fct_revenue_intelligence"
total_hhi = run_query(query_hhi).iloc[0]['total_hhi'] or 0

col1, col2, col3 = st.columns(3)
col1.metric("Avg Revenue per Relationship (ARPR)", f"${arpr:,.1f}M", help="Total Revenue / Active Revenue-Generating Clients")
col2.metric("Deal Win Rate", f"{win_rate:.1f}%", help="Closed Deals / (Closed + Dead Deals)")
col3.metric("HHI Concentration", f"{total_hhi:.0f}", help="Herfindahl-Hirschman Index. Higher means revenue is concentrated in fewer clients.")

st.divider()

# ==========================================
# 2. CHARTS
# ==========================================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Revenue Breakdown by Sector")
    query_sector = """
    SELECT f.sector, SUM(r.total_revenue_usd_m) AS revenue
    FROM gold.fct_revenue_intelligence r
    JOIN gold.dim_firm f ON r.firm_master_id = f.firm_master_id
    WHERE r.total_revenue_usd_m > 0
    GROUP BY f.sector
    """
    df_sector = run_query(query_sector)
    fig_tree = px.treemap(df_sector, path=['sector'], values='revenue', color='revenue', color_continuous_scale='Blues')
    fig_tree.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=400)
    st.plotly_chart(fig_tree, use_container_width=True)

with col_right:
    st.subheader("Deal Win Rate by Type")
    query_win_type = """
    SELECT deal_type, COUNT(CASE WHEN current_stage = 'Closed' THEN 1 END) as closed, COUNT(CASE WHEN current_stage = 'Dead' THEN 1 END) as dead
    FROM bronze.raw_deals
    WHERE current_stage IN ('Closed', 'Dead')
    GROUP BY deal_type
    """
    df_win = run_query(query_win_type)
    df_win['total'] = df_win['closed'] + df_win['dead']
    df_win['win_rate'] = (df_win['closed'] / df_win['total']) * 100
    df_win = df_win.sort_values('win_rate', ascending=False)
    
    fig_bar = px.bar(df_win, x='deal_type', y='win_rate', text='win_rate', title="Win Rate by Deal Type (%)", color='win_rate', color_continuous_scale='Teal')
    fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_bar.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=400, coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ==========================================
# 3. TOP REVENUE CLIENTS
# ==========================================
st.subheader("Top 15 Revenue-Generating Institutions")
query_top_rev = """
SELECT f.canonical_name, f.sector, r.total_revenue_usd_m, r.transaction_count
FROM gold.fct_revenue_intelligence r
JOIN gold.dim_firm f ON r.firm_master_id = f.firm_master_id
ORDER BY r.total_revenue_usd_m DESC LIMIT 15
"""
df_top_rev = run_query(query_top_rev)
st.dataframe(
    df_top_rev.style.format({"total_revenue_usd_m": "${:,.1f}M", "transaction_count": "{:,}"}).background_gradient(subset=["total_revenue_usd_m"], cmap="Greens"), 
    use_container_width=True, hide_index=True
)

st.divider()

# ==========================================
# 4. COHORT ANALYSIS (NRR)
# ==========================================
st.subheader("Revenue Retention by Cohort")
query_cohort = """
WITH first_tx AS (
    SELECT m.firm_master_id, MIN(EXTRACT(YEAR FROM t.transaction_date)::INT) as cohort_year
    FROM bronze.raw_transactions t
    JOIN silver.firm_id_mapping m ON t.firm_id = m.firm_id
    GROUP BY m.firm_master_id
),
yearly_rev AS (
    SELECT m.firm_master_id, EXTRACT(YEAR FROM t.transaction_date)::INT as tx_year, SUM(t.amount_usd_m) as revenue
    FROM bronze.raw_transactions t
    JOIN silver.firm_id_mapping m ON t.firm_id = m.firm_id
    GROUP BY m.firm_master_id, EXTRACT(YEAR FROM t.transaction_date)::INT
)
SELECT f.cohort_year, y.tx_year, SUM(y.revenue) as total_revenue
FROM first_tx f
JOIN yearly_rev y ON f.firm_master_id = y.firm_master_id
WHERE f.cohort_year >= 2019 AND f.cohort_year <= 2022
GROUP BY f.cohort_year, y.tx_year
ORDER BY f.cohort_year, y.tx_year
"""
df_cohort = run_query(query_cohort)

if not df_cohort.empty:
    pivot_df = df_cohort.pivot(index='cohort_year', columns='tx_year', values='total_revenue').fillna(0)
    for col in pivot_df.columns:
        first_year_rev = pivot_df.iloc[:, 0].replace(0, 1)
        pivot_df[col] = ((pivot_df[col] / first_year_rev) * 100).clip(upper=150)
        
    pivot_df.columns = pivot_df.columns.astype(str)
    pivot_df.index = pivot_df.index.astype(str)
    
    fig_cohort = px.imshow(
        pivot_df, labels=dict(x="Transaction Year", y="Cohort (Acquisition Year)", color="Retention (%)"),
        x=pivot_df.columns, y=pivot_df.index, color_continuous_scale="Blues", text_auto=".1f", aspect="auto"
    )
    fig_cohort.update_layout(height=400, title="Net Revenue Retention by Cohort (%)", margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_cohort, use_container_width=True)