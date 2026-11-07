import pandas as pd
import numpy as np
from sqlalchemy import text
from src.utils.db import get_engine
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score
from xgboost import XGBClassifier

def build_features_and_target(engine, snapshot_date="2024-01-01"):
    print(f"1. Building features as of {snapshot_date}...")
    
    snap = f"'{snapshot_date}'"
    future_window = f"'{pd.to_datetime(snapshot_date) + pd.Timedelta(days=90)}'"
    
    with engine.connect() as conn:
        # Added last_contact_date to calculate days_since_contact
        query_features = f"""
        WITH recent_interactions AS (
            SELECT 
                firm_id, 
                COUNT(*) as recent_int, 
                COUNT(DISTINCT contact_id) as recent_contacts,
                MAX(interaction_date) as last_contact_date
            FROM bronze.raw_interactions
            WHERE interaction_date >= DATE({snap}) - INTERVAL '180 days'
              AND interaction_date < DATE({snap})
            GROUP BY firm_id
        ),
        revenue AS (
            SELECT firm_id, SUM(amount_usd_m) as total_rev
            FROM bronze.raw_transactions
            WHERE transaction_date < DATE({snap})
            GROUP BY firm_id
        )
        SELECT 
            m.firm_master_id,
            COALESCE(ri.recent_int, 0) as recent_interactions,
            COALESCE(ri.recent_contacts, 0) as recent_contacts,
            COALESCE(DATE({snap}) - ri.last_contact_date, 999) as days_since_contact,
            COALESCE(r.total_rev, 0) as historical_revenue
        FROM silver.firm_id_mapping m
        LEFT JOIN recent_interactions ri ON m.firm_id = ri.firm_id
        LEFT JOIN revenue r ON m.firm_id = r.firm_id
        """
        df_features = pd.read_sql(query_features, conn)
        
        query_target = f"""
        SELECT DISTINCT firm_id
        FROM bronze.raw_interactions
        WHERE interaction_date >= DATE({snap})
          AND interaction_date < DATE({future_window})
        """
        df_active_future = pd.read_sql(query_target, conn)
        
        df_mapping = pd.read_sql("SELECT firm_id, firm_master_id FROM silver.firm_id_mapping", conn)
        active_master_ids = df_mapping[df_mapping['firm_id'].isin(df_active_future['firm_id'])]['firm_master_id']
        
    df_features['is_inactive_90d'] = (~df_features['firm_master_id'].isin(active_master_ids)).astype(int)
    
    df_model = df_features.groupby('firm_master_id').agg({
        'recent_interactions': 'sum',
        'recent_contacts': 'sum',
        'days_since_contact': 'min',
        'historical_revenue': 'sum',
        'is_inactive_90d': 'max'
    }).reset_index()
    
    return df_model

def train_and_evaluate():
    engine = get_engine()
    df = build_features_and_target(engine)
    
    print(f"   -> Dataset built: {len(df):,} unique firms.")
    print(f"   -> Churn Rate (Target=1): {df['is_inactive_90d'].mean()*100:.1f}%")
    
    X = df[['recent_interactions', 'recent_contacts', 'days_since_contact', 'historical_revenue']]
    y = df['is_inactive_90d']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("2. Training Models...")
    
    lr = LogisticRegression(class_weight='balanced', max_iter=1000)
    lr.fit(X_train, y_train)
    lr_preds = lr.predict_proba(X_test)[:, 1]
    lr_auc = roc_auc_score(y_test, lr_preds)
    
    xgb = XGBClassifier(
        n_estimators=100, 
        max_depth=4, 
        learning_rate=0.1, 
        scale_pos_weight=(len(y_train) - y_train.sum()) / y_train.sum(),
        random_state=42
    )
    xgb.fit(X_train, y_train)
    xgb_preds = xgb.predict_proba(X_test)[:, 1]
    xgb_auc = roc_auc_score(y_test, xgb_preds)
    
    print(f"   -> Logistic Regression AUC-ROC: {lr_auc:.3f}")
    print(f"   -> XGBoost AUC-ROC:             {xgb_auc:.3f}")
    
    print("3. Feature Importance (XGBoost):")
    importances = xgb.feature_importances_
    for feature, imp in zip(X.columns, importances):
        print(f"   -> {feature:25}: {imp:.3f}")
        
    print("4. Saving predictions to Gold Layer...")
    df['risk_probability'] = xgb.predict_proba(X)[:, 1]
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
        
    df_out = df[['firm_master_id', 'risk_probability', 'is_inactive_90d']]
    df_out.to_sql("fct_predictive_risk", engine, schema="gold", if_exists="replace", index=False)
    print("   -> Saved to gold.fct_predictive_risk")

if __name__ == "__main__":
    train_and_evaluate()