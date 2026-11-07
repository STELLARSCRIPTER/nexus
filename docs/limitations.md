# Limitations & Assumptions

## 1. Synthetic Data
The most critical limitation is that **all data is synthetic**. It was generated using `Faker` and `NumPy`. While it contains realistic business rules (e.g., revenue correlates with deal size, engagement decays over time), it does not reflect real market shocks, regulatory changes, or true human behavior.

## 2. Entity Resolution
Our fuzzy matching uses a strict 90% threshold on the Token Set Ratio. In a real enterprise, this would require a more sophisticated probabilistic model (like Splink or Dedupe) combined with human-in-the-loop review for edge cases (e.g., "Apple Inc" vs "Apple Records").

## 3. ML Target Definition
We defined "Inactivity" as zero logged interactions in 90 days. In reality, institutional finance relationships often go quiet for months during long due diligence periods, but this does not mean the relationship is dead. A survival analysis model (e.g., Cox Proportional Hazards) might be more mathematically appropriate than a simple binary classifier.