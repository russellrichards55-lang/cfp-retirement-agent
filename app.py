import streamlit as st
import numpy as np
from openai import OpenAI

st.set_page_config(page_title="Rusty’s CFP Retirement Agent", layout="wide", page_icon="📈")
st.title("Rusty’s CFP Retirement Planning Agent")
st.markdown("**Missouri-Focused CFP-Level Analysis & Personalized Recommendations**")

# Load API key from secrets
client = OpenAI(
    api_key=st.secrets["api"]["xai_api_key"],
    base_url="https://api.x.ai/v1"
)

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
    annual_spending_goal = st.number_input("Desired Annual Spending in Today's Dollars ($)", min_value=20_000, value=60_000, step=5_000)
    
    st.subheader("Tax Assumptions")
    federal_tax_rate = st.slider("Assumed Effective Federal Tax Rate on Traditional Withdrawals (%)", 0, 37, 22)
    
    st.subheader("Strategies")
    withdrawal_strategy = st.selectbox("Withdrawal Strategy", ["Fixed Real Spending", "4% Rule Variant", "Guardrails"])
    ss_claim_age = st.selectbox("Claim Social Security at Age", [62, 67, 70], index=1)
    ss_monthly_benefit = st.number_input("Estimated Monthly SS Benefit at FRA ($)", min_value=0, value=2500, step=100)
    
    num_simulations = st.slider("Number of Monte Carlo Simulations", 1000, 8000, 1500, step=500)

if st.button("🚀 Run Full CFP Analysis & Recommendations", type="primary"):
    with st.spinner(f"Running {num_simulations:,} simulations..."):
        np.random.seed(42)
        
        years_to_retire = desired_retirement_age - current_age
        years_in_retirement = life_expectancy - desired_retirement_age
        
        success_count = 0
        final_balances = []
        
        combined_tax_rate = (federal_tax_rate / 100.0) + 0.047
        
        for _ in range(num_simulations):
            bal_taxable = float(taxable_current)
            bal_trad = float(trad_current)
            bal_roth = float(roth_current)
            bal_re = float(re_value)
            bal_pm = float(pm_value)
            
            for _ in range(years_to_retire):
                ret_equity = np.random.normal(equity_return, equity_vol)
                ret_pm = np.random.normal(pm_return, pm_vol)
                
                bal_taxable = bal_taxable * (1 + ret_equity) + contrib_taxable
                bal_trad = bal_trad * (1 + ret_equity) + contrib_trad
                bal_roth = bal_roth * (1 + ret_equity) + contrib_roth
                bal_re = bal_re * (1 + re_appreciation) + re_rental_income
                bal_pm = bal_pm * (1 + ret_pm)
            
            current_spending = float(annual_spending_goal)
            ss_annual = float(ss_monthly_benefit * 12)
            success = True
            
            for yr in range(years_in_retirement):
                current_age_in_ret = desired_retirement_age + yr
                
                if withdrawal_strategy == "Fixed Real Spending":
                    wd = current_spending
                elif withdrawal_strategy == "4% Rule Variant":
                    wd = annual_spending_goal * 0.04 * (1 + inflation_rate) ** yr
                else:
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
                    success = False
                    break
                
                w_taxable = wd * (bal_taxable / total)
                w_trad = wd * (bal_trad / total)
                w_roth = wd * (bal_roth / total)
                w_re = wd * (bal_re / total)
                w_pm = wd * (bal_pm / total)
                
                trad_after_tax = w_trad * (1 - combined_tax_rate)
                
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
        
        # Store results in session state for chatbot
        st.session_state.simulation_results = {
            "success_rate": success_rate,
            "median_final": median_final,
            "desired_retirement_age": desired_retirement_age,
            "annual_spending_goal": annual_spending_goal,
            "withdrawal_strategy": withdrawal_strategy,
            "ss_claim_age": ss_claim_age,
            "trad_current": trad_current,
            "re_value": re_value,
            "re_pct": round((re_value / (taxable_current + trad_current + roth_current + re_value + pm_value) * 100), 1) if (taxable_current + trad_current + roth_current + re_value + pm_value) > 0 else 0,
            "federal_tax_rate": federal_tax_rate
        }
        
        st.success("✅ Simulation Complete")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col2:
            st.metric("Target Retirement Age", desired_retirement_age)
        with col3:
            st.metric("Median Final Balance", f"${median_final:,.0f}")

        st.subheader("📋 CFP Analysis & Personalized Recommendations")
        st.markdown(f"**Goal**: Retire at age **{desired_retirement_age}** with **${annual_spending_goal:,.0f}** in today's dollars.")

        if success_rate >= 80:
            st.success("✅ Strong probability of success.")
            st.markdown("- Maintain current path and prioritize Roth contributions.")
            if ss_claim_age < 70:
                st.markdown("- Consider delaying Social Security to age 70.")
        elif success_rate >= 60:
            st.warning("⚠️ Moderate success probability.")
            st.markdown("- Increase Roth contributions.")
            st.markdown("- Consider Roth conversion ladder.")
        else:
            st.error("❌ Low success probability.")
            st.markdown("- Lower spending goal or increase contributions significantly.")
            st.markdown("- Consider delaying retirement.")

        st.subheader("Missouri + Federal Tax Notes")
        st.markdown(f"- Traditional withdrawals taxed at ~**{federal_tax_rate + 4.7}%** combined.")
        st.markdown("- Roth withdrawals are tax-free.")
        st.markdown("- Social Security is not taxed in Missouri.")

# ==================== GROK CHATBOT ====================
st.subheader("💬 Ask Grok (Your CFP Assistant)")
st.caption("Ask questions about your plan, Roth conversions, real estate strategy, etc.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about your retirement plan..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Build context from simulation
            context = f"""
            User inputs:
            - Current age: {current_age}, Desired retirement age: {desired_retirement_age}, Life expectancy: {life_expectancy}
            - Spending goal: ${annual_spending_goal:,} today's dollars
            - Success rate: {success_rate:.1f}%
            - Median final balance: ${median_final:,.0f}
            - Withdrawal strategy: {withdrawal_strategy}
            - SS claiming age: {ss_claim_age}
            - Traditional balance: ${trad_current:,.0f}
            - Real estate value: ${re_value:,.0f} ({st.session_state.simulation_results.get('re_pct', 0)}% of portfolio)
            - Federal tax rate assumption: {federal_tax_rate}%
            
            Please give practical, CFP-style advice based on this data.
            """

            try:
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": "You are a knowledgeable, conservative CFP (Certified Financial Planner) providing fiduciary-style advice. Be clear, actionable, and conservative. Always prioritize tax efficiency and risk management."},
                        {"role": "user", "content": context + "\n\nUser question: " + prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Chatbot error: {str(e)}")

st.caption("The chatbot has access to your simulation results and can give personalized advice. The Grok API is used.")
