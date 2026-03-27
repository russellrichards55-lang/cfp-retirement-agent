import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

# Page config
st.set_page_config(page_title="Rusty’s Retirement Agent", layout="wide", page_icon="📈")
st.title("Rusty’s CFP Retirement Planning Agent")
st.markdown("**Conservative Monte Carlo + Deterministic Projections** — Topeka, KS focus")

# Sidebar inputs
with st.sidebar:
    st.header("Your Inputs")
    age = st.number_input("Current Age", min_value=20, max_value=100, value=55)
    retirement_age = st.number_input("Planned Retirement Age", min_value=age + 1, max_value=100, value=67)
    current_savings = st.number_input("Current Savings ($)", min_value=0, value=500_000, step=10_000)
    annual_contribution = st.number_input("Annual Contribution ($)", min_value=0, value=20_000, step=1_000)
    
    st.subheader("Return Assumptions (Conservative)")
    mean_annual_return = st.slider("Expected Annual Return (%)", 0.0, 12.0, 5.5) / 100.0
    volatility = st.slider("Volatility (Std Dev %)", 5.0, 25.0, 15.0) / 100.0
    inflation_rate = st.slider("Inflation Rate (%)", 1.0, 5.0, 3.0) / 100.0
    
    num_simulations = st.slider("Number of Monte Carlo Simulations", 1000, 10000, 5000, step=1000)
    years_to_retirement = retirement_age - age

# Main content
if st.button("🚀 Run Monte Carlo Simulation & Projections", type="primary"):
    with st.spinner(f"Running {num_simulations:,} simulations... This may take 10–40 seconds"):
        
        # Monte Carlo Simulation
        np.random.seed(42)  # For reproducibility
        final_balances = []
        all_paths = []  # For fan chart
        
        for _ in range(num_simulations):
            balance = current_savings
            path = [balance]
            
            for year in range(years_to_retirement):
                annual_return = np.random.normal(mean_annual_return, volatility)
                balance = balance * (1 + annual_return) + annual_contribution
                path.append(balance)
            
            final_balances.append(balance)
            all_paths.append(path)
        
        # Calculate metrics
        final_balances = np.array(final_balances)
        success_rate = (final_balances > 0).mean() * 100
        median_balance = np.median(final_balances)
        p10 = np.percentile(final_balances, 10)
        p90 = np.percentile(final_balances, 90)
        
        # Create median path for chart
        years_list = list(range(age, retirement_age + 1))
        median_path = np.median(all_paths, axis=0)
        
        # Plotly Figure - Median path + fan chart
        fig = go.Figure()
        
        # Fan chart (10th to 90th percentile bands)
        p10_path = np.percentile(all_paths, 10, axis=0)
        p90_path = np.percentile(all_paths, 90, axis=0)
        fig.add_trace(go.Scatter(x=years_list, y=p90_path, mode='lines', line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=years_list, y=p10_path, mode='lines', line=dict(width=0),
                                 fillcolor='rgba(0,100,255,0.2)', fill='tonexty', name='10th–90th Percentile'))
        
        # Median path
        fig.add_trace(go.Scatter(x=years_list, y=median_path, mode='lines+markers',
                                 name='Median Path', line=dict(color='blue', width=4)))
        
        fig.update_layout(
            title="Monte Carlo Retirement Portfolio Projections",
            xaxis_title="Age",
            yaxis_title="Portfolio Value ($)",
            template="plotly_white",
            hovermode="x unified"
        )
        
        # Histogram of final balances
        fig_hist = go.Figure(data=[go.Histogram(x=final_balances, nbinsx=50)])
        fig_hist.update_layout(
            title="Distribution of Final Portfolio Balances",
            xaxis_title="Final Balance ($)",
            yaxis_title="Number of Simulations",
            template="plotly_white"
        )
        
        # Display results
        st.success("✅ Simulation complete!")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Success Rate", f"{success_rate:.1f}%", help="Percentage of simulations where portfolio > $0 at end")
        with col2:
            st.metric("Median Final Balance", f"${median_balance:,.0f}")
        with col3:
            st.metric("10th Percentile (Bad Case)", f"${p10:,.0f}")
        with col4:
            st.metric("90th Percentile (Good Case)", f"${p90:,.0f}")
        
        st.subheader("Portfolio Projection (Fan Chart)")
        st.plotly_chart(fig, width="stretch")
        
        st.subheader("Distribution of Outcomes")
        st.plotly_chart(fig_hist, width="stretch")
        
        st.info("**Note**: This uses conservative assumptions. Sequence-of-returns risk is captured in the Monte Carlo. Results are illustrative only.")

else:
    st.info("👆 Adjust your inputs in the sidebar, then click the button above to run the Monte Carlo simulation.")

st.caption("Built as a fiduciary-style retirement planning tool | GitHub: russellrichards55-lang/cfp-retirement-agent")
