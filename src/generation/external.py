import numpy as np
import pandas as pd
from src.utils.rng import get_rng

def generate(cfg: dict, firms_df: pd.DataFrame) -> pd.DataFrame:
    n_obs = cfg["volumes"]["external_observations"]
    r = get_rng(cfg["seed"] + 11)

    # Generate market indicators (like an index)
    dates = pd.date_range(start=cfg["date_range"]["start"], end=cfg["date_range"]["end"], freq='D')
    
    # Pick random firms and assign them a market sensitivity score over time
    sampled_firms = r.choice(firms_df["firm_id"].to_numpy(), size=n_obs)
    sampled_dates = r.choice(dates, size=n_obs)

    df = pd.DataFrame({
        "observation_id": [f"EXT{i:07d}" for i in range(1, n_obs + 1)],
        "firm_id": sampled_firms,
        "observation_date": sampled_dates,
        "market_index": np.round(r.normal(loc=100, scale=15, size=n_obs), 2),
        "sector_volatility": np.round(r.uniform(0.1, 0.9, size=n_obs), 2),
        "is_synthetic": True
    })
    
    return df