"""Churn analysis on the synthetic telecom dataset.

Computes churn rates by segment, identifies top churn drivers, and saves
charts to images/. Prints key findings to stdout.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"figure.dpi": 120, "axes.grid": True,
                     "grid.alpha": 0.3, "font.size": 10})
COLORS = {"churned": "#d62728", "retained": "#2ca02c",
          "primary": "#1f77b4", "accent": "#ff7f0e"}

df = pd.read_csv("data_customers.csv")
df["signup_date"] = pd.to_datetime(df["signup_date"])

print("=" * 60)
print("CUSTOMER CHURN ANALYSIS")
print("=" * 60)
print(f"\nCustomers analyzed: {len(df):,}")

# ---- Overall churn rate ----
overall = df["churned"].mean()
print(f"Overall churn rate: {overall:.2%}")

# ---- Tenure buckets ----
df["tenure_bucket"] = pd.cut(
    df["tenure_months"],
    bins=[0, 6, 12, 24, 48, 72],
    labels=["0-6 mo", "7-12 mo", "1-2 yr", "2-4 yr", "4+ yr"],
)
by_tenure = df.groupby("tenure_bucket", observed=True)["churned"].mean().sort_index()

# ---- By segment ----
by_contract = df.groupby("contract_type")["churned"].mean().sort_values(ascending=False)
by_payment = df.groupby("payment_method")["churned"].mean().sort_values(ascending=False)
by_internet = df.groupby("internet_service")["churned"].mean().sort_values(ascending=False)
by_region = df.groupby("region")["churned"].mean().sort_values(ascending=False)
by_support = df.groupby("support_calls")["churned"].mean()

print("\n--- Churn rate by contract type ---")
for k, v in by_contract.items():
    print(f"  {k:14s}: {v:.2%}")
print("\n--- Churn rate by tenure bucket ---")
for k, v in by_tenure.items():
    print(f"  {k:10s}: {v:.2%}")
print("\n--- Churn rate by payment method ---")
for k, v in by_payment.items():
    print(f"  {k:17s}: {v:.2%}")
print("\n--- Churn rate by internet service ---")
for k, v in by_internet.items():
    print(f"  {k:12s}: {v:.2%}")

# ---- Support-call correlation ----
corr = df["support_calls"].corr(df["churned"])
print(f"\nSupport calls <-> churn correlation: {corr:.3f}")

# ---- Monthly charges distribution: churned vs retained ----
churned_charges = df.loc[df["churned"] == 1, "monthly_charges"]
retained_charges = df.loc[df["churned"] == 0, "monthly_charges"]
print(f"\nAvg monthly charge — churned:  ${churned_charges.mean():.2f}")
print(f"Avg monthly charge — retained: ${retained_charges.mean():.2f}")
print(f"Difference: ${churned_charges.mean() - retained_charges.mean():.2f}")

# ---- Top churn drivers (relative lift over average) ----
print("\n--- Top churn drivers (churn rate vs overall avg) ---")
segments = {}
for col in ["contract_type", "payment_method", "internet_service", "region"]:
    for k, v in df.groupby(col)["churned"].mean().items():
        segments[f"{col} = {k}"] = v
for seg, rate in sorted(segments.items(), key=lambda x: x[1], reverse=True)[:6]:
    print(f"  {seg:38s}: {rate:.2%} ({rate/overall - 1:+.1%} lift)")

# ---- Churn reasons ----
reasons = df.loc[df["churned"] == 1, "churn_reason"].value_counts(normalize=True)
print("\n--- Churn reasons (share of churned) ---")
for k, v in reasons.items():
    print(f"  {k:32s}: {v:.1%}")

# ---- Monthly churn trend ----
df["signup_month"] = df["signup_date"].dt.to_period("M").dt.to_timestamp()
trend = df.groupby("signup_month")["churned"].agg(["mean", "count"])
trend = trend[trend["count"] >= 100]  # stable cohorts only

# ================= CHARTS =================
def barh(ax, series, title, xlabel):
    series = series.sort_values()
    ax.barh(series.index.astype(str), series.values, color=COLORS["primary"])
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel(xlabel)
    for i, v in enumerate(series.values):
        ax.text(v + 0.005, i, f"{v:.1%}", va="center", fontsize=9)

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle("Churn Rate by Segment", fontsize=14, fontweight="bold")
barh(axes[0, 0], by_contract, "By Contract Type", "Churn rate")
barh(axes[0, 1], by_payment, "By Payment Method", "Churn rate")
barh(axes[1, 0], by_internet, "By Internet Service", "Churn rate")
barh(axes[1, 1], by_tenure, "By Tenure Bucket", "Churn rate")
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("images/churn_by_segment.png", bbox_inches="tight")
plt.close()

# Charges distribution
fig, ax = plt.subplots(figsize=(9, 5))
ax.hist(retained_charges, bins=40, alpha=0.6, label="Retained", color=COLORS["retained"])
ax.hist(churned_charges, bins=40, alpha=0.6, label="Churned", color=COLORS["churned"])
ax.axvline(retained_charges.mean(), color=COLORS["retained"], ls="--", lw=2)
ax.axvline(churned_charges.mean(), color=COLORS["churned"], ls="--", lw=2)
ax.set_title("Monthly Charges: Churned vs Retained", fontweight="bold")
ax.set_xlabel("Monthly charges ($)")
ax.set_ylabel("Customers")
ax.legend()
plt.savefig("images/charges_distribution.png", bbox_inches="tight")
plt.close()

# Support calls
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(by_support.index, by_support.values, marker="o", color=COLORS["accent"], lw=2)
ax.fill_between(by_support.index, by_support.values, alpha=0.2, color=COLORS["accent"])
ax.axhline(overall, ls="--", color="gray", label=f"Overall avg ({overall:.1%})")
ax.set_title("Churn Rate by Number of Support Calls", fontweight="bold")
ax.set_xlabel("Support calls")
ax.set_ylabel("Churn rate")
ax.legend()
plt.savefig("images/support_calls_churn.png", bbox_inches="tight")
plt.close()

# Monthly trend
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(trend.index, trend["mean"], marker="o", ms=4, color=COLORS["primary"], lw=2)
ax.axhline(overall, ls="--", color="gray", label=f"Overall avg ({overall:.1%})")
ax.set_title("Monthly Churn Rate Trend (by signup cohort)", fontweight="bold")
ax.set_xlabel("Signup month")
ax.set_ylabel("Churn rate")
ax.legend()
plt.gcf().autofmt_xdate()
plt.savefig("images/churn_trend.png", bbox_inches="tight")
plt.close()

# Churn reasons
fig, ax = plt.subplots(figsize=(9, 5))
r = reasons.sort_values()
ax.barh(r.index, r.values, color=COLORS["churned"])
ax.set_title("Churn Reasons (share of churned customers)", fontweight="bold")
ax.set_xlabel("Share of churned customers")
for i, v in enumerate(r.values):
    ax.text(v + 0.005, i, f"{v:.1%}", va="center", fontsize=9)
plt.savefig("images/churn_reasons.png", bbox_inches="tight")
plt.close()

print("\nCharts saved to images/:")
print("  - churn_by_segment.png, charges_distribution.png,")
print("  - support_calls_churn.png, churn_trend.png, churn_reasons.png")

# ---- KPI summary for reuse ----
df.groupby(["contract_type", "tenure_bucket"], observed=True)["churned"].mean().to_csv(
    "churn_summary_contract_tenure.csv")
print("\nSaved segment summary: churn_summary_contract_tenure.csv")
