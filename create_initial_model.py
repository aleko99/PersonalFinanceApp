import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

def create_initial_model(output_path='financial_advisor_model.joblib'):
    # Generate synthetic data for initial training
    np.random.seed(42)  # for reproducibility
    n_samples = 10000

    # Generate features
    income = np.random.lognormal(mean=10.5, sigma=0.5, size=n_samples)
    expenses = income * np.random.uniform(0.4, 0.9, n_samples)
    debt = np.random.lognormal(mean=9, sigma=1, size=n_samples)
    savings = income * np.random.uniform(0, 0.3, n_samples)
    investments = income * np.random.uniform(0, 0.4, size=n_samples)

    X = np.column_stack((income, expenses, debt, savings, investments))

    # Generate target (financial health score)
    y = (
        0.3 * (income - expenses) / income +  # Income vs Expenses
        0.2 * (1 - debt / income) +           # Debt to Income ratio
        0.2 * savings / income +              # Savings rate
        0.2 * investments / income +          # Investment rate
        0.1 * np.random.random(n_samples)     # Random factor
    )
    y = np.clip(y, 0, 1)  # Ensure score is between 0 and 1

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)

    # Save model and scaler
    joblib.dump((model, scaler), output_path)

    print(f"Initial model created and saved to {output_path}")

# Run this function to create the initial model
if __name__ == "__main__":
    create_initial_model()