import streamlit as st
import numpy as np

st.set_page_config(page_title="Rusty’s CFP Retirement Agent", layout="wide", page_icon="📈")
st.title("Rusty’s CFP Retirement Planning Agent")
st.markdown("**Missouri-Focused Analysis & Actionable Recommendations**")

# Sidebar inputs
with st.sidebar:
    st.header("Personal Details")
    current_age = st.number_input("Current Age", min_value=20, max_value=100, value=55)
    desired_retirement_age = st.number_input("Desired Retirement Age", min_value=current_age + 1, max_value=100, value=60)
    life_expectancy = st.number_input("Life Expectancy (for planning)", min_value=desired_retirement_age + 1, max_value=120, value=95)
    
    st.header("Retirement Accounts")
    taxable_current = st.number_input("Taxable Brokerage ($)", min_value=0, value=200_000, step=10_000)
    trad_current = st.number_input("Traditional IRA/401(k) ($)", min_value=0, value=200_000, step=10_000)
    roth_current = st.number_input("Roth IRA/401(k) ($)", min_value=0, value=100_000, step=10_000)
    
    st.header("Annual Contributions")
    contrib_taxable = st.number_input("Annual to Taxable Brokerage ($)", min_value=0, value=6_000, step=1_000)
    contrib_trad = st.number_input("Annual to Traditional ($)", min_value=0, value=10_000, step=1_000)
    contrib_roth = st.number_input("Annual to Roth ($)", min_value=0, value=4_000, step=1_000)
    
    st.header("Other Assets")
    re_value = st.number_input("Current Real Estate Value ($)", min_value=0, value=300_000, step=10_000)
    re_appreciation = st.slider("Real Estate Appreciation (%)", 0.0, 8.0, 3.5) / 100.0
    re_rental_income = st.number_input("Net Annual Rental Income ($)", min_value=0, value=12_000, step=1_000)
    
    pm_value = st.number_input("Current Precious Metals Value ($)", min_value=0, value=50_000, step=5_000)
    pm_return = st.slider("Precious Metals Return (%)", 0.0, 10.0, 4.0) / 100.0
    pm_vol = st.slider("Precious Metals Volatility (%)", 5.0, 30.0, 18.0) / 100.0
    
    st.subheader("Assumptions")
    equity_return = st.slider("Equity Expected Real Return (%)", 0.0, 12.0, 5.5) / 100.0
    equity_vol = st.slider("Equity Volatility (%)", 5.0, 25.0, 15.0) / 100.0
    inflation_rate = st.slider("Inflation Rate (%)", 1.0, 5.0, 3.0) / 100.0
    
    st.subheader("Retirement Spending")
    annual_spending_goal = st.number_input("Desired Annual Spending (Today's $)", min_value=20_000, value=60_000, step=5_000)
    
    st.subheader("Strategies")
    withdrawal_strategy = st.selectbox("Withdrawal Strategy", ["Fixed Real Spending", "4% Rule Variant", "Guardrails"])
    ss_claim_age = st.selectbox("Claim Social Security at Age", [62, 67, 70], index=1)
    ss_monthly_benefit = st.number_input("Estimated Monthly SS Benefit at FRA ($)", min_value=0, value=2500, step=100)
    
    num_simulations = st.slider("Number of Monte Carlo Simulations", 1000, 8000, 2000, step=500)

