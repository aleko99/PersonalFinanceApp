import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
logger = logging.getLogger(__name__)


class AIFinancialAdvisor:
    def __init__(self, model_path='financial_advisor_model.joblib', region='UK'):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.region = region
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model, self.scaler = joblib.load(self.model_path)
        else:
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

    def get_financial_health_score(self, income, expenses, debt, savings, investments):
        features = np.array([[income, expenses, debt, savings, investments]])
        scaled_features = self.scaler.transform(features)
        return self.model.predict(scaled_features)[0]

    def get_feature_importances(self):
        return dict(zip(['Income', 'Expenses', 'Debt', 'Savings', 'Investments'],
                        self.model.feature_importances_))

    def generate_ai_advice(self, income, expenses, debt, savings, investments):
        health_score = self.get_financial_health_score(income, expenses, debt, savings, investments)
        feature_importances = self.get_feature_importances()

        advice = [f"Your overall financial health score is {health_score:.2f} out of 1.00."]

        if health_score < 0.4:
            advice.append("Your financial health needs immediate attention. Let's focus on improvement strategies.")
        elif health_score < 0.7:
            advice.append("Your financial health is moderate. There's room for improvement.")
        else:
            advice.append("Great job! Your financial health is good. Let's optimize further.")

        sorted_importances = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)
        advice.append("\nAreas to focus on, in order of importance:")
        for feature, importance in sorted_importances:
            advice.append(f"{feature}: {importance:.2f}")

        if feature_importances['Debt'] > 0.2:
            advice.append("\nYour debt seems to be a significant factor. Consider these strategies:")
            advice.append("1. Focus on paying off high-interest debt first.")
            advice.append("2. Look into debt consolidation options.")
            advice.append("3. Create a strict budget to allocate more funds to debt repayment.")

        if feature_importances['Savings'] < 0.15:
            advice.append("\nYour savings rate could use a boost. Try these approaches:")
            advice.append("1. Set up automatic transfers to your savings account.")
            advice.append("2. Look for areas in your budget where you can cut back.")
            advice.append("3. Consider setting specific savings goals to stay motivated.")

        if feature_importances['Income'] > 0.3:
            advice.append("\nYour income is a key factor. Here are ways to potentially increase it:")
            advice.append("1. Negotiate a raise or seek promotion opportunities.")
            advice.append("2. Develop new skills to increase your market value.")
            advice.append("3. Consider starting a side hustle or freelancing.")

        advice.extend(self.get_region_specific_advice())

        return advice

    def get_region_specific_advice(self):
        if self.region == 'UK':
            return [
                "\nUK-Specific Financial Advice:",
                "1. Maximize your ISA contributions (£20,000 annual limit) for tax-free savings and investments.",
                "2. Consider opening a Lifetime ISA if you're saving for your first home or retirement.",
                "3. Take advantage of your pension annual allowance (up to £40,000) for tax relief on contributions.",
                "4. Look into the Help to Buy scheme if you're a first-time homebuyer.",
                "5. Consider using a SIPP (Self-Invested Personal Pension) for more control over your pension investments.",
                "6. If you're a homeowner, consider overpaying on your mortgage to reduce interest and term length.",
                "7. Explore National Savings and Investments (NS&I) for secure, government-backed savings options."
            ]
        else:
            return [
                "\nGeneral Investment Advice:",
                "1. Diversify your investment portfolio across different asset classes.",
                "2. Consider low-cost index funds for broad market exposure.",
                "3. Regularly review and rebalance your investment portfolio.",
                "4. Look into tax-efficient investment options available in your region.",
                "5. Consider seeking advice from a qualified financial advisor for personalized strategies."
            ]
