import numpy as np
import pandas as pd
from faker import Faker
from src.utils.rng import get_rng

SECTORS = ["Private Equity", "Hedge Fund", "Family Office", "Pension Fund",
           "Investment Bank", "Advisory", "Law Firm", "Consultancy", "Sovereign Wealth"]
REGIONS = ["North America", "Europe", "Asia-Pacific", "Middle East", "LATAM"]
SUFFIXES = ["Partners", "Capital", "Holdings", "Advisors", "Group"]

def generate(cfg: dict) -> pd.DataFrame:
    n_firms = cfg["volumes"]["firms"]
    fake = Faker()
    Faker.seed(cfg["seed"])
    r = get_rng(cfg["seed"])

    # Real-world institutional distribution is heavily skewed
    sector_probs = [0.30, 0.15, 0.12, 0.10, 0.10, 0.08, 0.05, 0.05, 0.05]
    region_probs = [0.45, 0.30, 0.15, 0.05, 0.05]

    # Generate base names
    base_names = [fake.company() for _ in range(n_firms)]
    suffixes = r.choice(SUFFIXES, size=n_firms)
    
    df = pd.DataFrame({
        "firm_id": [f"F{i:07d}" for i in range(1, n_firms + 1)],
        "legal_name": [f"{name} {suffix}" for name, suffix in zip(base_names, suffixes)],
        "sector": r.choice(SECTORS, size=n_firms, p=sector_probs),
        "region": r.choice(REGIONS, size=n_firms, p=region_probs),
        "country": [fake.country_code() for _ in range(n_firms)],
        # AUM follows a log-normal distribution (few massive firms, many small ones)
        "aum_usd_m": np.round(r.lognormal(mean=6.5, sigma=1.8, size=n_firms), 2),
        "founded_year": r.integers(1950, 2023, size=n_firms),
        "is_synthetic": True,
        "synthetic_batch_id": f"batch_{cfg['seed']}"
    })
    
    return df