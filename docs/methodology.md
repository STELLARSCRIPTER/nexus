# Quantitative Methodology

## 1. Entity Resolution (Module A)
- **Problem:** Institutional names are messy (e.g., "Partners" vs "Ptnrs").
- **Method:** We use `RapidFuzz` (Token Set Ratio) to compare names within the same country. 
- **Threshold:** A similarity score of >90% triggers a match.
- **Outcome:** Successfully merged 2,300+ duplicates, reducing 25,000 raw records to 22,672 master entities.

## 2. Relationship Scoring (Module B)
- **Formula:** `(Recent Interactions / 99th Percentile) * 40 + (Unique Contacts / 99th Percentile) * 60`.
- **Why 99th Percentile?** Using the absolute maximum would allow a few "whale" firms to skew the denominator and crush the average score to zero. Capping at the 99th percentile ensures the score is robust to outliers.

## 3. Predictive Modeling (Module E)
- **Target:** `is_inactive_90d` (Will this firm have zero interactions in the next 90 days?).
- **Model:** XGBoost Classifier.
- **Validation:** Chronological Split (Train on older data, test on newer data) to prevent data leakage.
- **Insight:** Feature importance revealed that "Breadth of Contacts" (unique people spoken to) is a stronger predictor of retention than "Total Historical Revenue". If you only have one point of contact at a firm, you are highly likely to churn.

## 4. Monte Carlo Simulation (Revenue)
- **Distribution:** Deal sizes are modeled using a Log-Normal distribution. Win rates are modeled using a Bernoulli distribution.
- **Simulation:** 10,000 iterations drawing random samples to calculate Value at Risk (VaR) for the next 90 days.