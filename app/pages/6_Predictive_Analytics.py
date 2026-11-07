import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np  # <--- ADD THIS LINE
from components.db import get_db_engine, run_query

st.set_page_config(layout="wide")

st.title(" Predictive & Quantitative Analytics")
st.markdown("Machine learning models and Monte Carlo simulations for forward-looking risk intelligence.")

tab1, tab2, tab3 = st.tabs([" ML Risk Watchlist", " Monte Carlo Forecast", " Survival Analysis"])

with tab1:
    st.subheader("Machine Learning Predictions (XGBoost)")
    st.markdown("The model predicts the probability of a firm becoming completely inactive in the next 90 days. The 'Watchlist' shows high-revenue firms with extreme risk scores.")
    
    # 1. Fetch all predictions
    query_ml = """
    SELECT 
        f.canonical_name,
        f.sector,
        p.risk_probability,
        COALESCE(r.total_revenue_usd_m, 0) as total_revenue_usd_m
    FROM gold.fct_predictive_risk p
    JOIN gold.dim_firm f ON p.firm_master_id = f.firm_master_id
    LEFT JOIN gold.fct_revenue_intelligence r ON p.firm_master_id = r.firm_master_id
    """
    df_ml = run_query(query_ml)
    
    # Categorize Risk
    def get_risk_category(prob):
        if prob >= 0.70: return "1. High Risk (>70%)"
        if prob >= 0.40: return "2. Medium Risk (40-70%)"
        return "3. Low Risk (<40%)"
        
    df_ml['risk_category'] = df_ml['risk_probability'].apply(get_risk_category)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Chart 1: Count of firms by Risk Category
        risk_counts = df_ml['risk_category'].value_counts().reset_index()
        risk_counts.columns = ['Risk Category', 'Count']
        
        fig_pie = px.pie(
            risk_counts, 
            names='Risk Category', 
            values='Count',
            title="Institution Risk Distribution",
            color='Risk Category',
            color_discrete_map={
                "1. High Risk (>70%)": "#D0021B",
                "2. Medium Risk (40-70%)": "#F5A623",
                "3. Low Risk (<40%)": "#50E3C2"
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_chart2:
        # Chart 2: Revenue at Risk
        rev_at_risk = df_ml.groupby('risk_category')['total_revenue_usd_m'].sum().reset_index()
        
        fig_bar = px.bar(
            rev_at_risk,
            x='risk_category',
            y='total_revenue_usd_m',
            title="Total Revenue (USD M) Exposed to Churn Risk",
            color='risk_category',
            color_discrete_map={
                "1. High Risk (>70%)": "#D0021B",
                "2. Medium Risk (40-70%)": "#F5A623",
                "3. Low Risk (<40%)": "#50E3C2"
            },
            labels={'risk_category': 'Risk Category', 'total_revenue_usd_m': 'Revenue at Risk (USD M)'}
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    
    # 2. The Watchlist Table
    st.subheader("🚨 High-Value, High-Risk Watchlist")
    st.markdown("These are the specific firms generating >$10M in revenue with a >50% probability of churning.")
    
    df_watchlist = df_ml[(df_ml['risk_probability'] > 0.5) & (df_ml['total_revenue_usd_m'] > 10)]
    df_watchlist = df_watchlist.sort_values('risk_probability', ascending=False)
    
    st.dataframe(
        df_watchlist[['canonical_name', 'sector', 'risk_probability', 'total_revenue_usd_m']].style.format({
            "risk_probability": "{:.1%}",
            "total_revenue_usd_m": "${:,.1f}M"
        }).background_gradient(subset=["risk_probability"], cmap="Reds"), 
        use_container_width=True, 
        hide_index=True
    )

with tab2:
    st.subheader("Monte Carlo Revenue Simulation (10,000 Iterations)")
    st.markdown("Simulating 10,000 possible futures based on historical deal size distributions and win rates.")
    
    query_mc = "SELECT simulated_revenue_usd_m FROM gold.fct_monte_carlo_revenue"
    df_mc = run_query(query_mc)
    
    mean_rev = df_mc['simulated_revenue_usd_m'].mean()
    p5_rev = df_mc['simulated_revenue_usd_m'].quantile(0.05)
    p95_rev = df_mc['simulated_revenue_usd_m'].quantile(0.95)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Expected Revenue (Next 90d)", f"${mean_rev:.1f}M")
    col2.metric("Worst Case (5th %ile / VaR)", f"${p5_rev:.1f}M", delta=f"{p5_rev - mean_rev:.1f}M", delta_color="inverse")
    col3.metric("Best Case (95th %ile)", f"${p95_rev:.1f}M", delta=f"{p95_rev - mean_rev:.1f}M")
    
    fig_hist = px.histogram(
        df_mc, 
        x="simulated_revenue_usd_m", 
        nbins=100,
        title="Distribution of Simulated Future Revenue",
        labels={"simulated_revenue_usd_m": "Simulated Revenue (USD M)"},
        color_discrete_sequence=['#636EFA']
    )
    
    fig_hist.add_vline(x=mean_rev, line_dash="dash", line_color="white", annotation_text="Mean")
    fig_hist.add_vline(x=p5_rev, line_dash="dash", line_color="red", annotation_text="5% VaR")
    
    st.plotly_chart(fig_hist, use_container_width=True)

with tab3:
    st.subheader("Institutional Survival Analysis")
    st.markdown("""
    Survival analysis models the *time until an event* (in this case, churn). It handles censored data (clients who are still active) better than standard classification models.
    
    We use two complementary statistical methods:
    1. **Kaplan-Meier Estimator:** A non-parametric statistic used to estimate the survival function from lifetime data. It shows the probability of a relationship remaining active over time.
    2. **Cox Proportional Hazards:** A regression model used to measure the impact of specific covariates (like historical revenue) on the hazard (risk) of churn.
    """)
    
    # Fetch Stats
    query_stats = "SELECT * FROM gold.fct_survival_stats"
    df_stats = run_query(query_stats)
    
    if not df_stats.empty:
        hr = df_stats['hazard_ratio'].iloc[0]
        hr_ci_lower = df_stats['hr_ci_lower'].iloc[0]
        hr_ci_upper = df_stats['hr_ci_upper'].iloc[0]
        p_val = df_stats['logrank_p_value'].iloc[0]
        
        high_row = df_stats[df_stats['cohort'] == 'High Revenue'].iloc[0]
        low_row = df_stats[df_stats['cohort'] == 'Low Revenue'].iloc[0]
        
        # Median survival could be inf if >50% of the cohort hasn't churned yet
        high_median = high_row['median_survival_days']
        low_median = low_row['median_survival_days']
        
        high_median_str = f"{high_median / 30.44:.1f} months" if pd.notna(high_median) and high_median != np.inf else "Not Reached (>24 mo)"
        low_median_str = f"{low_median / 30.44:.1f} months" if pd.notna(low_median) and low_median != np.inf else "Not Reached (>24 mo)"
        
        # 3 KPI Columns
        col1, col2, col3 = st.columns(3)
        
        col1.metric(
            label="Median Relationship Survival (High Rev)", 
            value=high_median_str, 
            help=f"Based on {high_row['size']:,} High Revenue institutions."
        )
        col2.metric(
            label="Median Relationship Survival (Low Rev)", 
            value=low_median_str, 
            help=f"Based on {low_row['size']:,} Low Revenue institutions."
        )
        col3.metric(
            label="Hazard Ratio (High vs Low Revenue)", 
            value=f"{hr:.2f}",
            help=f"95% CI: [{hr_ci_lower:.2f}, {hr_ci_upper:.2f}]. Log-rank p-value: {p_val:.4f}"
        )
        
        st.markdown(f"""
        **Statistical Interpretation:**
        * The **Hazard Ratio** for historical revenue is **{hr:.2f}** (95% CI: {hr_ci_lower:.2f} - {hr_ci_upper:.2f}). Because this is > 1.0 and the p-value is {p_val:.4f}, it means higher revenue is associated with a *higher* instantaneous hazard of churn in this synthetic dataset (likely due to deal cycles concluding).
        * The Kaplan-Meier curves show the survival probability over time. Median survival is the time at which the curve crosses the 50% threshold.
        """)
        
        # Chart
        query_km = "SELECT timeline_days, survival_probability, cohort FROM gold.fct_survival_curve ORDER BY timeline_days"
        df_km = run_query(query_km)
        df_km['timeline_months'] = df_km['timeline_days'] / 30.44
        
        fig_km = px.line(
            df_km, 
            x="timeline_months", 
            y="survival_probability",
            color="cohort",
            title="Kaplan-Meier Survival Curve: High vs Low Revenue Clients",
            labels={"timeline_months": "Relationship Age (Months)", "survival_probability": "Probability of Survival", "cohort": "Revenue Cohort"},
            color_discrete_map={"High Revenue": "#50E3C2", "Low Revenue": "#D0021B"}
        )
        
        fig_km.add_hline(y=0.5, line_dash="dash", line_color="gray", annotation_text="50% Survival Threshold")
        fig_km.update_traces(line_width=3)
        fig_km.update_layout(
            yaxis=dict(range=[0, 1.05]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        
        st.plotly_chart(fig_km, use_container_width=True)
    else:
        st.warning("Survival stats not found. Please run the survival analysis script.")