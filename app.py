import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Rusty’s CFP Retirement Agent", layout="wide", page_icon="📈")
st.title("Rusty’s CFP Retirement Planning Agent")
st.markdown("**Missouri-Focused Analysis & Recommendations** — Withdrawal + Social Security Strategies Added")

# Sidebar inputs
with st.sidebar:
    st.header("Personal Details")
    current_age = st.number_input("Current Age", min_value=20, max_value=100, value=55)
    desired_retirement_age = st.number_input("Desired Retirement Age (Target)", min_value=current_age + 1, max_value=100, value=60)
    life_expectancy = st.number_input("Life Expectancy (for planning)", min_value=desired_retirement_age + 1, max_value=120, value=95)
    
    st.header("Retirement Accounts")
    taxable_current = st.number_input("Taxable Brokerage ($)", min_value=0, value=200_000, step=10_000)
    trad_current = st.number_input("Traditional IRA/401(k) ($)", min_value=0, value=200_000, step=10_000)
    roth_current = st.number_input("Roth IRA/401(k) ($)", min_value=0, value=100_000, step=10_000)
    
    st.header("Annual Contributions (Retirement Accounts)")
    contrib_taxable = st.number_input("Annual to Taxable Brokerage ($)", min_value=0, value=6_000, step=1_000)
    contrib_trad = st.number_input("Annual to Traditional IRA/401(k) ($)", min_value=0, value=10_000, step=1_000)
    contrib_roth = st.number_input("Annual to Roth IRA/401(k) ($)", min_value=0, value=4_000, step=1_000)
    
    st.header("Other Assets")
    st.subheader("Real Estate")
    re_value = st.number_input("Current Real Estate Value ($)", min_value=0, value=300_000, step=10_000)
    re_appreciation = st.slider("Expected Annual Appreciation (%)", 0.0, 8.0, 3.5) / 100.0
    re_rental_income = st.number_input("Net Annual Rental Income ($)", min_value=0, value=12_000, step=1_000)
    
    st.subheader("Precious Metals")
    pm_value = st.number_input("Current Precious Metals Value ($)", min_value=0, value=50_000, step=5_000)
    pm_return = st.slider("Expected Annual Return (%)", 0.0, 10.0, 4.0) / 100.0
    pm_vol = st.slider("Precious Metals Volatility (%)", 5.0, 30.0, 18.0) / 100.0
    
    st.subheader("Assumptions")
    equity_return = st.slider("Equity Expected Real Return (%)", 0.0, 12.0, 5.5) / 100.0
    equity_vol = st.slider("Equity Volatility (%)", 5.0, 25.0, 15.0) / 100.0
    inflation_rate = st.slider("Inflation Rate (%)", 1.0, 5.0, 3.0) / 100.0
    
    st.subheader("Retirement Spending Goal")
    annual_spending_goal = st.number_input("Desired Annual Spending in Today's Dollars ($)", min_value=20_000, value=60_000, step=5_000)
    
    st.subheader("Withdrawal Strategy")
    withdrawal_strategy = st.selectbox(
        "Choose Withdrawal Strategy",
        ["Fixed Real Spending", "4% Rule Variant", "Guardrails"]
    )
    
    st.subheader("Social Security Strategy")
    ss_claim_age = st.selectbox("Claim Social Security at Age", [62, 67, 70], index=1)
    ss_monthly_benefit = st.number_input("Estimated Monthly SS Benefit at Full Retirement Age ($)", min_value=0, value=2500, step=100)
    
    num_simulations = st.slider("Number of Monte Carlo Simulations", 1000, 8000, 2500, step=500)

