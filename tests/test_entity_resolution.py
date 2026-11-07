import pytest
from src.utils.db import get_engine
from sqlalchemy import text

@pytest.fixture
def engine():
    return get_engine()

def test_bronze_silver_counts(engine):
    with engine.connect() as conn:
        # Bronze should have more rows (due to injected duplicates)
        bronze_count = conn.execute(text("SELECT COUNT(*) FROM bronze.raw_firms")).scalar()
        # Silver should have fewer rows (duplicates merged)
        silver_count = conn.execute(text("SELECT COUNT(*) FROM silver.dim_firms")).scalar()
        
        assert bronze_count > silver_count, "Entity resolution failed to reduce duplicate count."
        print(f"\n✅ Entity Resolution Test Passed: Bronze ({bronze_count}) > Silver ({silver_count}).")

def test_orphaned_deals(engine):
    with engine.connect() as conn:
        # We injected defects, so there SHOULD be orphaned deals in bronze
        orphans = conn.execute(text("SELECT COUNT(*) FROM bronze.raw_deals WHERE originator_firm_id IS NULL")).scalar()
        assert orphans > 0, "Defect injection failed, no orphaned deals found."
        print(f"\n✅ Data Quality Test Passed: Found {orphans} intentionally orphaned deals.")