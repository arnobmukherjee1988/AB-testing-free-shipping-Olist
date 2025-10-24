"""
Simulate treatment effects for free-shipping A/B test.
Models customer behavior change, computes revenue impact, and validates results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from matplotlib import rcParams
import shutil

# Use LaTeX fonts if available
if shutil.which("latex"):
    rcParams['text.usetex'] = True
    rcParams['font.family'] = 'serif'
else:
    print("LaTeX not found — using default matplotlib fonts.")

np.random.seed(42)

# ---- Load data ----
experiment_orders = pd.read_csv('../data/processed/new_experiment_design.csv')
print(f"Loaded experiment design: {experiment_orders.shape}")
print(experiment_orders['group'].value_counts())

# ---- Identify eligible customers ----
experiment_results = experiment_orders.copy()
experiment_results['below_threshold'] = experiment_results['total_price'] < 100

control_below = experiment_results.query("group == 'control' and below_threshold").shape[0]
treatment_below = experiment_results.query("group == 'treatment' and below_threshold").shape[0]
print(f"Eligible treatment customers below 100 BRL: {treatment_below}")

# ---- Simulate treatment response ----
response_rate = 0.40
min_add, max_add = 15, 35

treatment_eligible = (experiment_results['group'] == 'treatment') & (experiment_results['below_threshold'])
eligible_idx = experiment_results[treatment_eligible].index
num_eligible = len(eligible_idx)
num_responders = int(num_eligible * response_rate)

responder_idx = np.random.choice(eligible_idx, size=num_responders, replace=False)
experiment_results['responded'] = False
experiment_results.loc[responder_idx, 'responded'] = True

# Compute added amounts
experiment_results['amount_added'] = 0.0
experiment_results['final_price'] = experiment_results['total_price']
for idx in responder_idx:
    base_price = experiment_results.at[idx, 'total_price']
    needed = max(0, 100 - base_price)
    extra = np.random.uniform(min_add, max_add)
    experiment_results.at[idx, 'amount_added'] = needed + extra
    experiment_results.at[idx, 'final_price'] = base_price + needed + extra

print(f"Responders: {num_responders} ({response_rate*100:.1f}%), "
      f"avg addition: {experiment_results.loc[responder_idx, 'amount_added'].mean():.2f} BRL")

# ---- Revenue calculation ----
experiment_results['final_revenue'] = 0.0

# Control group: pay shipping
ctrl_mask = experiment_results['group'] == 'control'
experiment_results.loc[ctrl_mask, 'final_revenue'] = (
    experiment_results.loc[ctrl_mask, 'final_price'] + experiment_results.loc[ctrl_mask, 'total_shipping']
)

# Treatment group logic
treat_mask = experiment_results['group'] == 'treatment'
above_100 = treat_mask & (experiment_results['final_price'] >= 100)
below_100 = treat_mask & (experiment_results['final_price'] < 100)
experiment_results.loc[above_100, 'final_revenue'] = experiment_results.loc[above_100, 'final_price']
experiment_results.loc[below_100, 'final_revenue'] = (
    experiment_results.loc[below_100, 'final_price'] + experiment_results.loc[below_100, 'total_shipping']
)

ctrl_rev = experiment_results.loc[ctrl_mask, 'final_revenue']
treat_rev = experiment_results.loc[treat_mask, 'final_revenue']

diff = treat_rev.mean() - ctrl_rev.mean()
pct_diff = diff / ctrl_rev.mean() * 100
print(f"Mean revenue — Control: {ctrl_rev.mean():.2f}, Treatment: {treat_rev.mean():.2f}, Δ={diff:.2f} ({pct_diff:.2f}%)")

# ---- Revenue breakdown ----
responders = experiment_results.query("group == 'treatment' and responded")
already_above = experiment_results.query("group == 'treatment' and below_threshold == False")

revenue_gained = responders['amount_added'].sum()
revenue_lost = already_above['total_shipping'].sum()
net_effect = revenue_gained - revenue_lost
print(f"Revenue gained: +{revenue_gained:.2f}, lost: -{revenue_lost:.2f}, net: {net_effect:.2f} BRL")

# ---- Save results ----
experiment_results.to_csv('../data/processed/new_experiment_results.csv', index=False)
print(f"Saved: ../data/processed/new_experiment_results.csv ({len(experiment_results)} rows)")

# ---- Compare groups ----
metrics = [
    ('total_price', 'Original Price'),
    ('final_price', 'Final Price'),
    ('total_shipping', 'Shipping Cost'),
    ('final_revenue', 'Final Revenue'),
]
for col, name in metrics:
    c_mean = ctrl_mask.map({True: experiment_results[col]}).mean() if False else experiment_results.loc[ctrl_mask, col].mean()
    t_mean = experiment_results.loc[treat_mask, col].mean()
    change = (t_mean - c_mean) / c_mean * 100
    print(f"{name}: Control={c_mean:.2f}, Treatment={t_mean:.2f}, Δ={change:.2f}%")

# ---- Visualizations ----
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Distribution of revenue
axes[0, 0].hist(ctrl_rev, bins=50, alpha=0.6, label='Control', edgecolor='black')
axes[0, 0].hist(treat_rev, bins=50, alpha=0.6, label='Treatment', edgecolor='black')
axes[0, 0].axvline(ctrl_rev.mean(), color='blue', linestyle='--')
axes[0, 0].axvline(treat_rev.mean(), color='orange', linestyle='--')
axes[0, 0].set_title('Final Revenue Distribution')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)

# Mean comparison
axes[0, 1].bar(['Control', 'Treatment'], [ctrl_rev.mean(), treat_rev.mean()],
               color=['lightblue', 'lightcoral'], edgecolor='black')
axes[0, 1].set_title('Mean Revenue per Group')
axes[0, 1].grid(alpha=0.3, axis='y')

# Treatment breakdown
labels = ['Responders', 'Non-responders', 'Already above']
sizes = [
    len(responders),
    len(experiment_results.query("group == 'treatment' and responded == False and below_threshold")),
    len(already_above)
]
axes[1, 0].pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
axes[1, 0].set_title('Treatment Group Composition')

# Revenue impact
labels2 = ['Gained', 'Lost', 'Net']
values = [revenue_gained, -revenue_lost, net_effect]
axes[1, 1].bar(labels2, values, color=['green', 'red', 'gray'], edgecolor='black')
axes[1, 1].axhline(0, color='black')
axes[1, 1].set_title('Revenue Impact Breakdown')
axes[1, 1].grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../results/figures/new_treatment_effect_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: ../results/figures/new_treatment_effect_analysis.png")

# ---- Validation checks ----
missing_rev = experiment_results['final_revenue'].isnull().sum()
ctrl_check = (experiment_results.loc[ctrl_mask, 'final_price'] == experiment_results.loc[ctrl_mask, 'total_price']).all()
responders_check = (experiment_results.query("group == 'treatment' and responded")['final_price'] >= 100).all()

print(f"\nValidation summary:")
print(f"  Missing revenue values: {missing_rev}")
print(f"  Control unchanged: {ctrl_check}")
print(f"  All responders reached threshold: {responders_check}")
print(f"  Final revenue range: {experiment_results['final_revenue'].min():.2f}–{experiment_results['final_revenue'].max():.2f} BRL")
