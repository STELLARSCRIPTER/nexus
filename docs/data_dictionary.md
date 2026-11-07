# Data Dictionary

## Bronze Layer (Raw)
- `raw_firms`: The raw institutional data, including injected duplicates.
- `raw_deals`: Deal flow, including orphaned deals (missing originator).
- `raw_interactions`: CRM meetings, emails, and calls.
- `raw_transactions`: Financial fees and revenue events.

## Silver Layer (Cleaned)
- `dim_firms`: The clean master list of institutions.
  - `firm_master_id` (PK): The unique canonical ID.
  - `canonical_name`: The cleaned legal name.
- `firm_id_mapping`: Maps `firm_id` (Bronze) to `firm_master_id` (Silver).

## Gold Layer (Analytics)
- `fct_relationship_intelligence`: Engagement metrics (Relationship Score).
- `fct_revenue_intelligence`: Financial metrics (Total Revenue, HHI).
- `fct_predictive_risk`: ML predictions (Probability of 90-day churn).
- `fct_network_centrality`: Graph metrics (Degree, Betweenness).
- `fct_anomaly_alerts`: Isolation Forest flagged transactions.
- `fct_monte_carlo_revenue`: 10,000 simulated revenue outcomes.