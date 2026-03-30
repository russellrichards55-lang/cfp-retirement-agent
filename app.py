import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Rusty’s CFP Retirement Agent", layout="wide", page_icon="📈")
st.title("Rusty’s CFP Retirement Planning Agent")
st.markdown("**Missouri-Focused Analysis & Actionable Recommendations** — Conservative Monte Carlo with Withdrawal Phase")

# Sidebar inputs
with st.sidebar:
    st.header("Personal Details")
    current_age = st.number_input("Current Age", min_value=20, max_value=100, value=55)
    desired_retirement_age = st.number_input("Desired Retirement Age (Target)", min_value=current_age + 1, max_value=100, value=60)
    life_expectancy = st.number_input("Life Expectancy (for planning)", min_value=desired_retirement_age + 1, max_value=120, value=95)
    
    st.header("Current Savings by Account Type")
    taxable_current = st.number_input("Taxable Brokerage ($)", min_value=0, value=200_000, step=10_000)
    trad_current = st.number_input("Traditional IRA/401(k) ($)", min_value=0, value=200_000, step=10_000)
    roth_current = st.number_input("Roth IRA/401(k) ($)", min_value=0, value=100_000, step=10_000)
    
    st.header("Annual Contributions by Account Type")
    contrib_taxable = st.number_input("Annual to Taxable Brokerage ($)", min_value=0, value=6_000, step=1_000)
    contrib_trad = st.number_input("Annual to Traditional IRA/401(k) ($)", min_value=0, value=10_000, step=1_000)
    contrib_roth = st.number_input("Annual to Roth IRA/401(k) ($)", min_value=0, value=4_000, step=1_000)
    
    st.subheader("Return & Inflation Assumptions (Conservative)")
    mean_return = st.slider("Expected Annual Real Return (%)", 0.0, 12.0, 5.5) / 100.0
    volatility = st.slider("Volatility (Std Dev %)", 5.0, 25.0, 15.0) / 100.0
    inflation_rate = st.slider("Inflation Rate (%)", 1.0, 5.0, 3.0) / 100.0
    
    st.subheader("Retirement Spending Goal")
    annual_spending_goal = st.number_input("Desired Annual Spending in Today's Dollars ($)", min_value=20_000, value=60_000, step=5_000)
    
    num_simulations = st.slider("Number of Monte Carlo Simulations", 1000, 10000, 3000, step=500)  # lowered default for speed

# Main simulation button
if st.button("🚀 Run Full CFP Analysis & Recommendations", type="primary"):
    with st.spinner(f"Running {num_simulations:,} lifetime simulations (accumulation + withdrawal)..."):
        np.random.seed(42)
        
        years_to_retire = desired_retirement_age - current_age
        years_in_retirement = life_expectancy - desired_retirement_age
        total_years = years_to_retire + years_in_retirement
        
        # Run simulations
        success_count = 0
        final_balances = []
        
        for _ in range(num_simulations):
            bal_taxable = taxable_current
            bal_trad = trad_current
            bal_roth = roth_current
            balance = bal_taxable + bal_trad + bal_roth
            
            # Accumulation phase
            for _ in range(years_to_retire):
                ret = np.random.normal(mean_return, volatility)
                bal_taxable = bal_taxable * (1 + ret) + contrib_taxable
                bal_trad = bal_trad * (1 + ret) + contrib_trad
                bal_roth = bal_roth * (1 + ret) + contrib_roth
                balance = bal_taxable + bal_trad + bal_roth
            
            # Withdrawal phase (inflation-adjusted spending)
            current_spending = annual_spending_goal
            success = True
            for y in range(years_in_retirement):
                current_spending *= (1 + inflation_rate)
                ret = np.random.normal(mean_return, volatility)
                
                # Withdraw proportionally, apply Missouri tax drag on Traditional
                trad_withdrawal = current_spending * (bal_trad / balance) if balance > 0 else 0
                taxable_withdrawal = current_spending * (bal_taxable / balance) if balance > 0 else 0
                roth_withdrawal = current_spending * (bal_roth / balance) if balance > 0 else 0
                
                # Missouri ordinary income tax on Traditional (~4.7% top rate conservative estimate)
                trad_after_tax = trad_withdrawal * (1 - 0.047)
                
                bal_taxable -= taxable_withdrawal
                bal_trad -= trad_withdrawal
                bal_roth -= roth_withdrawal
                
                # Grow remaining balance
                bal_taxable = bal_taxable * (1 + ret)
                bal_trad = bal_trad * (1 + ret)
                bal_roth = bal_roth * (1 + ret)
                
                balance = bal_taxable + bal_trad + bal_roth
                
                if balance < 0:
                    success = False
                    break
            
            if success:
                success_count += 1
            final_balances.append(balance)
        
        success_rate = (success_count / num_simulations) * 100
        median_final = np.median(final_balances)
        
        # Simple "what's needed" adjustment logic
        required_contrib_increase = 0
        if success_rate < 70:
            required_contrib_increase = int((70 - success_rate) / 10 * 5000)  # rough heuristic
        
        # Display Results
        st.success("✅ Full Lifetime Simulation Complete")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Success Rate (Lasts to Life Expectancy)", f"{success_rate:.1f}%")
        with col2:
            st.metric("Median Final Balance", f"${median_final:,.0f}")
        with col3:
            st.metric("Desired Retirement Age", f"{desired_retirement_age}")
        
        # CFP Analysis & Recommendations
        st.subheader("📋 CFP Analysis & Recommendations")
        st.markdown(f"**Target:** Retire at **{desired_retirement_age}** with **${annual_spending_goal:,.0f}** annual spending (today’s dollars).")
        
        if success_rate >= 80:
            st.success("✅ Your current plan has a **strong** chance of success.")
            st.markdown("- No major changes needed. Continue current contribution levels.")
        elif success_rate >= 60:
            st.warning("⚠️ Moderate success probability. Small adjustments recommended.")
        else:
            st.error("❌ Success rate is low for your target. Action needed now.")
        
        st.markdown("**Recommended Actions Right Now:**")
        if required_contrib_increase > 0:
            st.markdown(f"- **Increase total annual contributions by ~${required_contrib_increase:,.0f}** (prioritize Roth if eligible).")
        if trad_current > 0 and current_age < 59.5:
            st.markdown("- Consider a **Roth conversion ladder** now while in a lower tax bracket (reduces future Missouri ordinary income tax drag).")
        if contrib_roth < contrib_trad:
            st.markdown("- Shift more new contributions to **Roth** — tax-free growth and withdrawals are powerful in Missouri.")
        st.markdown("- Maximize employer 401(k) match if available (free money).")
        st.markdown("- Review taxable brokerage for tax-loss harvesting opportunities.")
        st.markdown("- Re-run with different spending goals or delayed retirement if needed.")
        
        st.subheader("Missouri Tax Notes (2026)")
        st.markdown("""
        - **Taxable Brokerage**: 100% capital gains exemption at state level (huge advantage).
        - **Traditional IRA/401(k)**: Withdrawals taxed as ordinary income (up to 4.7% Missouri rate).
        - **Roth IRA/401(k)**: Completely tax-free qualified withdrawals (best for long-term efficiency).
        """)
        
        st.caption("**Disclaimer**: This is educational modeling only. Tax laws change. Always consult a licensed CFP and tax professional for your personal situation in Missouri.")

else:
    st.info("👆 Enter your numbers in the sidebar and click the button above for a full CFP-style analysis.")

st.caption("Missouri-focused fiduciary-style retirement planner | GitHub: russellrichards55-lang/cfp-retirement-agent")
