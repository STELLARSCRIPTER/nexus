import pandas as pd
from src.generation import firms

def test_firm_generation():
    # Mock config
    cfg = {
        "seed": 42,
        "volumes": {"firms": 100}
    }
    
    df = firms.generate(cfg)
    
    # Assertions
    assert len(df) == 100
    assert "firm_id" in df.columns
    assert "legal_name" in df.columns
    assert df["aum_usd_m"].min() > 0
    assert df["is_synthetic"].all() == True
    print("\n✅ Generator Test Passed: Data is structured correctly.")