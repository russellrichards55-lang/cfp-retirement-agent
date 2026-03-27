import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Rusty’s Retirement Agent", layout="wide", page_icon="📈")
st.title("Rusty’s CFP Retirement Planning Agent")
st.markdown("**Conservative Monte Carlo Projections with Account-Type Separation** — Missouri tax implications noted")

# Sidebar inputs
with st.sidebar:
    st.header("Personal Details")
    age = st.number_input("Current Age", min_value=20, max_value=100, value=55)
    retirement_age = st.number_input("Planned Retirement Age", min_value=age + 1, max_value=100, value=67)
    
    st.header("Current Savings Allocation")
    current_savings = st.number_input("Total Current Savings ($)", min_value=0, value=500_000, step=10_000)
    
    taxable_pct = st.slider("Taxable Brokerage (%)", 0, 100, 40)
    trad_pct = st.slider("Traditional IRA/401(k) (%)", 0, 100, 40)
    roth_pct = st.slider("Roth IRA/401(k) (%)", 0, 100, 20)
    
    # Normalize to 100%
    total_pct = taxable_pct + trad_pct + roth_pct
    if total_pct != 100:
        st.warning(f"Allocation sums to {total_pct}%. It will be normalized.")
    
    taxable_current = current_savings * (taxable_pct / 100)
    trad_current = current_savings * (trad_pct / 100)
    roth_current = current_savings * (roth_pct / 100)
    
    st.header("Annual Contribution Allocation")
    annual_contribution = st.number_input("Total Annual Contribution ($)", min_value=0, value=20_000, step=1_000)
    
    contrib_taxable_pct = st.slider("Taxable Brokerage (%)", 0, 100, 30, key="contrib_taxable")
    contrib_trad_pct = st.slider("Traditional (%)", 0, 100, 50, key="contrib_trad")
    contrib_roth_pct = st.slider("Roth (%)", 0, 100, 20, key="contrib_roth")
    
    total_contrib_pct = contrib_taxable_pct + contrib_trad_pct + contrib_roth_pct
    if total_contrib_pct != 100:
        st.warning(f"Contribution allocation sums to {total_contrib_pct}%. It will be normalized.")
    
    contrib_taxable = annual_contribution * (contrib_taxable_pct / 100)
    contrib_trad = annual_contribution * (contrib_trad_pct / 100)
    contrib_roth = annual_contribution * (contrib_roth_pct / 100)
    
    st.subheader("Return Assumptions (Conservative)")
    mean_annual_return = st.slider("Expected Annual Real Return (%)", 0.0, 12.0, 5.5) / 100.0
    volatility = st.slider("Volatility (Std Dev %)", 5.0, 25.0, 15.0) / 100.0
    inflation_rate = st.slider("Inflation Rate (%)", 1.0, 5.0, 3.0) / 100.0
    
    num_simulations = st.slider("Number of Monte Carlo Simulations", 1000, 10000, 5000, step=1000)
    years_to_retirement = retirement_age - age

# Main simulation
if st.button("🚀 Run Monte Carlo Simulation with Account Types", type="primary"):
    with st.spinner(f"Running {num_simulations:,} simulations across account types..."):
        np.random.seed(42)
        
        final_taxable = []
        final_trad = []
        final_roth = []
        all_total_paths = []
        
        for _ in range(num_simulations):
            bal_taxable = taxable_current
            bal_trad = trad_current
            bal_roth = roth_current
            path_total = [bal_taxable + bal_trad + bal_roth]
            
            for _ in range(years_to_retirement):
                ret = np.random.normal(mean_annual_return, volatility)
                
                bal_taxable = bal_taxable * (1 + ret) + contrib_taxable
                bal_trad = bal_trad * (1 + ret) + contrib_trad
                bal_roth = bal_roth * (1 + ret) + contrib_roth
                
                path_total.append(bal_taxable + bal_trad + bal_roth)
            
            final_taxable.append(bal_taxable)
            final_trad.append(bal_trad)
            final_roth.append(bal_roth)
            all_total_paths.append(path_total)
        
        # Metrics
        final_taxable = np.array(final_taxable)
        final_trad = np.array(final_trad)
        final_roth = np.array(final_roth)
        final_total = final_taxable + final_trad + final_roth
        
        success_rate = (final_total > 0).mean() * 100
        median_total = np.median(final_total)
        p10_total = np.percentile(final_total, 10)
        p90_total = np.percentile(final_total, 90)
        
        # Charts
        years_list = list(range(age, retirement_age + 1))
        median_path = np.median(all_total_paths, axis=0)
        
        fig = go.Figure()
        p10_path = np.percentile(all_total_paths, 10, axis=0)
        p90_path = np.percentile(all_total_paths, 90, axis=0)
        
        fig.add_trace(go.Scatter(x=years_list, y=p90_path, mode='lines', line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=years_list, y=p10_path, mode='lines', line=dict(width=0),
                                 fillcolor='rgba(0,100,255,0.2)', fill='tonexty', name='10th–90th Percentile'))
        fig.add_trace(go.Scatter(x=years_list, y=median_path, mode='lines+markers',
                                 name='Median Total Portfolio', line=dict(color='blue', width=4)))
        
        fig.update_layout(
            title="Monte Carlo Portfolio Projections by Age (All Accounts)",
            xaxis_title="Age",
            yaxis_title="Portfolio Value ($)",
            template="plotly_white",
            hovermode="x unified"
        )
        
        # Display Results
        st.success("✅ Simulation complete!")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col2:
            st.metric("Median Final Balance", f"${median_total:,.0f}")
        with col3:
            st.metric("10th Percentile", f"${p10_total:,.0f}")
        with col4:
            st.metric("90th Percentile", f"${p90_total:,.0f}")
        
        st.subheader("Final Balance by Account Type (Median)")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Taxable Brokerage", f"${np.median(final_taxable):,.0f}")
        with col_b:
            st.metric("Traditional IRA/401(k)", f"${np.median(final_trad):,.0f}")
        with col_c:
            st.metric("Roth IRA/401(k)", f"${np.median(final_roth):,.0f}")
        
        st.subheader("Missouri Tax Notes (2026)")
        st.markdown("""
        - **Taxable Brokerage**: Missouri has eliminated state capital gains tax → growth and withdrawals are state-tax free (federal long-term capital gains may still apply).
        - **Traditional IRA/401(k)**: Withdrawals taxed as ordinary income at Missouri state rates (up to 4.7%).
        - **Roth IRA/401(k)**: Qualified withdrawals are completely tax-free at both federal and Missouri state level.
        """)
        
        st.subheader("Portfolio Projection (Fan Chart)")
        st.plotly_chart(fig, width="stretch")
        
        st.caption("**Important**: This is for educational purposes only. Missouri tax rules can change. Always consult a licensed CFP or tax professional for your specific situation in Missouri.")

else:
    st.info("👆 Adjust inputs and allocations in the sidebar, then click the button to run the simulation.")

st.caption("Missouri-focused retirement planning tool | GitHub: russellrichards55-lang/cfp-retirement-agent")
