"""Generate a synthetic telecom customer dataset (~10k rows) for churn analysis.

Seeded RNG for reproducibility. All data is synthetic — no real customer data.
"""
import numpy as np
import pandas as pd

SEED = 42
N = 10_000

rng = np.random.default_rng(SEED)

customer_id = [f"CUST-{i:06d}" for i in range(1, N + 1)]

# Tenure: skewed toward newer customers (many customers are recent)
tenure_months = rng.integers(1, 73, N)
tenure_months = np.minimum(tenure_months, rng.integers(1, 49, N))  # bias shorter

# Monthly charges ~ lognormal, clamped to realistic band
monthly_charges = np.clip(rng.lognormal(mean=4.25, sigma=0.32, size=N), 25, 150).round(2)

# Contract type: short-tenure customers skew month-to-month
contract_type = np.empty(N, dtype=object)
for i in range(N):
    t = tenure_months[i]
    if t <= 6:
        p = [0.75, 0.15, 0.10]   # month-to-month, one-year, two-year
    elif t <= 24:
        p = [0.45, 0.35, 0.20]
    else:
        p = [0.20, 0.40, 0.40]
    contract_type[i] = rng.choice(["Month-to-month", "One year", "Two year"], p=p)

# Payment method
payment_method = rng.choice(
    ["Electronic check", "Mailed check", "Bank transfer", "Credit card"],
    size=N, p=[0.30, 0.15, 0.30, 0.25],
)

# Internet service
internet_service = rng.choice(
    ["Fiber optic", "DSL", "No internet"], size=N, p=[0.50, 0.35, 0.15]
)

# Support calls: 0..8, Poisson-ish
support_calls = np.clip(rng.poisson(lam=1.4, size=N), 0, 8)

# Signup date: random day between 2022-01-01 and 2025-12-31
signup_date = pd.to_datetime(rng.integers(0, 1461, N), unit="D",
                             origin=pd.Timestamp("2022-01-01"))

# Region
region = rng.choice(["Northeast", "Midwest", "South", "West"],
                    size=N, p=[0.20, 0.22, 0.33, 0.25])

total_charges = (tenure_months * monthly_charges).round(2)

# ---- Churn probability: drivers are month-to-month contract, short tenure,
# many support calls, high monthly charges (fiber), electronic check ----
churn_prob = np.full(N, 0.06)
churn_prob[contract_type == "Month-to-month"] += 0.22
churn_prob[contract_type == "One year"] += 0.06
churn_prob[tenure_months <= 6] += 0.10
churn_prob[tenure_months <= 12] += 0.04
churn_prob[support_calls >= 4] += 0.18
churn_prob[(support_calls >= 2) & (support_calls < 4)] += 0.06
churn_prob[monthly_charges > 100] += 0.08
churn_prob[internet_service == "Fiber optic"] += 0.05
churn_prob[payment_method == "Electronic check"] += 0.05
churn_prob = np.clip(churn_prob, 0.01, 0.90)

churned = (rng.random(N) < churn_prob).astype(int)

# Churn reasons for churned customers
reasons = [
    "Price too high",
    "Poor customer service",
    "Competitor offered better deal",
    "Frequent service outages",
    "Moving / relocation",
]
reason_weights = {
    "Month-to-month": [0.35, 0.15, 0.20, 0.15, 0.15],
    "One year":       [0.25, 0.20, 0.20, 0.15, 0.20],
    "Two year":       [0.20, 0.20, 0.15, 0.15, 0.30],
}
churn_reason = np.empty(N, dtype=object)
churn_reason[churned == 0] = np.nan
churned_idx = np.where(churned == 1)[0]
for i in churned_idx:
    churn_reason[i] = rng.choice(reasons, p=reason_weights[contract_type[i]])

df = pd.DataFrame({
    "customer_id": customer_id,
    "signup_date": signup_date,
    "region": region,
    "contract_type": contract_type,
    "payment_method": payment_method,
    "internet_service": internet_service,
    "tenure_months": tenure_months,
    "monthly_charges": monthly_charges,
    "total_charges": total_charges,
    "support_calls": support_calls,
    "churned": churned,
    "churn_reason": churn_reason,
})

df.to_csv("data_customers.csv", index=False)
print(f"Saved {len(df):,} rows -> data_customers.csv")
print(f"Overall churn rate: {df['churned'].mean():.2%}")
