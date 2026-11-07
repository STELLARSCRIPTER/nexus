# NEXUS: Institutional Relationship & Quantitative Intelligence Platform

**NEXUS** is an executive-level financial intelligence platform designed to simulate, analyze, and forecast the complex relationship networks of a Private Equity or institutional investment firm.

By transforming fragmented, intentionally dirty CRM, deal, and financial data into a unified analytical ecosystem, NEXUS provides actionable insights into relationship health, revenue concentration risk, machine learning predictions, and Monte Carlo forecasts.

> **Note on Data:** This project uses a custom-built, highly relational synthetic data generator (`Faker`, `NumPy`). It simulates 1.5+ million records and deliberately injects data quality defects (duplicates, missing IDs) to demonstrate a robust Entity Resolution pipeline. **No real client data is used.**

Portfolio Link - https://thisisnexus.streamlit.app/

---

## 🏗️ Architecture & Data Pipeline (Medallion Architecture)

The platform is built on a modern data stack using **PostgreSQL** and **Python**, following the Bronze/Silver/Gold data modeling pattern:

1. **Bronze Layer (Raw):** Ingests 1.5M+ raw synthetic records (Firms, Deals, Contacts, Transactions, Interactions). Contains deliberate real-world data defects (duplicate names, orphaned deals).

2. **Silver Layer (Cleaned):** Contains the Master Data Management (MDM) tables. Uses **Fuzzy String Matching (RapidFuzz)** to resolve duplicate firm names and establish a canonical `firm_master_id`.

3. **Gold Layer (Analytics):** The quantitative intelligence engine. Contains aggregated facts, relationship scores, network centrality metrics, ML predictions, and Monte Carlo simulations.

---

## 🧠 Quantitative Intelligence Engine (The Math)

Unlike traditional BI dashboards, NEXUS integrates several advanced mathematical and statistical models:

- **Module A: Entity Resolution:** Probabilistic matching using string similarity (Token Set Ratio) to deduplicate institutional entities, successfully merging 2,300+ duplicates.

- **Module B: Relationship Scoring:** An explainable, weighted scoring model based on engagement decay, frequency of interactions, and breadth of contacts.

- **Module D: Revenue & RevOps Intelligence:** Calculates the **Herfindahl-Hirschman Index (HHI)** for revenue concentration risk, Average Revenue Per Relationship (ARPR), and Net Revenue Retention (NRR) via Cohort Analysis.

- **Module E: Predictive Analytics (XGBoost):** A Gradient Boosted Tree model predicting the probability of a high-value client becoming inactive over the next 90 days, validated using chronological feature engineering.

- **Module F: Graph Network Analysis:** Utilizes `NetworkX` to calculate **Degree** and **Betweenness Centrality** across 48,000+ deal edges, identifying the most influential "bridge" firms in the ecosystem.

- **Module G: Anomaly Detection:** Implements `Isolation Forest` (unsupervised ML) to flag statistically anomalous deal transactions.

- **Survival Analysis:** Uses the **Kaplan-Meier Estimator** and **Cox Proportional Hazards** model (via `lifelines`) to model time-to-churn, accounting for censored data.

- **Monte Carlo Simulation:** Runs 10,000 simulations drawing from historical Log-Normal deal size distributions to calculate future Revenue Value at Risk (VaR).

---

## 💻 Tech Stack

| Category | Technologies |
|---|---|
| Data Generation | `Faker`, `NumPy` |
| Data Processing & Entity Resolution | `pandas`, `RapidFuzz` |
| Database | `PostgreSQL`, `SQLAlchemy` |
| Machine Learning | `scikit-learn`, `XGBoost` |
| Statistical Analysis | `SciPy`, `statsmodels`, `lifelines` |
| Network Analysis | `NetworkX` |
| Frontend / BI | `Streamlit`, `Plotly`, `pyvis` |

---

## 🚀 How to Run Locally

### 1. Prerequisites

- Python 3.10+
- PostgreSQL (running locally on port 5432)

### 2. Setup Database

Create a database and user in PostgreSQL:

```sql
CREATE DATABASE nexus;
CREATE USER nexus_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE nexus TO nexus_user;
```

### 3. Setup Environment

Clone the repository and install dependencies:

```bash
git clone https://github.com/STELLARSCRIPTER/nexus
cd nexus

python -m venv .venv
```

Activate the virtual environment:

**Windows:**

```bash
.venv\Scripts\activate
```

**Mac/Linux:**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the root directory:

```env
NEXUS_DB_HOST=localhost
NEXUS_DB_PORT=5432
NEXUS_DB_NAME=nexus
NEXUS_DB_USER=nexus_user
NEXUS_DB_PASSWORD=your_password
```

### 4. Generate & Load Data (Bronze Layer)

```bash
python -m src.generation.orchestrator
python -m src.ingestion.load_bronze
```

### 5. Run Entity Resolution (Silver) & Quant Models (Gold)

Build the clean master data:

```bash
python -m src.transform.silver.resolution
```

Build analytical tables:

```bash
python -m src.transform.gold.build_gold
```

Train ML models and run simulations:

```bash
python -m src.modeling.predictive.train_model
python -m src.modeling.network.graph_analysis
python -m src.modeling.anomaly.detect_anomalies
python -m src.modeling.revenue.monte_carlo
python -m src.modeling.predictive.survival_analysis
python -m src.modeling.predictive.quota_modeling
```

### 6. Launch Executive Dashboard

```bash
python -m streamlit run app/streamlit_app.py
```

---

## 📊 Key Features

- Synthetic financial and institutional relationship data generation.
- Large-scale data ingestion and processing.
- Entity resolution and duplicate detection.
- Relationship health and engagement scoring.
- Revenue concentration and retention analysis.
- Client inactivity prediction using XGBoost.
- Institutional relationship network visualization.
- Financial transaction anomaly detection.
- Customer survival and churn analysis.
- Monte Carlo revenue forecasting.
- Executive-level interactive dashboard.

---

## 📁 Project Highlights

NEXUS demonstrates the integration of:

- Data Engineering
- Database Management
- Master Data Management
- Quantitative Finance
- Machine Learning
- Predictive Analytics
- Statistical Modeling
- Graph Theory
- Financial Risk Analysis
- Business Intelligence

---