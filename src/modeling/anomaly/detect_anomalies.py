import pandas as pd
import numpy as np
from sqlalchemy import text
from src.utils.db import get_engine
from sklearn.ensemble import IsolationForest

def detect_anomalies():
    engine = get_engine()
    
    print("1. Fetching transaction data...")
    with engine.connect() as conn:
        query = """
        SELECT 
            m.firm_master_id,
            t.amount_usd_m,
            t.transaction_date
        FROM bronze.raw_transactions t
        JOIN silver.firm_id_mapping m ON t.firm_id = m.firm_id
        WHERE t.transaction_type = 'advisory_fee'
        """
        df = pd.read_sql(query, conn)

    print(f"   -> Loaded {len(df):,} advisory fee transactions.")
    
    print("2. Detecting anomalies using Isolation Forest...")
    # Isolation Forest looks for data points that are "easy to isolate" (i.e., outliers)
    X = df[['amount_usd_m']]
    
    # Contamination = expected proportion of outliers. Let's assume 2%
    iso = IsolationForest(contamination=0.02, random_state=42)
    df['is_anomaly'] = iso.fit_predict(X)
    
    # In sklearn, -1 means anomaly, 1 means normal
    df['anomaly_score'] = iso.decision_function(X)
    df['is_anomaly'] = df['is_anomaly'] == -1
    
    # 3. Calculate thresholds for explainability
    q1 = df['amount_usd_m'].quantile(0.25)
    q3 = df['amount_usd_m'].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + (1.5 * iqr)
    
    print(f"   -> Found {df['is_anomaly'].sum():,} anomalous transactions.")
    
    # 4. Save to database
    print("3. Saving anomaly alerts to Gold layer...")
    df_alerts = df[df['is_anomaly']].copy()
    df_alerts = df_alerts.sort_values('anomaly_score')
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
        
    df_alerts.to_sql("fct_anomaly_alerts", engine, schema="gold", if_exists="replace", index=False)
    print("✅ Anomaly alerts saved to gold.fct_anomaly_alerts")

if __name__ == "__main__":
    detect_anomalies()