if st.button("🚀 Run Full CFP Analysis & Recommendations", type="primary"):
    with st.spinner(f"Running {num_simulations:,} simulations..."):
        np.random.seed(42)
        
        years_to_retire = desired_retirement_age - current_age
        years_in_retirement = life_expectancy - desired_retirement_age
        
        success_count = 0
        final_balances = []
        
        for _ in range(num_simulations):
            bal_taxable = float(taxable_current)
            bal_trad = float(trad_current)
            bal_roth = float(roth_current)
            bal_re = float(re_value)
            bal_pm = float(pm_value)
            
            # Accumulation phase
            for _ in range(years_to_retire):
                ret_equity = np.random.normal(equity_return, equity_vol)
                ret_pm = np.random.normal(pm_return, pm_vol)
                
                bal_taxable = bal_taxable * (1 + ret_equity) + contrib_taxable
                bal_trad = bal_trad * (1 + ret_equity) + contrib_trad
                bal_roth = bal_roth * (1 + ret_equity) + contrib_roth
                bal_re = bal_re * (1 + re_appreciation) + re_rental_income
                bal_pm = bal_pm * (1 + ret_pm)
            
            # Withdrawal phase
            current_spending = float(annual_spending_goal)
            ss_annual = float(ss_monthly_benefit * 12)
            
            for yr in range(years_in_retirement):
                current_age_in_ret = desired_retirement_age + yr
                
                if withdrawal_strategy == "Fixed Real Spending":
                    wd = current_spending
                elif withdrawal_strategy == "4% Rule Variant":
                    wd = annual_spending_goal * 0.04 * (1 + inflation_rate) ** yr
                else:  # Guardrails
                    wd = current_spending
                    total_balance = bal_taxable + bal_trad + bal_roth + bal_re + bal_pm
                    if total_balance < annual_spending_goal * 20:
                        wd *= 0.8
                    elif total_balance > annual_spending_goal * 30:
                        wd *= 1.1
                
                if current_age_in_ret >= ss_claim_age:
                    wd = max(0, wd - ss_annual)
                
                current_spending *= (1 + inflation_rate)
                
                total = bal_taxable + bal_trad + bal_roth + bal_re + bal_pm
                if total <= 0:
                    break
                
                w_taxable = wd * (bal_taxable / total)
                w_trad = wd * (bal_trad / total)
                w_roth = wd * (bal_roth / total)
                w_re = wd * (bal_re / total)
                w_pm = wd * (bal_pm / total)
                
                bal_taxable -= w_taxable
                bal_trad -= w_trad
                bal_roth -= w_roth
                bal_re -= w_re
                bal_pm -= w_pm
                
                ret_equity = np.random.normal(equity_return, equity_vol)
                ret_pm = np.random.normal(pm_return, pm_vol)
                bal_taxable *= (1 + ret_equity)
                bal_trad *= (1 + ret_equity)
                bal_roth *= (1 + ret_equity)
                bal_re *= (1 + re_appreciation)
                bal_pm *= (1 + ret_pm)
            
            final_balance = bal_taxable + bal_trad + bal_roth + bal_re + bal_pm
            final_balances.append(final_balance)
            
            if final_balance >= 0:
                success_count += 1
        
        success_rate = (success_count / num_simulations) * 100
        median_final = np.median(final_balances) if final_balances else 0
        
        # Results
        st.success("✅ Simulation Complete")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col2:
            st.metric("Target Retirement Age", desired_retirement_age)
        with col3:
            st.metric("Median Final Balance", f"${median_final:,.0f}")

        st.subheader("📋 CFP Analysis & Recommendations")
        
        st.markdown(f"**Goal**: Retire at age **{desired_retirement_age}** with **${annual_spending_goal:,.0f}** annual spending.")

        if success_rate >= 80:
            st.success("✅ Strong probability of success.")
            st.markdown("- Your plan looks solid with current contributions and strategies.")
            if ss_claim_age < 70:
                st.markdown("- Delaying Social Security to age 70 would further strengthen the plan.")
        
        elif success_rate >= 60:
            st.warning("⚠️ Moderate success probability.")
            st.markdown("**Recommended Actions:**")
            st.markdown("- Increase Roth contributions")
            st.markdown("- Consider Roth conversion ladder")
            if ss_claim_age < 70:
                st.markdown("- Delay Social Security to age 70 to reduce portfolio drawdown")
        
        else:
            st.error("❌ Low success probability — significant changes needed.")
            st.markdown("**Priority Actions Right Now:**")
            st.markdown("- **Lower annual spending goal** (try reducing by $10,000–$20,000)")
            st.markdown("- **Increase annual contributions** aggressively (especially to Roth)")
            st.markdown("- Consider delaying retirement by 2–5 years")
            st.markdown("- Explore part-time income or downsizing real estate in early retirement")

        st.subheader("Missouri Tax Notes")
        st.markdown("""
        - Social Security is **not taxed** in Missouri.
        - Traditional withdrawals are taxed as ordinary income (up to 4.7%).
        - Roth withdrawals are completely tax-free.
        """)
        
        st.caption("Educational modeling only. Consult a licensed CFP and tax professional.")

else:
    st.info("👆 Enter your information and click the button above.")

st.caption("Missouri-focused retirement planning tool | GitHub: russellrichards55-lang/cfp-retirement-agent")