class EnhancedSmartSavingsAdvisor:
    def __init__(self, transaction_model, debt_model, savings_model, investment_model, region='UK'):
        self.transaction_model = transaction_model
        self.debt_model = debt_model
        self.savings_model = savings_model
        self.investment_model = investment_model
        self.ai_advisor = AIFinancialAdvisor(region=region)

    def generate_comprehensive_advice(self):
        income, expenses = self.analyze_cash_flow()
        total_expenses = sum(expenses.values())
        debt = sum(debt['balance'] for debt in self.analyze_debts())
        savings = self.analyze_savings()
        investments = sum(inv['amount'] for inv in self.analyze_investments())

        ai_advice = self.ai_advisor.generate_ai_advice(income, total_expenses, debt, savings, investments)

        advice = ai_advice + ["\nAdditional Insights:"]
        advice.extend(self.generate_expense_optimization_advice(expenses))
        advice.extend(self.generate_investment_strategy(self.analyze_investments(), income - total_expenses))
        advice.extend(self.generate_wealth_building_tips())

        return advice

    def analyze_cash_flow(self) -> Tuple[float, Dict[str, float]]:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        transactions = self.transaction_model.get_transactions_in_range(start_date, end_date)

        income = sum(float(t[3]) for t in transactions if t[4] == 'Income')
        expenses = {
            category: sum(float(t[3]) for t in transactions if t[2] == category and t[4] == 'Expense')
            for category in set(t[2] for t in transactions if t[4] == 'Expense')
        }

        return income, expenses

    def analyze_debts(self) -> List[Dict]:
        return [
            {"name": d[1], "balance": d[2], "apr": d[3]}
            for d in self.debt_model.get_all_debts()
        ]

    def analyze_savings(self) -> float:
        return self.savings_model.calculate_total_savings()

    def analyze_investments(self) -> List[Dict]:
        return self.investment_model.get_all_investments()

    def generate_income_advice(self, income: float, expenses: Dict[str, float]) -> List[str]:
        advice = []
        total_expenses = sum(expenses.values())

        if income <= total_expenses:
            advice.append(
                "Your expenses are currently exceeding or matching your income. Focus on increasing your income through the following methods:")
            advice.append("1. Negotiate a salary raise or seek promotion opportunities in your current job.")
            advice.append("2. Develop new skills to increase your market value.")
            advice.append("3. Consider starting a side business or freelancing to create additional income streams.")
        else:
            savings_rate = (income - total_expenses) / income * 100
            if savings_rate < 20:
                advice.append(
                    f"Your current savings rate is {savings_rate:.2f}%. Aim to increase this to at least 20% by optimizing expenses and increasing income.")
            else:
                advice.append(
                    f"Great job! Your savings rate is {savings_rate:.2f}%. Consider allocating more towards investments to accelerate wealth building.")

        return advice

    def generate_expense_optimization_advice(self, expenses: Dict[str, float]) -> List[str]:
        advice = []
        total_expenses = sum(expenses.values())

        # Identify top expense categories
        top_expenses = sorted(expenses.items(), key=lambda x: x[1], reverse=True)[:3]

        advice.append("Expense Optimization Strategies:")
        for category, amount in top_expenses:
            percentage = (amount / total_expenses) * 100
            advice.append(f"- {category}: ${amount:.2f} ({percentage:.2f}% of total expenses)")

            if category == "Housing":
                advice.append("  Consider house hacking or relocating to reduce housing costs.")
            elif category == "Transportation":
                advice.append("  Evaluate public transportation options or consider carpooling to reduce costs.")
            elif category == "Food":
                advice.append("  Meal prep and reduce dining out to optimize food expenses.")
            else:
                advice.append(
                    f"  Look for ways to reduce {category.lower()} expenses without sacrificing quality of life.")

        return advice

    def generate_debt_elimination_strategy(self, debts: List[Dict], available_cash: float) -> List[str]:
        advice = []

        if not debts:
            advice.append(
                "Congratulations! You have no debts. Focus on building wealth through savings and investments.")
            return advice

        total_debt = sum(debt['balance'] for debt in debts)
        highest_apr_debt = max(debts, key=lambda x: x['apr'])

        advice.append(f"Total Debt: ${total_debt:.2f}")
        advice.append("Debt Elimination Strategy:")
        advice.append(
            f"1. Focus on paying off the highest interest debt first: {highest_apr_debt['name']} (APR: {highest_apr_debt['apr']}%)")
        advice.append(
            f"2. Allocate at least 50% of your available cash (${available_cash * 0.5:.2f}) towards debt repayment.")
        advice.append("3. Consider debt consolidation or refinancing for lower interest rates.")
        advice.append("4. Avoid taking on new debt while paying off existing obligations.")

        return advice

    def generate_savings_strategy(self, current_savings: float, available_cash: float) -> List[str]:
        advice = []

        emergency_fund_goal = available_cash * 6  # 6 months of expenses

        advice.append(f"Current Savings: ${current_savings:.2f}")
        advice.append("Savings Strategy:")

        if current_savings < emergency_fund_goal:
            advice.append(f"1. Build an emergency fund of ${emergency_fund_goal:.2f} (6 months of expenses)")
            advice.append(
                f"2. Allocate 30% of available cash (${available_cash * 0.3:.2f}) towards your emergency fund")
        else:
            advice.append("Great job on your emergency fund! Consider the following:")
            advice.append("1. Maximize contributions to tax-advantaged retirement accounts")
            advice.append("2. Open a high-yield savings account for short-term goals")

        return advice

    def generate_investment_strategy(self, investments: List[Dict], available_cash: float) -> List[str]:
        advice = []

        total_investments = sum(inv['amount'] for inv in investments)
        advice.append(f"Current Investment Portfolio: ${total_investments:.2f}")
        advice.append("Investment Strategy:")
        advice.append("1. Diversify your portfolio across different asset classes:")
        advice.append("   - Stocks (60-80%): For long-term growth")
        advice.append("   - Bonds (20-30%): For stability and income")
        advice.append("   - Real Estate (10-20%): For diversification and potential passive income")
        advice.append(f"2. Allocate at least 20% of available cash (${available_cash * 0.2:.2f}) towards investments")
        advice.append("3. Consider low-cost index funds for broad market exposure")
        advice.append("4. Regularly rebalance your portfolio to maintain your target asset allocation")

        return advice

    def generate_wealth_building_tips(self) -> List[str]:
        advice = [
            "Wealth Building Strategies:",
            "1. Develop multiple income streams to accelerate wealth accumulation",
            "2. Continuously educate yourself on financial management and investment strategies",
            "3. Network with successful individuals in your field to create opportunities",
            "4. Consider starting a business or investing in startups for potentially high returns",
            "5. Leverage tax-efficient investment vehicles like 401(k)s, IRAs, and 529 plans",
            "6. Invest in yourself through education, skills development, and health to increase your earning potential",
            "7. Practice delayed gratification and avoid lifestyle inflation as your income grows",
            "8. Regularly review and optimize your financial strategy to adapt to changing circumstances"
        ]
        return advice