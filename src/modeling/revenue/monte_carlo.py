import numpy as np
import pandas as pd
from sqlalchemy import text
from src.utils.db import get_engine

def run_monte_carlo(n_simulations=10000):
    engine = get_engine()
    
    print("1. Fetching historical deal data...")
    with engine.connect() as conn:
        df_deals = pd.read_sql("""
            SELECT deal_size_usd_m, current_stage 
            FROM bronze.raw_deals
            WHERE deal_size_usd_m > 0
        """, conn)
        
        df_fees = pd.read_sql("""
            SELECT SUM(amount_usd_m) as total_fees
            FROM bronze.raw_transactions
            WHERE transaction_type = 'advisory_fee'
        """, conn)

    # 2. Fit Distributions
    # Deal sizes follow a log-normal distribution
    deal_sizes = df_deals['deal_size_usd_m']
    log_deal_sizes = np.log(deal_sizes[deal_sizes > 0])
    mu = log_deal_sizes.mean()
    sigma = log_deal_sizes.std()
    
    # Win rate: Closed deals / Total deals
    win_rate = len(df_deals[df_deals['current_stage'] == 'Closed']) / len(df_deals)
    
    print(f"   -> Historical Mean Deal Size: ${np.exp(mu + (sigma**2)/2):.1f}M")
    print(f"   -> Historical Win Rate: {win_rate*100:.1f}%")
    
    # 3. Run Monte Carlo Simulation
    print(f"2. Running {n_simulations:,} simulations for the next 90 days...")
    np.random.seed(42)
    
    # Assume we source ~5% of our historical deal volume in the next 90 days
    # (This is an assumption that can be parameterized)
    avg_deals_per_quarter = len(df_deals) / 24 # 2 years of data
    future_deals_target = int(avg_deals_per_quarter * 0.10) # Simulate 10% of pipeline moving
    
    simulated_revenues = []
    
    for _ in range(n_simulations):
        # Draw number of deals sourced (Poisson distribution)
        n_sourced = np.random.poisson(future_deals_target)
        
        # Draw deal sizes (Log-normal)
        sizes = np.random.lognormal(mean=mu, sigma=sigma, size=n_sourced)
        
        # Draw whether each deal closes (Bernoulli with win rate)
        closes = np.random.binomial(1, win_rate, size=n_sourced)
        
        # Calculate revenue for this simulation
        # Assuming a 1.5% advisory fee on closed deals
        revenue = sum(sizes * closes) * 0.015
        simulated_revenues.append(revenue)
        
    simulated_revenues = np.array(simulated_revenues)
    
    # 4. Calculate Statistics
    mean_rev = np.mean(simulated_revenues)
    p5_rev = np.percentile(simulated_revenues, 5)
    p95_rev = np.percentile(simulated_revenues, 95)
    var_95 = mean_rev - p5_rev # Value at Risk
    
    print("\n3. Monte Carlo Results (Next 90 Days):")
    print(f"   -> Expected Revenue: ${mean_rev:.2f}M")
    print(f"   -> Best Case (95th %ile): ${p95_rev:.2f}M")
    print(f"   -> Worst Case (5th %ile): ${p5_rev:.2f}M")
    print(f"   -> Value at Risk (95% VaR): ${var_95:.2f}M")
    
    # 5. Save to Database
    df_out = pd.DataFrame({
        "simulation_id": range(1, n_simulations + 1),
        "simulated_revenue_usd_m": simulated_revenues
    })
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
        
    df_out.to_sql("fct_monte_carlo_revenue", engine, schema="gold", if_exists="replace", index=False)
    print("\n✅ Saved simulations to gold.fct_monte_carlo_revenue")

if __name__ == "__main__":
    run_monte_carlo()