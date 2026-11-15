# NEXUS: Institutional Relationship & Quantitative Intelligence Platform

**NEXUS** is an executive-level financial intelligence platform designed to simulate, analyze, and forecast the complex relationship networks of a Private Equity or institutional investment firm.

By transforming fragmented, intentionally dirty CRM, deal, and financial data into a unified analytical ecosystem, NEXUS provides actionable insights into relationship health, revenue concentration risk, machine learning predictions, and Monte Carlo forecasts.

> **Note on Data:** This project uses a custom-built, highly relational synthetic data generator (`Faker`, `NumPy`). It simulates 1.5+ million records and deliberately injects data quality defects (duplicates, missing IDs) to demonstrate a robust Entity Resolution pipeline. **No real client data is used.**

**🚀 Portfolio Link:** [https://thisisnexus.streamlit.app/](https://thisisnexus.streamlit.app/)

---

## 🏗️ Architecture & Data Pipeline (Medallion Architecture)

The platform is built on a modern data stack using **PostgreSQL (Supabase)** and **Python**, following the Bronze/Silver/Gold data modeling pattern:

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

- **ARIMA Time-Series Forecasting:** Uses auto-regressive time-series modeling to forecast future deal volume and revenue based on historical trends and lags.

---

## 🖥️ The Three Interfaces: Streamlit, Power BI & Excel

NEXUS delivers its analytical capabilities through three different platforms, each designed for a specific business purpose.

### 1. Streamlit — Interactive Analytical Application

**Purpose:** Deep analytical exploration and interactive model outputs.

**Live Application:** [NEXUS Streamlit App](https://thisisnexus.streamlit.app/)

**What was built:**

- A 7-page interactive web application.
- **Executive Overview:** Four KPI cards, dual-axis network forecasting, and a custom Plotly Sankey diagram illustrating deal flow.
- **Network Analysis:** Interactive `pyvis` network graph allowing users to explore institutional relationships and influential firms.
- **Relationship Intelligence:** Dynamic histograms, relationship scoring, and at-risk account filtering.
- **Predictive Analytics:** A three-tab interface featuring:
  - XGBoost client inactivity risk watchlist.
  - 10,000-iteration Monte Carlo revenue VaR simulations.
  - Kaplan-Meier survival curves with statistical p-values.
- **Data Quality:** Visual representation of the Entity Resolution pipeline, demonstrating how duplicate and inconsistent records are identified and resolved.

### 2. Power BI — Executive Intelligence Dashboard

**Purpose:** High-level strategic reporting and business intelligence for executive decision-making.

**What was built:**

- A 5-page interactive dashboard connected directly to the Supabase cloud database.
- **Executive Intelligence:** KPI cards, Top 10 Exposures, and Quadrant Analysis scatter plots identifying high-value and high-bridge firms.
- **Network & Capacity:** Relationship network distribution and Relationship Manager (RM) quota attainment analysis.
- **Relationship Intelligence:** Risk distribution donut charts and high-value/low-engagement scatter plots.
- **Revenue Intelligence:** Dynamic treemaps, HHI revenue concentration analysis, and ARPR metrics.
- **Deal & Pipeline:** Pipeline funnel charts and win-rate analysis across different deal types.
- **Dashboard Design:** Custom dark-theme JSON configuration inspired by the Bloomberg Terminal aesthetic.

### 3. Excel — Institutional Financial Modelling Workbook

**Purpose:** Financial modelling, scenario analysis, sensitivity testing, and quantitative forecasting.

**Workbook:** `NEXUS_Financial_Model.xlsx`

**What was built:**

- An 8-sheet institutional-grade financial modelling workbook.
- **Overview:** Central navigation hub with embedded summary charts and key financial indicators.
- **Revenue Dashboard:** Dynamic dropdown functionality allowing users to switch between Base, Upside, and Downside revenue scenarios.
- **Deal Economics:** Separates Gross Transaction Value from Net Advisory Fees, calculates Weighted Pipeline, and connects assumptions through a `Control_Backend` sheet.
- **Portfolio Concentration:** Complete HHI calculation, Top 1/5/10 exposure analysis, and cumulative revenue concentration percentages.
- **Scenario Analysis:** What-If Data Tables, sensitivity analysis, and dynamic line charts.
- **Monte Carlo Simulation:** 10,000-row `NORM.INV(RAND())` simulation calculating expected revenue, 5th percentile (VaR), and 95th percentile outcomes.
- **ARIMA Forecast:** Manual construction of an autoregressive forecasting model using Excel's Data Analysis Toolpak.
- **Forecast vs Actual:** Combination charts featuring ±10% statistical safe zones and a Waterfall Gap Analysis bridge.

---

## 💻 Tech Stack

| Category | Technologies |
|---|---|
| Data Generation | `Faker`, `NumPy` |
| Data Processing & Entity Resolution | `pandas`, `RapidFuzz` |
| Database | `PostgreSQL`, `Supabase`, `SQLAlchemy` |
| Machine Learning | `scikit-learn`, `XGBoost` |
| Statistical Analysis | `SciPy`, `statsmodels`, `lifelines` |
| Network Analysis | `NetworkX` |
| Web Application | `Streamlit` |
| Data Visualization | `Plotly`, `pyvis` |
| Business Intelligence | `Power BI`, `Microsoft Excel` |
| Financial Modelling | Excel Formulas, Data Tables, Monte Carlo Simulation |

---

## 🚀 How to Run Locally

### 1. Prerequisites

- Python 3.10+
- PostgreSQL (running locally on port 5432 or through Supabase)

### 2. Setup Database

Create a database and user in PostgreSQL:

```sql
CREATE DATABASE nexus;
CREATE USER nexus_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE nexus TO nexus_user;

Setup Environment

git clone https://github.com/STELLARSCRIPTER/nexus
cd nexus
Clone the repository and install dependencies:
python -m venv .venv

Activate the virtual environment:
Windows: .venv\Scripts\activate     
Mac/Linux: source .venv/bin/activate

Install dependencies:
pip install -r requirements.txt

Create a .env file in the root directory:

NEXUS_DB_HOST=localhost
NEXUS_DB_PORT=5432
NEXUS_DB_NAME=nexus
NEXUS_DB_USER=nexus_user
NEXUS_DB_PASSWORD=your_password

Run Entity Resolution (Silver) & Quant Models (Gold)
Build the clean master data:
python -m src.transform.silver.resolution

Build analytical tables:

python -m src.transform.gold.build_gold

Train ML models and run simulations:

python -m src.modeling.predictive.train_model
python -m src.modeling.network.graph_analysis
python -m src.modeling.anomaly.detect_anomalies
python -m src.modeling.revenue.monte_carlo
python -m src.modeling.predictive.survival_analysis
python -m src.modeling.predictive.quota_modeling

Start the Streamlit application:
python -m streamlit run app/streamlit_app.py

Key Features
- Synthetic financial and institutional relationship data generation.
- Large-scale data ingestion and processing.
- Bronze, Silver, and Gold Medallion Architecture.
- Entity resolution and duplicate detection using fuzzy matching.
- Relationship health and engagement scoring.
- Revenue concentration and retention analysis.
- Client inactivity prediction using XGBoost.
- Institutional relationship network visualization.
- Network centrality and influential firm identification.
- Financial transaction anomaly detection using Isolation Forest.
- Customer survival and churn analysis.
- Monte Carlo revenue forecasting and Value at Risk estimation.
- ARIMA-based time-series forecasting.
- Interactive executive dashboard using Streamlit.
- Strategic business intelligence reporting using Power BI.
- Institutional financial modelling using Microsoft Excel.
- Scenario analysis and financial sensitivity modelling.


Project Highlights
NEXUS demonstrates the integration of:
- Data Engineering (Medallion Architecture)
- Database Management (PostgreSQL, Supabase)
- Master Data Management (Entity Resolution)
- Quantitative Finance (Monte Carlo, ARIMA, VaR)
- Machine Learning (XGBoost, Isolation Forest)
- Predictive Analytics (Survival Analysis)
- Statistical Modeling (Kaplan-Meier, Cox Proportional Hazards)
- Graph Theory (Network Centrality)
- Financial Risk Analysis (HHI, Revenue Concentration)
- Revenue Operations Intelligence (ARPR, NRR, Cohort Analysis)
- Business Intelligence (Power BI, Streamlit)
- Financial Modelling (Microsoft Excel)
