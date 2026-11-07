import pytest
from src.utils.db import get_engine
from sqlalchemy import text

@pytest.fixture
def engine():
    return get_engine()

def test_ml_predictions_exist(engine):
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM gold.fct_predictive_risk")).scalar()
        assert count > 0, "No ML predictions found in the Gold layer."
        
        # Check that probabilities are between 0 and 1
        invalid_probs = conn.execute(text("SELECT COUNT(*) FROM gold.fct_predictive_risk WHERE risk_probability < 0 OR risk_probability > 1")).scalar()
        assert invalid_probs == 0, "ML model produced invalid probabilities outside [0, 1]."
        print("\n✅ ML Test Passed: Predictions exist and are mathematically valid.")

def test_network_centrality(engine):
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM gold.fct_network_centrality")).scalar()
        assert count > 0, "Network graph metrics missing."
        print("\n✅ Network Test Passed: Centrality metrics generated.")