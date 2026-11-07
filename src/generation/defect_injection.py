import numpy as np
import pandas as pd
from src.utils.rng import get_rng

def inject_firm_duplicates(cfg: dict, firms_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Creates duplicate firms with slightly misspelled names."""
    r = get_rng(cfg["seed"] + 99)
    n_dupes = int(len(firms_df) * cfg["defect_rates"]["duplicate_firm"])
    
    # Pick random firms to duplicate
    dupe_indices = r.choice(firms_df.index, size=n_dupes, replace=False)
    dupes = firms_df.loc[dupe_indices].copy()
    
    # Corrupt the names (Ltd vs Limited, Partners vs Ptnrs, etc.)
    new_names = []
    for name in dupes["legal_name"]:
        if "Partners" in name:
            new_names.append(name.replace("Partners", "Ptnrs"))
        elif "Capital" in name:
            new_names.append(name.replace("Capital", "Cap."))
        else:
            new_names.append(name + " Ltd.")
            
    dupes["legal_name"] = new_names
    dupes["firm_id"] = dupes["firm_id"] + "_DUP"
    
    # Ground truth: map the duplicate ID back to the original ID for evaluation later
    ground_truth = pd.DataFrame({
        "original_id": firms_df.loc[dupe_indices, "firm_id"].values,
        "duplicate_id": dupes["firm_id"].values,
        "defect_type": "duplicate_name"
    })
    
    combined_firms = pd.concat([firms_df, dupes], ignore_index=True)
    return combined_firms, ground_truth

def inject_orphaned_deals(cfg: dict, deals_df: pd.DataFrame) -> pd.DataFrame:
    """Removes the originator firm from some deals (simulating bad CRM data)."""
    r = get_rng(cfg["seed"] + 100)
    n_orphans = int(len(deals_df) * cfg["defect_rates"]["orphan_deal"])
    
    orphan_indices = r.choice(deals_df.index, size=n_orphans, replace=False)
    deals_df.loc[orphan_indices, "originator_firm_id"] = None
    return deals_df