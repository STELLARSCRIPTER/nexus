import yaml
from pathlib import Path
import pandas as pd
from src.utils.rng import init_seeds
from src.generation import (
    firms, contacts, deals, transactions, 
    interactions, commitments, portfolio, defect_injection, external
)

def run(config_path: str = "config/settings.yaml") -> None:
    cfg = yaml.safe_load(Path(config_path).read_text())
    init_seeds(cfg["seed"])
    
    out_dir = Path(cfg["paths"]["raw_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Generating: Firms (Clean)")
    firms_df = firms.generate(cfg)

    print("Generating: Contacts")
    contacts_df = contacts.generate(cfg, firms_df)

    print("Generating: Firm-Contact Links")
    firm_contact_df = contacts.generate_firm_contact(cfg, firms_df, contacts_df)

    print("Generating: Deals & Transactions")
    deals_df = deals.generate(cfg, firms_df)
    stages_df = deals.generate_stage_history(cfg, deals_df)
    tx_df = transactions.generate(cfg, deals_df, firms_df)
    fee_df = transactions.generate_fees(cfg, tx_df)

    print("Generating: CRM Interactions")
    interactions_df = interactions.generate(cfg, firm_contact_df)

    print("Generating: Investor & Portfolio Data")
    funds_df, commitments_df = commitments.generate(cfg, firms_df)
    portfolio_df = portfolio.generate(cfg, funds_df)

    print("Generating: External Market Observations")
    external_df = external.generate(cfg, firms_df)

    print("Injecting Data Defects (Duplicates & Orphans)...")
    firms_corrupted_df, ground_truth_df = defect_injection.inject_firm_duplicates(cfg, firms_df)
    deals_corrupted_df = defect_injection.inject_orphaned_deals(cfg, deals_df)

    print("Saving to CSV...")
    firms_corrupted_df.to_csv(out_dir / "firms.csv", index=False)
    ground_truth_df.to_csv(out_dir / "ground_truth.csv", index=False) 
    contacts_df.to_csv(out_dir / "contacts.csv", index=False)
    firm_contact_df.to_csv(out_dir / "firm_contact.csv", index=False)
    
    # Note: We save the corrupted deals, but the original stages/transactions still reference the original IDs
    deals_corrupted_df.to_csv(out_dir / "deals.csv", index=False) 
    
    stages_df.to_csv(out_dir / "deal_stage_history.csv", index=False)
    tx_df.to_csv(out_dir / "transactions.csv", index=False)
    fee_df.to_csv(out_dir / "fee_record.csv", index=False)
    interactions_df.to_csv(out_dir / "interactions.csv", index=False)
    funds_df.to_csv(out_dir / "funds.csv", index=False)
    commitments_df.to_csv(out_dir / "commitments.csv", index=False)
    portfolio_df.to_csv(out_dir / "portfolio_companies.csv", index=False)
    external_df.to_csv(out_dir / "external_observations.csv", index=False)

    print("\n✅ Full dataset generation complete (1.5M+ rows).")
    
if __name__ == "__main__":
    run()