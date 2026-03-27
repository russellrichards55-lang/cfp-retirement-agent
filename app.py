import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Rusty’s Retirement Agent", layout="wide", page_icon="📈")
st.title("Rusty’s CFP Retirement Planning Agent")
st.markdown("**Conservative Monte Carlo Projections with Separate Account Types** — Missouri tax implications noted")

# Sidebar inputs
with st.sidebar:
    st.header("Personal Details")
    age = st.number_input("Current Age", min_value=20, max_value=100, value=55)
    retirement_age = st.number_input("Planned Retirement Age", min_value=age + 1, max_value=100, value=67)
    
    st.header("Current Savings by Account Type")
    taxable_current = st.number_input("Taxable Brokerage ($)", min_value=0, value=200_000, step=10_000)
    trad_current = st.number_input("Traditional IRA/401(k) ($)", min_value=0, value=200_000, step=10_000)
    roth_current = st.number_input("Roth IRA/401(k) ($)", min_value=0, value=100_000, step=10_000)
    
    total_current_savings = taxable_current + trad_current + roth_current
    st.info(f"**Total Current Savings: ${total_current_savings:,.0f}**")
    
    st.header("Annual Contributions by Account Type")
    contrib_taxable = st.number_input("Annual to Taxable Brokerage ($)", min_value=0, value=6_000, step=1_000)
    contrib_trad = st.number_input("Annual to Traditional IRA/401(k) ($)", min_value=0, value=10_000, step=1_000)
    contrib_roth = st.number_input("Annual to Roth IRA/401(k) ($)", min_value=0, value=4_000, step=1_000)
    
    total_annual_contribution = contrib_taxable + contrib_trad + contrib_roth
    st.info(f"**Total Annual Contribution: ${total_annual_contribution:,.0f}**")
    
    st.subheader("Return Assumptions (Conservative)")
    mean_annual_return = st.slider("Expected Annual Real Return (%)", 0.0, 12.0, 5.5) / 100.0
    volatility = st.slider("Volatility (Std Dev %)", 5.0, 25.0, 15.0) / 100.0
    inflation_rate = st.slider("Inflation Rate (%)", 1.0, 5.0, 3.0) / 100.0
    
    num_simulations = st.slider("Number of Monte Carlo Simulations", 1000, 10000, 5000, step=1000)
    years_to_retirement = retirement_age - age

# Main simulation - only runs when button is clicked
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
            st.metric("10th Percentile (Bad Case)", f"${p10_total:,.0f}")
        with col4:
            st.metric("90th Percentile (Good Case)", f"${p90_total:,.0f}")
        
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
        - **Taxable Brokerage**: Missouri has eliminated state capital gains tax for individuals → growth and qualified withdrawals are state-tax free (federal long-term capital gains may still apply).
        - **Traditional IRA/401(k)**: Withdrawals taxed as ordinary income at Missouri state rates (up to 4.7%).
        - **Roth IRA/401(k)**: Qualified withdrawals are completely tax-free at both federal and Missouri state level.
        """)
        
        st.subheader("Portfolio Projection (Fan Chart)")
        st.plotly_chart(fig, width="stretch")
        
        st.caption("**Important**: This is for educational/illustrative purposes only. Missouri tax rules can change. Consult a licensed CFP or tax professional for your specific situation.")

else:
    st.info("👆 Enter your savings and contribution amounts by account type in the sidebar, then click the button above to run the simulation.")

st.caption("Missouri-focused retirement planning tool | GitHub: russellrichards55-lang/cfp-retirement-agent")
