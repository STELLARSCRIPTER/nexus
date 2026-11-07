import numpy as np
import pandas as pd
from src.utils.rng import get_rng, random_dates

INTERACTION_TYPES = ["Meeting", "Email", "Call", "Event"]

def generate(cfg: dict, firm_contact_df: pd.DataFrame) -> pd.DataFrame:
    n_interactions = cfg["volumes"]["interactions"]
    r = get_rng(cfg["seed"] + 7)

    # We sample from the firm_contact links so interactions are always tied to a real relationship
    sampled_links = firm_contact_df.sample(n=n_interactions, replace=True, random_state=cfg["seed"]).reset_index(drop=True)
    
    # Interaction dates: weighted more heavily towards recent years
    dates = random_dates(r, cfg["date_range"]["start"], cfg["date_range"]["end"], n_interactions)

    df = pd.DataFrame({
        "interaction_id": [f"I{i:09d}" for i in range(1, n_interactions + 1)],
        "contact_id": sampled_links["contact_id"],
        "firm_id": sampled_links["firm_id"],
        "interaction_type": r.choice(INTERACTION_TYPES, size=n_interactions, p=[0.2, 0.6, 0.15, 0.05]),
        "interaction_date": dates,
        "duration_mins": np.where(
            r.random(n_interactions) < 0.5, 0, r.integers(15, 120, size=n_interactions)
        ), # Emails have 0 duration, calls/meetings have 15-120 mins
        "is_synthetic": True,
        "synthetic_batch_id": f"batch_{cfg['seed']}"
    })
    
    # Sort chronologically to mimic real logs
    df = df.sort_values("interaction_date").reset_index(drop=True)
    return df   