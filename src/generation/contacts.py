import numpy as np
import pandas as pd
from faker import Faker
from src.utils.rng import get_rng

TITLES = ["Analyst", "Associate", "VP", "Director", "MD", "Partner", "CEO", "CIO"]
TITLE_PROBS = [0.20, 0.25, 0.20, 0.15, 0.10, 0.05, 0.03, 0.02]

def generate(cfg: dict, firms_df: pd.DataFrame) -> pd.DataFrame:
    n_contacts = cfg["volumes"]["contacts"]
    fake = Faker()
    Faker.seed(cfg["seed"] + 1)
    r = get_rng(cfg["seed"] + 1)

    # Probability of a contact belonging to a firm is weighted by that firm's AUM
    aum_weights = firms_df["aum_usd_m"].to_numpy()
    aum_probs = aum_weights / aum_weights.sum()
    
    primary_firms = r.choice(firms_df["firm_id"].to_numpy(), size=n_contacts, p=aum_probs)

    df = pd.DataFrame({
        "contact_id": [f"C{i:08d}" for i in range(1, n_contacts + 1)],
        "first_name": [fake.first_name() for _ in range(n_contacts)],
        "last_name": [fake.last_name() for _ in range(n_contacts)],
        "primary_firm_id": primary_firms,
        "title": r.choice(TITLES, size=n_contacts, p=TITLE_PROBS),
        "email": [fake.email() for _ in range(n_contacts)],
        "linkedin_url": [f"https://linkedin.com/in/{fake.user_name()}" for _ in range(n_contacts)],
        "is_synthetic": True,
        "synthetic_batch_id": f"batch_{cfg['seed']}"
    })
    return df

def generate_firm_contact(cfg: dict, firms_df: pd.DataFrame, contacts_df: pd.DataFrame) -> pd.DataFrame:
    """Generates the many-to-many relationship between firms and contacts."""
    n_links = cfg["volumes"]["firm_contact"]
    r = get_rng(cfg["seed"] + 2)

    # Start with the primary firm link for every contact
    primary_links = contacts_df[["contact_id", "primary_firm_id"]].rename(
        columns={"primary_firm_id": "firm_id"}
    )
    
    # We need to generate extra links. We'll keep generating until we hit the target.
    links_accumulated = [primary_links]
    current_count = len(primary_links)
    
    while current_count < n_links:
        # Generate in chunks to avoid memory issues if target is huge
        chunk_size = min(n_links - current_count, 50000) * 2 
        
        extra_firms = r.choice(firms_df["firm_id"].to_numpy(), size=chunk_size)
        extra_contacts = r.choice(contacts_df["contact_id"].to_numpy(), size=chunk_size)
        extra_links = pd.DataFrame({"contact_id": extra_contacts, "firm_id": extra_firms})
        
        links_accumulated.append(extra_links)
        
        # Combine and drop duplicates to see how many unique links we have now
        combined = pd.concat(links_accumulated, ignore_index=True)
        combined = combined.drop_duplicates(subset=["contact_id", "firm_id"])
        
        # Keep only the unique ones for the next iteration check
        links_accumulated = [combined]
        current_count = len(combined)

    # Once we have enough (or slightly more), trim to exact target
    all_links = links_accumulated[0].head(n_links).copy().reset_index(drop=True)

    all_links["relationship_type"] = r.choice(
        ["employee", "board_member", "advisor", "investor_contact"],
        size=n_links, p=[0.7, 0.1, 0.1, 0.1]
    )
    all_links["is_primary"] = ~all_links.duplicated(subset=["contact_id"])
    all_links["is_synthetic"] = True
    all_links["synthetic_batch_id"] = f"batch_{cfg['seed']}"
    
    return all_links