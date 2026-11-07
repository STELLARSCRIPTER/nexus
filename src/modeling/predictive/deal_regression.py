import pandas as pd
import numpy as np
import statsmodels.api as sm
from sqlalchemy import text
from src.utils.db import get_engine

def run_deal_regression():
    engine = get_engine()
    print("1. Fetching deal data...")
    
    # Fetch raw deals (we don't need to join market data for this basic regression)
    query = """
    SELECT 
        d.deal_id,
        d.deal_type,
        d.deal_size_usd_m,
        d.current_stage
    FROM bronze.raw_deals d
    WHERE d.current_stage IN ('Closed', 'Dead')
    """
    df = pd.read_sql(query, engine)
    
    print(f"   -> Loaded {len(df):,} resolved deals.")
    
    # Target: 1 if Closed, 0 if Dead
    df['is_closed'] = (df['current_stage'] == 'Closed').astype(int)
    
    # One-hot encode deal_type
    df = pd.get_dummies(df, columns=['deal_type'], drop_first=True, dtype=int)
    
    # Prepare X and y
    X = df.drop(columns=['deal_id', 'current_stage', 'is_closed'])
    y = df['is_closed']
    
    # Add constant for statsmodels
    X = sm.add_constant(X)
    
    print("2. Fitting Logistic Regression...")
    model = sm.Logit(y, X)
    result = model.fit(disp=0)
    
    # Extract coefficients and p-values
    df_results = pd.DataFrame({
        "variable": result.params.index,
        "coefficient": result.params.values,
        "p_value": result.pvalues.values,
        "odds_ratio": np.exp(result.params.values)
    })
    
    print("\nRegression Results:")
    print(df_results.to_string())
    
    # Save to gold
    print("\n3. Saving regression results...")
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
    df_results.to_sql("fct_deal_regression", engine, schema="gold", if_exists="replace", index=False)
    print("✅ Regression results saved to gold.fct_deal_regression")

if __name__ == "__main__":
    run_deal_regression()