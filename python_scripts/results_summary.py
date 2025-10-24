"""
Final Results Summary and Business Recommendations
Summarizes A/B test outcomes, calculates ROI for universal vs targeted strategies,
and provides implementation roadmap and KPIs.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import shutil

# --- LaTeX setup ---
if shutil.which("latex"):
    rcParams['text.usetex'] = True
    rcParams['font.family'] = 'serif'
    rcParams['axes.titlesize'] = 12
    rcParams['axes.labelsize'] = 11
    rcParams['font.size'] = 10
else:
    print("LaTeX not found — using default matplotlib fonts.")

pd.set_option('display.max_columns', None)
pd.set_option('display.precision', 2)

# --- Load data ---
experiment_results = pd.read_csv('../data/processed/new_experiment_results.csv')
analysis_results = pd.read_csv('../data/processed/new_analysis_results.csv')
print(f"Experiment: {experiment_results.shape}, Analysis: {analysis_results.shape}")

# --- Experiment overview ---
n_control = len(experiment_results[experiment_results['group'] == 'control'])
n_treatment = len(experiment_results[experiment_results['group'] == 'treatment'])
print(f"Control={n_control}, Treatment={n_treatment}")

baseline_mean = experiment_results.query("group=='control'")['order_total'].mean()
baseline_std = experiment_results.query("group=='control'")['order_total'].std()
print(f"Baseline mean={baseline_mean:.2f}, std={baseline_std:.2f}")

# --- Economic impact by segment ---
experiment_results['segment'] = pd.cut(
    experiment_results['total_price'],
    bins=[0, 75, 150, float('inf')],
    labels=['Small', 'Medium', 'Large']
)

summary = []
for seg in ['Small', 'Medium', 'Large']:
    data = experiment_results[experiment_results['segment'] == seg]
    c = data[data['group'] == 'control']
    t = data[data['group'] == 'treatment']

    control_rev = c['final_revenue'].sum()
    treatment_rev = t['final_revenue'].sum()
    diff = treatment_rev - control_rev
    per_diff = t['final_revenue'].mean() - c['final_revenue'].mean()

    responders = t[t['responded'] == True]
    rev_add = responders['amount_added'].sum()
    ship_cost = t[t['final_price'] >= 100]['total_shipping'].sum()

    summary.append({
        'Segment': seg,
        'N_Control': len(c),
        'N_Treatment': len(t),
        'Revenue_Gain': rev_add,
        'Shipping_Cost': ship_cost,
        'Net_Impact': rev_add - ship_cost,
        'Per_Customer_Diff': per_diff
    })

eco_df = pd.DataFrame(summary)
print("\nRevenue impact by segment:")
print(eco_df.to_string(index=False))

# --- Overall economics ---
total_gain = eco_df['Revenue_Gain'].sum()
total_cost = eco_df['Shipping_Cost'].sum()
total_net = eco_df['Net_Impact'].sum()
print(f"\nOverall: Gain=+{total_gain:,.2f}, Cost=-{total_cost:,.2f}, Net={total_net:+,.2f}")

# --- ROI analysis ---
universal_gain = total_gain
universal_cost = total_cost
universal_net = total_net
universal_roi = (universal_net / universal_cost * 100) if universal_cost != 0 else np.nan

small = eco_df[eco_df['Segment'] == 'Small'].iloc[0]
target_gain = small['Revenue_Gain']
target_cost = small['Shipping_Cost']
target_net = small['Net_Impact']
target_roi = (target_net / target_cost * 100) if target_cost != 0 else np.nan

comparison = pd.DataFrame({
    'Strategy': ['Universal (All)', 'Targeted (Small Only)'],
    'Customers_Affected': [n_treatment, small['N_Treatment']],
    'Revenue_Gain': [universal_gain, target_gain],
    'Shipping_Cost': [universal_cost, target_cost],
    'Net_Profit': [universal_net, target_net],
    'ROI_%': [universal_roi, target_roi],
    'Recommendation': ['REJECT', 'IMPLEMENT']
})
print("\nStrategy comparison:")
print(comparison.to_string(index=False))

comparison.to_csv('../data/processed/new_strategy_comparison.csv', index=False)
print("Saved: ../data/processed/new_strategy_comparison.csv")

# --- Visualization ---
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Net profit comparison
strategies = ['Universal', 'Targeted']
profits = [universal_net, target_net]
colors = ['red' if x < 0 else 'green' for x in profits]
axes[0, 0].bar(strategies, profits, color=colors, edgecolor='black')
axes[0, 0].axhline(0, color='black')
axes[0, 0].set_ylabel('Net Profit (BRL)')
axes[0, 0].set_title('Net Profit by Strategy')
axes[0, 0].grid(alpha=0.3, axis='y')

# 2. ROI comparison
rois = [universal_roi, target_roi]
colors_roi = ['red' if x < 0 else 'green' for x in rois]
axes[0, 1].bar(strategies, rois, color=colors_roi, edgecolor='black')
axes[0, 1].axhline(0, color='black')
axes[0, 1].set_ylabel(r'ROI (\%)')
axes[0, 1].set_title('Return on Investment by Strategy')
axes[0, 1].grid(alpha=0.3, axis='y')

# 3. Economic breakdown by segment
x = np.arange(len(eco_df))
width = 0.25
axes[1, 0].bar(x - width, eco_df['Revenue_Gain'], width, label='Revenue Gained', color='green', edgecolor='black')
axes[1, 0].bar(x, -eco_df['Shipping_Cost'], width, label='Shipping Cost', color='red', edgecolor='black')
axes[1, 0].bar(x + width, eco_df['Net_Impact'], width, label='Net Impact', color='blue', edgecolor='black')
axes[1, 0].set_xticks(x)
axes[1, 0].set_xticklabels(eco_df['Segment'])
axes[1, 0].set_ylabel('Amount (BRL)')
axes[1, 0].set_title('Economic Breakdown by Segment')
axes[1, 0].legend()
axes[1, 0].grid(alpha=0.3, axis='y')

# 4. Treatment effect by segment (hardcoded from analysis)
effects = [35.92, -10.33, -8.02]
cols = ['green' if e > 0 else 'red' for e in effects]
axes[1, 1].bar(eco_df['Segment'], effects, color=cols, edgecolor='black')
axes[1, 1].axhline(0, color='black')
axes[1, 1].set_ylabel(r'Treatment Effect (\%)')
axes[1, 1].set_title('Treatment Effect by Segment')
axes[1, 1].grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../results/figures/new_final_summary.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: ../results/figures/new_final_summary.png")

# --- Executive summary (concise console version) ---
print("\n" + "="*60)
print("EXECUTIVE SUMMARY")
print("="*60)
print("Should we offer free shipping for orders above 100 BRL?")
print("→ NO for universal free shipping.")
print("→ YES for targeted free shipping to small orders (<75 BRL).")
print(f"\nUniversal ROI: {universal_roi:.1f}% | Net={universal_net:+,.2f} BRL")
print(f"Targeted ROI: {target_roi:.1f}% | Net={target_net:+,.2f} BRL")
print(f"Improvement: {target_net - universal_net:+,.2f} BRL")
print("\nRecommendation: IMPLEMENT targeted free shipping for small orders only.")
print("="*60)
