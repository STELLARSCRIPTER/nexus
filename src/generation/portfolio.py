import numpy as np
import pandas as pd
from faker import Faker
from src.utils.rng import get_rng

def generate(cfg: dict, funds_df: pd.DataFrame) -> pd.DataFrame:
    n_companies = cfg["volumes"]["portfolio_companies"]
    fake = Faker()
    Faker.seed(cfg["seed"] + 9)
    r = get_rng(cfg["seed"] + 9)

    df = pd.DataFrame({
        "company_id": [f"PC{i:05d}" for i in range(1, n_companies + 1)],
        "company_name": [fake.company() for _ in range(n_companies)],
        "fund_id": r.choice(funds_df["fund_id"].to_numpy(), size=n_companies),
        "industry": r.choice(["Tech", "Healthcare", "Industrials", "Consumer", "Finance"], size=n_companies),
        "investment_size_usd_m": np.round(r.lognormal(mean=1.5, sigma=1.0, size=n_companies), 2),
        "current_valuation_usd_m": np.round(r.lognormal(mean=2.0, sigma=1.2, size=n_companies), 2),
        "is_synthetic": True
    })
    return df