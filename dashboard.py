"""Build a self-contained interactive HTML dashboard with Plotly.

No server required — open dashboard.html in any browser. All charts are
interactive (hover, zoom, legend filtering).
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

df = pd.read_csv("data_customers.csv")
df["signup_date"] = pd.to_datetime(df["signup_date"])

BLUE, RED, GREEN, ORANGE, TEAL = "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#17becf"
BG = "#f4f6fa"

overall = df["churned"].mean()
total = len(df)
churned_n = int(df["churned"].sum())
avg_tenure = df["tenure_months"].mean()
avg_charge = df["monthly_charges"].mean()
rev_at_risk = float(df.loc[df["churned"] == 1, "monthly_charges"].sum())

# ---------- KPI cards (styled HTML) ----------
def card(label, value, sub=""):
    return (
        f'<div class="card"><div class="card-label">{label}</div>'
        f'<div class="card-value">{value}</div>'
        f'<div class="card-sub">{sub}</div></div>'
    )

cards_html = (
    card("Total Customers", f"{total:,}", "synthetic telecom dataset")
    + card("Overall Churn Rate", f"{overall:.1%}", f"{churned_n:,} customers churned")
    + card("Avg Tenure", f"{avg_tenure:.1f} mo", "all customers")
    + card("Avg Monthly Charge", f"${avg_charge:.2f}", "all customers")
    + card("Monthly Revenue at Risk", f"${rev_at_risk:,.0f}", "churned customers")
)

# ---------- Chart 1: churn by contract ----------
by_contract = df.groupby("contract_type")["churned"].mean().reindex(
    ["Month-to-month", "One year", "Two year"])
fig1 = go.Figure(go.Bar(
    x=by_contract.index, y=by_contract.values,
    marker_color=[RED, ORANGE, GREEN],
    text=[f"{v:.1%}" for v in by_contract.values], textposition="outside",
    hovertemplate="%{x}<br>Churn rate: %{y:.1%}<extra></extra>"))
fig1.update_layout(title="Churn Rate by Contract Type", yaxis_tickformat=".0%",
                   yaxis_title="Churn rate", height=380)

# ---------- Chart 2: churn by tenure bucket ----------
df["tenure_bucket"] = pd.cut(
    df["tenure_months"], bins=[0, 6, 12, 24, 48, 72],
    labels=["0-6 mo", "7-12 mo", "1-2 yr", "2-4 yr", "4+ yr"])
by_tenure = df.groupby("tenure_bucket", observed=True)["churned"].mean()
fig2 = go.Figure(go.Bar(
    x=by_tenure.index.astype(str), y=by_tenure.values,
    marker_color=BLUE,
    text=[f"{v:.1%}" for v in by_tenure.values], textposition="outside",
    hovertemplate="%{x}<br>Churn rate: %{y:.1%}<extra></extra>"))
fig2.update_layout(title="Churn Rate by Tenure Bucket", yaxis_tickformat=".0%",
                   yaxis_title="Churn rate", height=380)

# ---------- Chart 3: tenure vs charges scatter ----------
sample = df.sample(min(2000, len(df)), random_state=42)
fig3 = px.scatter(
    sample, x="tenure_months", y="monthly_charges",
    color=sample["churned"].map({0: "Retained", 1: "Churned"}),
    color_discrete_map={"Retained": GREEN, "Churned": RED},
    labels={"tenure_months": "Tenure (months)", "monthly_charges": "Monthly charges ($)",
            "color": "Status"},
    title="Tenure vs Monthly Charges (2,000-customer sample)",
    hover_data=["contract_type", "support_calls"],
    opacity=0.55, height=420)
fig3.update_layout(legend_title_text="Status")

# ---------- Chart 4: monthly trend ----------
df["signup_month"] = df["signup_date"].dt.to_period("M").dt.to_timestamp()
trend = df.groupby("signup_month")["churned"].agg(["mean", "count"])
trend = trend[trend["count"] >= 100]
fig4 = go.Figure()
fig4.add_trace(go.Scatter(
    x=trend.index, y=trend["mean"], mode="lines+markers",
    name="Monthly churn rate", line=dict(color=BLUE, width=2.5),
    hovertemplate="%{x|%b %Y}<br>Churn: %{y:.1%}<extra></extra>"))
fig4.add_hline(y=overall, line_dash="dash", line_color="gray",
               annotation_text=f"Overall avg {overall:.1%}")
fig4.update_layout(title="Monthly Churn Rate Trend (by signup cohort)",
                   yaxis_tickformat=".0%", yaxis_title="Churn rate", height=380)

# ---------- Chart 5: churn reasons ----------
reasons = df.loc[df["churned"] == 1, "churn_reason"].value_counts()
fig5 = go.Figure(go.Pie(
    labels=reasons.index, values=reasons.values, hole=0.4,
    hovertemplate="%{label}<br>%{percent} (%{value:,} customers)<extra></extra>"))
fig5.update_layout(title="Churn Reasons", height=420)

# ---------- Chart 6: churn by payment method ----------
by_pay = df.groupby("payment_method")["churned"].mean().sort_values()
fig6 = go.Figure(go.Bar(
    x=by_pay.values, y=by_pay.index, orientation="h",
    marker_color=TEAL,
    text=[f"{v:.1%}" for v in by_pay.values], textposition="outside",
    hovertemplate="%{y}<br>Churn rate: %{x:.1%}<extra></extra>"))
fig6.update_layout(title="Churn Rate by Payment Method", xaxis_tickformat=".0%",
                   xaxis_title="Churn rate", height=380)

# ---------- Assemble ----------
dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Customer Churn Insights Dashboard</title>
<style>
  body {{ font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
         background: {BG}; margin: 0; padding: 24px; color: #222; }}
  .container {{ max-width: 1200px; margin: auto; }}
  h1 {{ margin: 0 0 4px; }}
  .subtitle {{ color: #666; margin-bottom: 24px; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px; margin-bottom: 24px; }}
  .card {{ background: #fff; border-radius: 10px; padding: 18px;
          box-shadow: 0 1px 4px rgba(0,0,0,.08); border-top: 4px solid {BLUE}; }}
  .card-label {{ font-size: 12px; color: #888; text-transform: uppercase;
                 letter-spacing: .5px; }}
  .card-value {{ font-size: 30px; font-weight: 700; margin: 6px 0 2px; }}
  .card-sub {{ font-size: 12px; color: #999; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .full {{ grid-column: 1 / -1; }}
  .plot {{ background: #fff; border-radius: 10px; padding: 8px;
           box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  .footer {{ color: #999; font-size: 12px; margin-top: 24px; text-align: center; }}
  @media (max-width: 800px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">
  <h1>📊 Customer Churn Insights Dashboard</h1>
  <div class="subtitle">Telecom customer churn analysis &mdash; synthetic dataset of
    {total:,} customers &middot; Generated with Python (pandas + Plotly)</div>
  <div class="cards">{cards_html}</div>
  <div class="grid">
    <div class="plot">__FIG1__</div>
    <div class="plot">__FIG2__</div>
    <div class="plot full">__FIG3__</div>
    <div class="plot full">__FIG4__</div>
    <div class="plot">__FIG5__</div>
    <div class="plot">__FIG6__</div>
  </div>
  <div class="footer">Author: Akshitha Yedla &middot; Data: synthetic (generate_data.py, seed 42)
    &middot; Open this file in any browser &mdash; no server required.</div>
</div>
</body>
</html>"""

figs = [fig1, fig2, fig3, fig4, fig5, fig6]
for i, fig in enumerate(figs, start=1):
    div = fig.to_html(full_html=False, include_plotlyjs=(i == 1), div_id=f"chart{i}")
    dashboard_html = dashboard_html.replace(f"__FIG{i}__", div)

with open("dashboard.html", "w") as f:
    f.write(dashboard_html)

print(f"dashboard.html written ({len(dashboard_html)/1024:.0f} KB) — open in a browser.")
