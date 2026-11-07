import numpy as np
import random
from faker import Faker

def get_rng(seed: int) -> np.random.Generator:
    """Returns a seeded numpy generator for reproducible outputs."""
    return np.random.default_rng(seed)

def init_seeds(seed: int) -> None:
    """Sets the global seed across numpy, stdlib random, and faker."""
    np.random.seed(seed)
    random.seed(seed)
    Faker.seed(seed)

def random_dates(r: np.random.Generator, start: str, end: str, n: int) -> np.ndarray:
    """Generates a numpy array of random dates between start and end."""
    start_date = np.datetime64(start)
    end_date = np.datetime64(end)
    days_between = (end_date - start_date).astype('timedelta64[D]').astype(int)
    random_days = r.integers(0, days_between, size=n)
    return start_date + random_days.astype('timedelta64[D]')