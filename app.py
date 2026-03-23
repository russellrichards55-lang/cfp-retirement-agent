# app.py - CFP-Level Retirement Agent v1.0 (Cloud-Native via Streamlit)
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Rusty’s CFP Retirement Agent", layout="wide")

st.title("Rusty’s Personal CFP-Level Retirement Planner")
st.markdown("**Version 1.0** – Deterministic + Monte Carlo simulation. All in-browser, no local install.")

# ── SIDEBAR INPUTS ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Your Inputs")
    
    current_age = st.number_input("Current Age", min_value=30, max_value=80, value=55, step=1)
    retirement_age = st.number_input("Planned Retirement Age", min_value=50, max_value=75, value=65, step=1)
    life_expectancy = st.number_input("Planning Horizon (Age at End)", min_value=85, max_value=110, value=95, step=1)
    
    current_portfolio = st.number_input("Current Total Portfolio ($)", min_value=0, value=500000, step=10000, format="%d")
    annual_contribution = st.number_input("Annual Savings/Contribution (pre-retirement)", min_value=0, value=20000, step=1000)
    annual_spending_retirement = st.number_input("Desired Annual Spending in Retirement (today's $)", min_value=40000, value=80000, step=1000)
    
    expected_return = st.slider("Expected Annual Return (nominal %)", 4.0, 10.0, 7.0, step=0.1) / 100
    volatility = st.slider("Annual Volatility (std dev %)", 8.0, 20.0, 15.0, step=0.5) / 100
    inflation = st.slider("Expected Inflation (%)", 2.0, 5.0, 3.0, step=0.1) / 100
    
    num_simulations = st.slider("Monte Carlo Runs", 1000, 20000, 5000, step=1000)
    success_threshold = st.slider("Success Threshold (Portfolio > $0 at end)", 0.70, 0.95, 0.85, step=0.05)

# ── CALCULATIONS ────────────────────────────────────────────────────────────────
years_to_retire = retirement_age - current_age
years_in_retire = life_expectancy - retirement_age
total_years = years_to_retire + years_in_retire

real_return = (1 + expected_return) / (1 + inflation) - 1

# Deterministic projection
balance_det = [current_portfolio]
for y in range(1, total_years + 1):
    if y <= years_to_retire:
        new_bal = balance_det[-1] * (1 + expected_return) + annual_contribution
    else:
        new_bal = balance_det[-1] * (1 + expected_return) - annual_spending_retirement * (1 + inflation)**(y - years_to_retire - 1)
    balance_det.append(max(new_bal, 0))

df_det = pd.DataFrame({"Year": range(0, total_years + 1), "Balance": balance_det})
df_det["Age"] = current_age + df_det["Year"]

# Monte Carlo
np.random.seed(42)  # reproducible
returns = np.random.normal(expected_return, volatility, (num_simulations, total_years))
balances_mc = np.zeros((num_simulations, total_years + 1))
balances_mc[:, 0] = current_portfolio

for y in range(1, total_years + 1):
    if y <= years_to_retire:
        balances_mc[:, y] = balances_mc[:, y-1] * (1 + returns[:, y-1]) + annual_contribution
    else:
        withdrawal = annual_spending_retirement * (1 + inflation)**(y - years_to_retire - 1)
        balances_mc[:, y] = balances_mc[:, y-1] * (1 + returns[:, y-1]) - withdrawal
    balances_mc[:, y] = np.maximum(balances_mc[:, y], 0)

success_rate = np.mean(balances_mc[:, -1] > 0)
percentiles = np.percentile(balances_mc[:, -1], [5, 25, 50, 75, 95])

# ── MAIN LAYOUT ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Portfolio Projection")
    
    fig = go.Figure()
    
    # Deterministic line
    fig.add_trace(go.Scatter(x=df_det["Age"], y=df_det["Balance"]/1000,
                             mode='lines', name='Deterministic', line=dict(color='blue', width=3)))
    
    # Monte Carlo fan (percentiles)
    ages = np.arange(current_age, current_age + total_years + 1)
    p5  = np.percentile(balances_mc, 5,  axis=0)/1000
    p25 = np.percentile(balances_mc, 25, axis=0)/1000
    p50 = np.percentile(balances_mc, 50, axis=0)/1000
    p75 = np.percentile(balances_mc, 75, axis=0)/1000
    p95 = np.percentile(balances_mc, 95, axis=0)/1000
    
    fig.add_trace(go.Scatter(x=ages, y=p95, line=dict(color='rgba(0,100,255,0.2)'), name='95th'))
    fig.add_trace(go.Scatter(x=ages, y=p5,  line=dict(color='rgba(0,100,255,0.2)'), fill='tonexty', fillcolor='rgba(0,100,255,0.1)', name='5-95%'))
    fig.add_trace(go.Scatter(x=ages, y=p75, line=dict(color='rgba(0,100,255,0.4)')))
    fig.add_trace(go.Scatter(x=ages, y=p25, line=dict(color='rgba(0,100,255,0.4)'), fill='tonexty', fillcolor='rgba(0,100,255,0.2)', name='25-75%'))
    fig.add_trace(go.Scatter(x=ages, y=p50, line=dict(color='orange', dash='dash'), name='Median MC'))
    
    fig.update_layout(title="Projected Portfolio Balance ($000s)",
                      xaxis_title="Your Age", yaxis_title="Balance ($ thousands)",
                      hovermode="x unified", legend=dict(orientation="h"))
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Key Metrics")
    st.metric("Success Probability", f"{success_rate:.1%}", help="Percent of simulations where portfolio > $0 at age " + str(life_expectancy))
    st.metric("Success Target", f"{success_threshold:.0%}", delta=f"{success_rate - success_threshold:.1%}")
    
    st.markdown("**Ending Balance Percentiles (age " + str(life_expectancy) + ")**")
    st.write(f"5th:  ${percentiles[0]:,.0f}")
    st.write(f"25th: ${percentiles[1]:,.0f}")
    st.write(f"Median: ${percentiles[2]:,.0f}")
    st.write(f"75th: ${percentiles[3]:,.0f}")
    st.write(f"95th: ${percentiles[4]:,.0f}")

# Quick Chat Placeholder (we'll make this Grok-powered next)
st.subheader("Ask your CFP Agent (coming soon)")
user_question = st.text_input("e.g., 'What if I retire at 62 instead?'")
if user_question:
    st.info("Grok integration in progress – reply here with questions and we'll add real agent reasoning!")

st.markdown("---")
st.caption("Built cloud-native with Streamlit + NumPy + Plotly. Deploy next → Streamlit Community Cloud.")
