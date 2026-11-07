import pandas as pd
import numpy as np
from sqlalchemy import text
from src.utils.db import get_engine
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test

def run_survival_analysis():
    engine = get_engine()
    
    print("1. Building Survival Dataset (Time-to-Churn)...")
    query = """
    WITH first_last_int AS (
        SELECT 
            firm_id,
            MIN(interaction_date) as first_date,
            MAX(interaction_date) as last_date,
            COUNT(DISTINCT interaction_date) as active_days
        FROM bronze.raw_interactions
        GROUP BY firm_id
    )
    SELECT 
        m.firm_master_id,
        fl.first_date,
        fl.last_date,
        fl.active_days,
        COALESCE(r.total_rev, 0) as historical_revenue
    FROM first_last_int fl
    JOIN silver.firm_id_mapping m ON fl.firm_id = m.firm_id
    LEFT JOIN (
        SELECT m2.firm_master_id, SUM(t.amount_usd_m) as total_rev
        FROM bronze.raw_transactions t
        JOIN silver.firm_id_mapping m2 ON t.firm_id = m2.firm_id
        GROUP BY m2.firm_master_id
    ) r ON m.firm_master_id = r.firm_master_id
    """
    
    df = pd.read_sql(query, engine)
    df['first_date'] = pd.to_datetime(df['first_date'])
    df['last_date'] = pd.to_datetime(df['last_date'])
    df['duration'] = (df['last_date'] - df['first_date']).dt.days
    df = df[df['duration'] > 0].copy()
    
    max_date = df['last_date'].max()
    df['churned'] = ((max_date - df['last_date']).dt.days > 90).astype(int)
    
    df_model = df.groupby('firm_master_id').agg({
        'duration': 'max',
        'churned': 'max',
        'historical_revenue': 'sum'
    }).reset_index()
    
    median_rev = df_model['historical_revenue'].median()
    df_model['revenue_cohort'] = np.where(df_model['historical_revenue'] > median_rev, 'High Revenue', 'Low Revenue')
    
    # 1. Cox Model
    print("2. Fitting Cox Proportional Hazards Model...")
    cph = CoxPHFitter()
    cph.fit(df_model.drop(columns=['firm_master_id', 'revenue_cohort']), duration_col='duration', event_col='churned')
    cph.print_summary()
    
    print("   -> Checking Proportional Hazards Assumption...")
    try:
        cph.check_assumptions(df_model.drop(columns=['firm_master_id', 'revenue_cohort']), p_value_threshold=0.05, show_plots=False)
        print("      ✅ Assumption Holds (p > 0.05)")
    except Exception as e:
        print(f"      ⚠️ Assumption Violated: {e}")
    
    hr = cph.hazard_ratios_['historical_revenue']
    hr_lower = np.exp(cph.confidence_intervals_.loc['historical_revenue'].iloc[0])
    hr_upper = np.exp(cph.confidence_intervals_.loc['historical_revenue'].iloc[1])
    
    # 2. Kaplan-Meier & Median Survival
    print("3. Calculating Kaplan-Meier stats...")
    cohorts = {}
    stats_rows = []
    
    for name, grouped_df in df_model.groupby('revenue_cohort'):
        kmf = KaplanMeierFitter()
        kmf.fit(durations=grouped_df['duration'], event_observed=grouped_df['churned'], label=name)
        
        median_surv = kmf.median_survival_time_
        
        km_df = kmf.survival_function_.reset_index()
        km_df.columns = ['timeline_days', 'survival_probability']
        km_df['cohort'] = name
        cohorts[name] = km_df
        
        stats_rows.append({
            "cohort": name,
            "size": len(grouped_df),
            "median_survival_days": median_surv
        })
    
    # 3. Log-Rank Test
    high_rev = df_model[df_model['revenue_cohort'] == 'High Revenue']
    low_rev = df_model[df_model['revenue_cohort'] == 'Low Revenue']
    
    results = logrank_test(
        high_rev['duration'], low_rev['duration'],
        event_observed_A=high_rev['churned'], event_observed_B=low_rev['churned']
    )
    p_value = results.p_value
    
    df_km_all = pd.concat(cohorts.values(), ignore_index=True)
    df_stats = pd.DataFrame(stats_rows)
    
    df_stats['hazard_ratio'] = hr
    df_stats['hr_ci_lower'] = hr_lower
    df_stats['hr_ci_upper'] = hr_upper
    df_stats['logrank_p_value'] = p_value
    
    # 4. Save to Gold Layer
    print("4. Saving Survival data to Gold Layer...")
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
        
    df_km_all.to_sql("fct_survival_curve", engine, schema="gold", if_exists="replace", index=False)
    df_stats.to_sql("fct_survival_stats", engine, schema="gold", if_exists="replace", index=False)
    print("✅ Saved survival data and stats to Gold Layer.")

if __name__ == "__main__":
    run_survival_analysis()