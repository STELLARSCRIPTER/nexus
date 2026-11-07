import numpy as np
import pandas as pd
from src.utils.rng import get_rng, random_dates

STAGES = ["Sourced", "Screening", "IOI", "Due Diligence", "Negotiation", "Closed", "Dead"]
STAGE_PROBS = [0.10, 0.15, 0.10, 0.25, 0.10, 0.20, 0.10]
DEAL_TYPES = ["M&A", "Growth Equity", "LBO", "Venture", "Recapitalisation"]

def generate(cfg: dict, firms_df: pd.DataFrame) -> pd.DataFrame:
    n_deals = cfg["volumes"]["deals"]
    r = get_rng(cfg["seed"] + 3)

    originators = r.choice(firms_df["firm_id"].to_numpy(), size=n_deals)
    counterparties = r.choice(firms_df["firm_id"].to_numpy(), size=n_deals)
    
    dates = random_dates(r, cfg["date_range"]["start"], cfg["date_range"]["end"], n_deals)
    sizes = np.round(r.lognormal(mean=3.5, sigma=1.2, size=n_deals), 2)
    
    stages = r.choice(STAGES, size=n_deals, p=STAGE_PROBS)
    
    # Business rule: Deals announced less than 180 days ago cannot be Closed/Dead
    today = np.datetime64("2025-11-01")
    days_old = (today - dates).astype('timedelta64[D]').astype(int)
    stages = np.where(days_old < 180, "Sourced", stages)

    df = pd.DataFrame({
        "deal_id": [f"D{i:07d}" for i in range(1, n_deals + 1)],
        "originator_firm_id": originators,
        "counterparty_firm_id": counterparties,
        "deal_type": r.choice(DEAL_TYPES, size=n_deals, p=[0.35, 0.25, 0.15, 0.15, 0.10]),
        "deal_size_usd_m": sizes,
        "announced_date": dates,
        "current_stage": stages,
        "is_synthetic": True,
        "synthetic_batch_id": f"batch_{cfg['seed']}"
    })
    return df

def generate_stage_history(cfg: dict, deals_df: pd.DataFrame) -> pd.DataFrame:
    """Walks each deal forward through its lifecycle stages."""
    n_target = cfg["volumes"]["deal_stage_history"]
    r = get_rng(cfg["seed"] + 4)
    stage_order = {s: i for i, s in enumerate(STAGES)}

    records = []
    hist_id = 1
    
    for _, deal in deals_df.iterrows():
        final_idx = stage_order[deal["current_stage"]]
        n_stages = max(1, final_idx + 1)
        
        # Progression gaps (days)
        gaps = r.integers(7, 90, size=n_stages)
        current_date = np.datetime64(deal["announced_date"])
        
        for i in range(n_stages):
            current_date += np.timedelta64(int(gaps[i]), 'D')
            records.append({
                "stage_history_id": f"SH{hist_id:09d}",
                "deal_id": deal["deal_id"],
                "stage": STAGES[i],
                "stage_entered_date": current_date,
                "is_synthetic": True,
                "synthetic_batch_id": f"batch_{cfg['seed']}"
            })
            hist_id += 1
            if hist_id > n_target:
                break
        if hist_id > n_target:
            break

    return pd.DataFrame(records)