# Main simulation
if st.button("🚀 Run Full CFP Analysis & Recommendations", type="primary"):
    with st.spinner(f"Running {num_simulations:,} lifetime simulations with chosen strategies..."):
        np.random.seed(42)
        
        years_to_retire = desired_retirement_age - current_age
        years_in_retirement = life_expectancy - desired_retirement_age
        
        success_count = 0
        final_balances = []
        
        for _ in range(num_simulations):
            # Starting balances
            bal_taxable = taxable_current
            bal_trad = trad_current
            bal_roth = roth_current
            bal_re = re_value
            bal_pm = pm_value
            balance = bal_taxable + bal_trad + bal_roth + bal_re + bal_pm
            
            # Accumulation phase
            for _ in range(years_to_retire):
                ret_equity = np.random.normal(equity_return, equity_vol)
                ret_pm = np.random.normal(pm_return, pm_vol)
                
                bal_taxable = bal_taxable * (1 + ret_equity) + contrib_taxable
                bal_trad = bal_trad * (1 + ret_equity) + contrib_trad
                bal_roth = bal_roth * (1 + ret_equity) + contrib_roth
                bal_re = bal_re * (1 + re_appreciation) + re_rental_income
                bal_pm = bal_pm * (1 + ret_pm)
                balance = bal_taxable + bal_trad + bal_roth + bal_re + bal_pm
            
            # Withdrawal phase with chosen strategy + SS
            current_spending = annual_spending_goal
            ss_annual = ss_monthly_benefit * 12
            success = True
            
            for year_in_ret in range(years_in_retirement):
                current_age_in_ret = desired_retirement_age + year_in_ret
                
                # Apply chosen withdrawal strategy
                if withdrawal_strategy == "Fixed Real Spending":
                    withdrawal_needed = current_spending
                elif withdrawal_strategy == "4% Rule Variant":
                    withdrawal_needed = annual_spending_goal * 0.04 * (1 + inflation_rate) ** year_in_ret
                else:  # Guardrails (simple version)
                    withdrawal_needed = current_spending
                    if balance < annual_spending_goal * 20:   # bad year
                        withdrawal_needed *= 0.8
                    elif balance > annual_spending_goal * 30:  # good year
                        withdrawal_needed *= 1.1
                
                # Social Security offset
                if current_age_in_ret >= ss_claim_age:
                    withdrawal_needed = max(0, withdrawal_needed - ss_annual)
                
                current_spending *= (1 + inflation_rate)
                
                # Proportional withdrawal from portfolio
                total = bal_taxable + bal_trad + bal_roth + bal_re + bal_pm
                if total <= 0:
                    success = False
                    break
                
                w_taxable = withdrawal_needed * (bal_taxable / total)
                w_trad = withdrawal_needed * (bal_trad / total)
                w_roth = withdrawal_needed * (bal_roth / total)
                w_re = withdrawal_needed * (bal_re / total)
                w_pm = withdrawal_needed * (bal_pm / total)
                
                # Missouri tax drag on Traditional
                trad_after_tax = w_trad * (1 - 0.047)
                
                bal_taxable -= w_taxable
                bal_trad -= w_trad
                bal_roth -= w_roth
                bal_re -= w_re
                bal_pm -= w_pm
                
                # Grow remaining balances
                ret_equity = np.random.normal(equity_return, equity_vol)
                ret_pm = np.random.normal(pm_return, pm_vol)
                bal_taxable *= (1 + ret_equity)
                bal_trad *= (1 + ret_equity)
                bal_roth *= (1 + ret_equity)
                bal_re *= (1 + re_appreciation)
                bal_pm *= (1 + ret_pm)
                
                if bal_taxable + bal_trad + bal_roth + bal_re + bal_pm < 0:
                    success = False
                    break
            
            if success:
                success_count += 1
            final_balances.append(bal_taxable + bal_trad + bal_roth + bal_re + bal_pm)
        
        success_rate = (success_count / num_simulations) * 100
        median_final = np.median(final_balances)
        
        # Display Results
        st.success("✅ Full Lifetime Simulation Complete")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col2:
            st.metric("Median Final Balance", f"${median_final:,.0f}")
        with col3:
            st.metric("Target Retirement Age", f"{desired_retirement_age}")
        
        st.subheader("📋 CFP Analysis & Recommendations")
        st.markdown(f"**Goal**: Retire at **{desired_retirement_age}** with **${annual_spending_goal:,.0f}** annual spending using **{withdrawal_strategy}** and claiming SS at **age {ss_claim_age}**.")
        
        if success_rate >= 80:
            st.success("✅ Strong plan")
        elif success_rate >= 60:
            st.warning("⚠️ Moderate success probability")
        else:
            st.error("❌ Plan needs strengthening")
        
        st.markdown("**Recommended Actions Right Now:**")
        if ss_claim_age < 70:
            st.markdown("- **Delay Social Security to age 70** if possible — each year delayed increases your benefit ~8% and reduces portfolio withdrawals.")
        if withdrawal_strategy == "Guardrails":
            st.markdown("- Guardrails strategy is working well for volatility protection.")
        if trad_current > 0 and current_age < 59.5:
            st.markdown("- Consider a **Roth conversion ladder** now to reduce future Missouri ordinary income tax drag.")
        st.markdown("- Prioritize Roth contributions and review real estate/rental income for tax efficiency.")
        
        st.subheader("Missouri Tax Notes")
        st.markdown("""
        - **Real Estate**: Property taxes apply; capital gains on sale federally taxable (Missouri exemption on primary residence).
        - **Precious Metals**: Treated as collectibles (28% federal long-term capital gains rate).
        - **Traditional**: Ordinary income tax (up to 4.7% Missouri).
        - **Roth**: Tax-free qualified withdrawals.
        - **Social Security**: Missouri does not tax Social Security benefits.
        """)
        
        st.caption("Educational modeling only. Consult a licensed CFP and tax professional.")

else:
    st.info("👆 Enter all your numbers and choose withdrawal + Social Security strategies in the sidebar, then click the button.")

st.caption("Missouri-focused retirement planning tool | GitHub: russellrichards55-lang/cfp-retirement-agent")
