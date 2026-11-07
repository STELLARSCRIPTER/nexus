import streamlit as st
import plotly.express as px
import pandas as pd
from components.db import run_query

st.set_page_config(layout="wide")

st.title("📈 Deal Intelligence")
st.markdown("Monitor the deal pipeline, stage conversion, and opportunity prioritization.")

# ==========================================
# 1. Pipeline Volume
# ==========================================
st.subheader("Current Deal Volume by Stage")
st.markdown("Unlike a sequential funnel, this bar chart shows the exact number of **unique deals currently sitting in each stage**.")

query_pipeline = """
SELECT current_stage, COUNT(*) as deal_count, SUM(deal_size_usd_m) as total_value
FROM bronze.raw_deals
GROUP BY current_stage
"""
df_pipeline = run_query(query_pipeline)

stage_order = ["Sourced", "Screening", "IOI", "Due Diligence", "Negotiation", "Closed", "Dead"]
df_pipeline['stage_order'] = df_pipeline['current_stage'].apply(lambda x: stage_order.index(x) if x in stage_order else 99)
df_pipeline = df_pipeline.sort_values('stage_order')

fig_bar = px.bar(
    df_pipeline,
    x='current_stage',
    y='deal_count',
    text='deal_count',
    title="Current Deal Count by Pipeline Stage",
    color='deal_count',
    color_continuous_scale="Blues"
)
fig_bar.update_traces(textposition='outside')
fig_bar.update_layout(xaxis_title="Pipeline Stage", yaxis_title="Number of Deals", coloraxis_showscale=False)
st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 2. Deal Size Distribution
# ==========================================
st.subheader("Deal Size Distribution")
query_sizes = "SELECT deal_size_usd_m, deal_type FROM bronze.raw_deals WHERE deal_size_usd_m > 0"
df_sizes = run_query(query_sizes)

fig_box = px.box(
    df_sizes, 
    x="deal_type", 
    y="deal_size_usd_m",
    color="deal_type",
    log_y=True,
    title="Distribution of Deal Sizes (Log Scale)",
    labels={"deal_type": "Deal Type", "deal_size_usd_m": "Deal Size (USD M)"}
)
st.plotly_chart(fig_box, use_container_width=True)

st.divider()

# ==========================================
# 3. Regression Analysis
# ==========================================
st.subheader("Statistical Drivers of Win Rate")
st.markdown("""
Using **Logistic Regression**, we analyzed which variables statistically impact the probability of a deal closing. 
The **Odds Ratio** tells us how much a 1-unit increase in the variable changes the odds of winning.
""")

query_reg = "SELECT variable, coefficient, p_value, odds_ratio FROM gold.fct_deal_regression ORDER BY odds_ratio DESC"
df_reg = run_query(query_reg)

if not df_reg.empty:
    df_reg['variable'] = df_reg['variable'].str.replace('deal_type_', 'Type: ')
    st.dataframe(
        df_reg.style.format({"coefficient": "{:.4f}", "p_value": "{:.4f}", "odds_ratio": "{:.3f}"}).background_gradient(subset=["odds_ratio"], cmap="coolwarm"),
        use_container_width=True,
        hide_index=True
    )