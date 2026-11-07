import numpy as np
import pandas as pd
from src.utils.rng import get_rng, random_dates

def generate(cfg: dict, firms_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    n_funds = cfg["volumes"]["funds"]
    n_commitments = cfg["volumes"]["commitments"]
    r = get_rng(cfg["seed"] + 8)

    # 1. Generate Funds
    funds_df = pd.DataFrame({
        "fund_id": [f"FND{i:03d}" for i in range(1, n_funds + 1)],
        "fund_name": [f"Nexus Fund {i}" for i in range(1, n_funds + 1)],
        "vintage_year": r.integers(2015, 2024, size=n_funds),
        "target_size_usd_m": np.round(r.lognormal(mean=4.0, sigma=1.0, size=n_funds), 2),
        "is_synthetic": True
    })

    # 2. Generate Commitments (Which firm invested in which fund)
    investor_firms = r.choice(firms_df["firm_id"].to_numpy(), size=n_commitments)
    committed_funds = r.choice(funds_df["fund_id"].to_numpy(), size=n_commitments)
    
    commitments_df = pd.DataFrame({
        "commitment_id": [f"COM{i:07d}" for i in range(1, n_commitments + 1)],
        "investor_firm_id": investor_firms,
        "fund_id": committed_funds,
        "commitment_amount_usd_m": np.round(r.lognormal(mean=2.0, sigma=1.2, size=n_commitments), 2),
        "commitment_date": random_dates(r, "2015-01-01", "2023-12-31", n_commitments),
        "is_synthetic": True
    })
    
    return funds_df, commitments_df