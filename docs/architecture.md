# NEXUS Data Architecture

## Medallion Architecture
The platform is built on a standard 3-tier data lakehouse architecture to ensure data quality and traceability.

1. **Bronze (Raw Ingestion):** 
   - Data is generated via Python (`src/generation`).
   - Loaded into PostgreSQL as raw text tables (`bronze.raw_*`).
   - Includes audit columns (`_loaded_at`, `_source_file`).
   - Contains deliberately injected defects (duplicate names, orphaned deals).

2. **Silver (Cleansed & Conformed):**
   - Deduplication and Entity Resolution (Module A).
   - Creates the Master Data Management (MDM) tables.
   - `silver.dim_firms`: The canonical list of 22,672 unique institutions.
   - `silver.firm_id_mapping`: A lookup table mapping the messy Bronze IDs to the clean Silver IDs.

3. **Gold (Analytics & Quant):**
   - Business-level aggregates and machine learning outputs.
   - `gold.fct_relationship_intelligence`: Engagement scores.
   - `gold.fct_revenue_intelligence`: HHI concentration and total revenue.
   - `gold.fct_predictive_risk`: XGBoost churn probabilities.
   - `gold.fct_network_centrality`: Graph theory metrics.
   - `gold.fct_anomaly_alerts`: Isolation Forest outlier flags.
   - `gold.fct_monte_carlo_revenue`: 10,000 simulated future revenue states.

## Tech Stack
- **Database:** PostgreSQL
- **Pipeline:** Python, Pandas, SQLAlchemy
- **Machine Learning:** Scikit-Learn, XGBoost, NetworkX
- **Frontend:** Streamlit, Plotly