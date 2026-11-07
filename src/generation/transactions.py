import numpy as np
import pandas as pd
from src.utils.rng import get_rng

BASE_FEE_BPS = {
    "M&A": 150, "LBO": 120, "Growth Equity": 100,
    "Venture": 80, "Recapitalisation": 110
}

def generate(cfg: dict, deals_df: pd.DataFrame, firms_df: pd.DataFrame) -> pd.DataFrame:
    r = get_rng(cfg["seed"] + 5)
    closed_deals = deals_df[deals_df["current_stage"] == "Closed"].copy()

    records = []
    for i, (_, deal) in enumerate(closed_deals.iterrows(), start=1):
        bps = BASE_FEE_BPS.get(deal["deal_type"], 100)
        # Fee = deal size * basis points * noise
        fee = deal["deal_size_usd_m"] * (bps / 10000) * r.lognormal(0, 0.15)
        
        # Transaction settles 30-180 days after announcement
        tx_date = np.datetime64(deal["announced_date"]) + np.timedelta64(int(r.integers(30, 180)), 'D')
        
        records.append({
            "transaction_id": f"T{i:08d}",
            "deal_id": deal["deal_id"],
            "firm_id": deal["originator_firm_id"],
            "transaction_date": tx_date,
            "amount_usd_m": round(float(fee), 6),
            "transaction_type": "advisory_fee",
            "is_synthetic": True,
            "synthetic_batch_id": f"batch_{cfg['seed']}"
        })

    tx_df = pd.DataFrame(records)
    n_target = cfg["volumes"]["transactions"]

    # Pad with recurring retainers if we don't have enough closed deals
    if len(tx_df) < n_target:
        n_pad = n_target - len(tx_df)
        pad_firms = r.choice(firms_df["firm_id"].to_numpy(), size=n_pad)
        pad_dates = r.choice(tx_df["transaction_date"].to_numpy(), size=n_pad) if len(tx_df) else np.repeat(np.datetime64("2023-01-01"), n_pad)
        
        pad_records = pd.DataFrame({
            "transaction_id": [f"T{len(tx_df)+i+1:08d}" for i in range(n_pad)],
            "deal_id": None,
            "firm_id": pad_firms,
            "transaction_date": pad_dates,
            "amount_usd_m": np.round(r.lognormal(mean=-1.0, sigma=1.0, size=n_pad), 6),
            "transaction_type": r.choice(["retainer", "monitoring_fee", "success_fee"], size=n_pad),
            "is_synthetic": True,
            "synthetic_batch_id": f"batch_{cfg['seed']}"
        })
        tx_df = pd.concat([tx_df, pad_records], ignore_index=True)

    return tx_df.head(n_target).reset_index(drop=True)

def generate_fees(cfg: dict, tx_df: pd.DataFrame) -> pd.DataFrame:
    """Splits transactions into smaller fee components."""
    n_target = cfg["volumes"]["fee_records"]
    r = get_rng(cfg["seed"] + 6)

    records = []
    fee_id = 1
    fee_types = ["base_fee", "incentive_fee", "reimbursement"]
    fee_probs = [0.6, 0.25, 0.15]

    for _, tx in tx_df.iterrows():
        n_components = int(r.integers(1, 4))
        shares = r.dirichlet(np.ones(n_components)) # Sums to 1.0
        
        for i in range(n_components):
            records.append({
                "fee_id": f"FE{fee_id:09d}",
                "transaction_id": tx["transaction_id"],
                "fee_type": r.choice(fee_types, p=fee_probs),
                "amount_usd_m": round(float(tx["amount_usd_m"]) * shares[i], 8),
                "is_synthetic": True,
                "synthetic_batch_id": f"batch_{cfg['seed']}"
            })
            fee_id += 1
            if fee_id > n_target:
                break
        if fee_id > n_target:
            break

    return pd.DataFrame(records)