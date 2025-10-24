"""
Experiment design for A/B testing free shipping on orders ≥100 BRL.
Defines hypotheses, computes required sample size, and randomizes groups.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import math
from matplotlib import rcParams
import shutil

# Use LaTeX fonts if available
if shutil.which("latex"):
    rcParams['text.usetex'] = True
    rcParams['font.family'] = 'serif'
else:
    print("LaTeX not found — using default matplotlib fonts.")

# Load order-level data
order_totals = pd.read_csv('../data/processed/order_totals.csv')
print(f"Loaded order_totals: {order_totals.shape}")

# ---- Baseline metrics ----
baseline_revenue = order_totals['order_total'].mean()
baseline_price = order_totals['total_price'].mean()
baseline_shipping = order_totals['total_shipping'].mean()
revenue_std = order_totals['order_total'].std()

print(f"Mean revenue: {baseline_revenue:.2f} BRL | Std: {revenue_std:.2f}")
print(f"Mean shipping: {baseline_shipping:.2f} BRL")

# ---- Minimum detectable effect (MDE) ----
mde_pct = 5.0
mde_abs = baseline_revenue * (mde_pct / 100)
print(f"MDE: {mde_pct}% ({mde_abs:.2f} BRL increase target)")

if mde_abs > baseline_shipping:
    print("Target increase covers shipping costs.")
else:
    print("Target increase below shipping cost — realistic scenario.")

# ---- Power analysis ----
alpha = 0.05
beta = 0.20
power = 1 - beta
z_alpha = stats.norm.ppf(1 - alpha / 2)
z_beta = stats.norm.ppf(power)

numerator = 2 * ((z_alpha + z_beta) ** 2) * (revenue_std ** 2)
denominator = mde_abs ** 2
n_per_group = math.ceil(numerator / denominator)
n_total = n_per_group * 2

print(f"\nPower analysis results:")
print(f"α = {alpha}, Power = {power}, Effect size = {mde_abs:.2f} BRL")
print(f"Required sample size: {n_per_group:,} per group ({n_total:,} total)")
print(f"Available orders: {len(order_totals):,}")

# ---- Randomization ----
np.random.seed(42)
orders_for_experiment = min(n_total, len(order_totals))
experiment_orders = order_totals.sample(n=orders_for_experiment, random_state=42)

experiment_orders['group'] = np.random.choice(
    ['control', 'treatment'],
    size=len(experiment_orders),
    p=[0.5, 0.5]
)

control_mean = experiment_orders[experiment_orders['group'] == 'control']['order_total'].mean()
treatment_mean = experiment_orders[experiment_orders['group'] == 'treatment']['order_total'].mean()
print(f"\nRandomization check:")
print(f"Control mean: {control_mean:.2f} BRL, Treatment mean: {treatment_mean:.2f} BRL")
print(f"Difference: {abs(control_mean - treatment_mean):.2f} BRL (pre-treatment balance)")

# ---- Save experiment design ----
experiment_orders.to_csv('../data/processed/new_experiment_design.csv', index=False)
print(f"Saved: ../data/processed/new_experiment_design.csv ({len(experiment_orders):,} rows)")

# ---- Visualization ----
fig, axes = plt.subplots(1, 2, figsize=(7, 3))
groups = ['Control', 'Treatment']
sizes = [
    (experiment_orders['group'] == 'control').sum(),
    (experiment_orders['group'] == 'treatment').sum()
]
means = [control_mean, treatment_mean]
colors = ['lightblue', 'lightcoral']

# Group size plot
axes[0].bar(groups, sizes, color=colors, edgecolor='black')
axes[0].set_title('Experiment Group Sizes')
axes[0].set_ylabel('Orders')
for i, v in enumerate(sizes):
    axes[0].text(i, v + 200, f'{v:,}', ha='center', va='bottom', fontweight='bold')

# Baseline mean plot
axes[1].bar(groups, means, color=colors, edgecolor='black')
axes[1].set_title('Baseline Revenue per Order')
axes[1].set_ylabel('BRL')
for i, v in enumerate(means):
    axes[1].text(i, v + 5, f'{v:.2f}', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('../results/figures/new_experiment_design_overview.png', dpi=300, bbox_inches='tight')
plt.close()

print("Saved: ../results/figures/new_experiment_design_overview.png")
